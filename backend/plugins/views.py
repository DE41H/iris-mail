from datetime import timedelta
from secrets import token_urlsafe
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import structlog
from django.contrib.auth import logout
from django.core.cache import cache
from django.db import IntegrityError
from django.db.models import Count, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce
from django.db.transaction import atomic
from django.utils.timezone import localdate
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import mixins, serializers, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from plugins.authentication import AgentKeyAuthentication, PluginKeyAuthentication
from plugins.gmail import get_hist_id, google_token, revoke
from plugins.models import (
    AgentKey,
    Code,
    CustomUser,
    Plugin,
    Result,
    Subscription,
    Usage,
)
from plugins.permissions import PluginKeyAuth, SessionPermission
from plugins.serializers import (
    NAME_TAKEN,
    AgentKeySerializer,
    CodeSerializer,
    ConnectSerializer,
    CustomUserSerializer,
    MeSerializer,
    PluginSerializer,
    ResultSerializer,
    SubscriptionSerializer,
    UsageSerializer,
)

logger = structlog.get_logger(__name__)


def _param(name, field, value):
    try: return field.run_validation(value)
    except ValidationError as err: raise ValidationError({name: err.detail}) from err


def _need_google(user):
    if not google_token(user).exists(): raise ValidationError({"google": "Reconnect Google first."})


def _save_key(serializer, model, **extra) -> str:
    clash = f"{model._meta.db_table}_prefix_key"
    while True:
        pre, hash, key = model.gen_key()
        try:
            with atomic(): serializer.save(prefix=pre, key=hash, **extra)
            return key
        except IntegrityError as err:
            if getattr(getattr(err.__cause__, "diag", None), "constraint_name", None) != clash: raise


@extend_schema(exclude=True)
class PluginViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = PluginSerializer
    authentication_classes = (AgentKeyAuthentication, SessionAuthentication)

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        def count(qs):
            return Coalesce(Subquery(qs.filter(plugin=OuterRef("pk")).values("plugin").annotate(n=Count("pk")).values("n")), 0)

        return Plugin.objects.filter(developer_id=self.request.user.pk).annotate(
            subscriber_count=count(Subscription.objects.filter(active=True)),
            result_count=count(Result.objects.all()),
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try: key = _save_key(serializer, Plugin, developer=request.user)
        except IntegrityError as err: raise ValidationError({"name": NAME_TAKEN}) from err
        logger.info("plugin created", plugin=serializer.instance.pk, user=request.user.pk)  # pyright: ignore[reportOptionalMemberAccess]
        return Response({**serializer.data, "key": key}, status=201)

    def perform_update(self, serializer):
        try: serializer.save()
        except IntegrityError as err: raise ValidationError({"name": NAME_TAKEN}) from err

    def perform_destroy(self, instance):
        logger.info("plugin deleted", plugin=instance.pk, user=instance.developer_id)
        instance.delete()

    @action(detail=True, methods=["post"])
    def rotate_key(self, request, pk=None, **kwargs):
        serializer = self.get_serializer(self.get_object(), data={}, partial=True)
        serializer.is_valid(raise_exception=True)
        key = _save_key(serializer, Plugin)
        logger.info("key rotated", plugin=serializer.instance.pk, user=request.user.pk)  # pyright: ignore[reportOptionalMemberAccess]
        return Response({"key": key})


@extend_schema(exclude=True)
class AgentKeyViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = AgentKeySerializer

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return AgentKey.objects.filter(user_id=self.request.user.pk)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = _save_key(serializer, AgentKey, user=request.user)
        logger.info("agent key created", key=serializer.instance.pk, user=request.user.pk)  # pyright: ignore[reportOptionalMemberAccess]
        return Response({**serializer.data, "key": key}, status=201)

    def perform_destroy(self, instance):
        logger.info("agent key revoked", key=instance.pk, user=instance.user_id)
        instance.delete()

    @action(detail=True, methods=["post"])
    def rotate_key(self, request, pk=None, **kwargs):
        serializer = self.get_serializer(self.get_object(), data={}, partial=True)
        serializer.is_valid(raise_exception=True)
        key = _save_key(serializer, AgentKey)
        logger.info("agent key rotated", key=serializer.instance.pk, user=request.user.pk)  # pyright: ignore[reportOptionalMemberAccess]
        return Response({**serializer.data, "key": key})


@extend_schema_view(
    list=extend_schema(exclude=True),
    destroy=extend_schema(exclude=True),
    set_active=extend_schema(exclude=True),
    remove=extend_schema(
        summary="Remove a user",
        description="Send `user` or `email`. Always 204. Their results are deleted after 30 days.",
        request=SubscriptionSerializer,
        responses={204: None},
    ),
)
class SubscriptionViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = SubscriptionSerializer
    authentication_classes = (PluginKeyAuthentication, SessionAuthentication)

    def get_permissions(self):
        return [PluginKeyAuth()] if self.action == "remove" else [SessionPermission()]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        if isinstance(self.request.auth, Plugin):  # pyright: ignore[reportAttributeAccessIssue]
            return Subscription.objects.filter(plugin=self.request.auth).prefetch_related("plugin")  # pyright: ignore[reportAttributeAccessIssue]
        return Subscription.objects.filter(user_id=self.request.user.pk).prefetch_related("plugin")

    def perform_destroy(self, instance):
        by = "developer" if isinstance(self.request.auth, Plugin) else "user"  # pyright: ignore[reportAttributeAccessIssue]
        logger.info("sub removed", plugin=instance.plugin_id, user=instance.user_id, by=by)
        instance.delete()

    @action(detail=False, methods=["post"])
    def remove(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if sub := self.get_queryset().filter(user_id=serializer.validated_data["user_id"]).first():
            self.perform_destroy(sub)
        return Response(status=204)

    @action(detail=True, methods=["post"])
    def set_active(self, request, pk=None, **kwargs):
        subscription = self.get_object()
        active = _param("active", serializers.BooleanField(), request.data.get("active"))
        if active: _need_google(request.user)
        if active and not subscription.active:
            subscription.set_active(True, hist_from=get_hist_id(request.user))
        else:
            subscription.set_active(active)
        logger.info("sub on" if subscription.active else "sub off", plugin=subscription.plugin_id, user=subscription.user_id)
        return Response(self.get_serializer(subscription).data)


@extend_schema_view(list=extend_schema(
    summary="List results",
    description="One per inbox email (Spam skipped). `output`: answers to your schema, plus `rules: {name: [match]}`. "
    "Deleted 30 days after ack, else after 100.",
    parameters=[
        OpenApiParameter("user", OpenApiTypes.UUID),
        OpenApiParameter("version", int, description="Plugin version."),
        OpenApiParameter("fetched", bool, description="`false` = new, `true` = acked."),
    ],
))
class ResultViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ResultSerializer
    authentication_classes = (PluginKeyAuthentication,)
    permission_classes = (PluginKeyAuth,)

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        queryset = Result.objects.filter(plugin=self.request.auth)  # pyright: ignore[reportAttributeAccessIssue]
        if user := self.request.GET.get("user"):
            queryset = queryset.filter(user=_param("user", serializers.UUIDField(), user))
        if version := self.request.GET.get("version"):
            queryset = queryset.filter(version=_param("version", serializers.IntegerField(min_value=1, max_value=32767), version))
        fetched = self.request.GET.get("fetched")
        if fetched is None:
            return queryset
        if fetched.lower() not in ("true", "false"):
            raise ValidationError({"fetched": "Use true or false."})
        return queryset.filter(fetched=fetched.lower() == "true")

    @extend_schema(
        summary="Ack results",
        description="Marks 1–500 results fetched. Unknown ids are ignored. Returns how many were newly acked.",
        request=inline_serializer("Ack", {"ids": serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=500)}),
        responses=inline_serializer("Acknowledged", {"acknowledged": serializers.IntegerField()}),
    )
    @action(detail=False, methods=["post"])
    def ack(self, request, **kwargs):
        ids = _param("ids", serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=500), request.data.get("ids"))
        acked = Result.objects.filter(plugin=request.auth, pk__in=ids, fetched=False).update(fetched=True)
        return Response({"acknowledged": acked})


@extend_schema(exclude=True)
class MeViewSet(mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = MeSerializer

    def get_object(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return self.request.user

    def perform_destroy(self, instance):
        logger.info("account deleted", user=instance.pk)
        revoke(instance)
        logout(self.request)
        instance.delete()


@extend_schema_view(list=extend_schema(
    summary="List users",
    description="Users with your plugin on.",
))
class UserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = CustomUserSerializer
    authentication_classes = (PluginKeyAuthentication,)
    permission_classes = (PluginKeyAuth,)

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return CustomUser.objects.filter(subscriptions__plugin=self.request.auth, subscriptions__active=True)  # pyright: ignore[reportAttributeAccessIssue]


@extend_schema(exclude=True)
class UsageViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = UsageSerializer
    permission_classes = (SessionPermission,)
    pagination_class = None

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return Usage.objects.filter(user_id=self.request.user.pk, date__gt=localdate() - timedelta(days=7)).order_by("-date")

    def list(self, request, *args, **kwargs):
        days = self.get_serializer(self.get_queryset(), many=True).data
        return Response({"today": localdate(), "days": days})

    @action(detail=False, authentication_classes=[], permission_classes=[AllowAny])
    def stats(self, request, **kwargs):
        today = localdate()
        count = lambda: Usage.objects.filter(date__gt=today - timedelta(days=7)).aggregate(n=Sum("used"))["n"] or 0
        return Response({"week": cache.get_or_set(f"usage:stats:{today}", count, 60 * 15)})


@extend_schema_view(
    create=extend_schema(
        summary="Create a connect link",
        description="Send the user to `url` within 3 min (one use). They accept or deny, then land on your redirect "
        "URL with `?code=…&status=accepted|denied`. `code` is shown once.",
        request=None,
        responses={201: inline_serializer("ConnectLink", {"code": serializers.CharField(), "url": serializers.URLField()})},
    ),
    retrieve=extend_schema(
        summary="Check a connect link",
        description="`user` and `email` are set once accepted. 404 if unknown; codes are deleted after a day.",
        parameters=[OpenApiParameter("code", str, OpenApiParameter.PATH)],
        responses=CodeSerializer,
    ),
)
class CodeViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = CodeSerializer
    authentication_classes = (PluginKeyAuthentication,)
    permission_classes = (PluginKeyAuth,)
    lookup_field = "code"

    def get_object(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        code = Code.objects.filter(plugin=self.request.auth, hash=Plugin.gen_hash(self.kwargs["code"])).prefetch_related("user").first()  # pyright: ignore[reportAttributeAccessIssue]
        if code is None: raise NotFound()
        return code

    def create(self, request, *args, **kwargs):
        code = token_urlsafe(32)
        Code.objects.create(plugin=request.auth, hash=Plugin.gen_hash(code))
        logger.info("code created", plugin=request.auth.pk)
        return Response({"code": code, "url": request.build_absolute_uri(f"/connect#{code}")}, status=201)


@extend_schema(exclude=True)
class ConnectViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ConnectSerializer
    permission_classes = (SessionPermission,)
    lookup_field = "code"

    def get_object(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        code = Code.pending().filter(hash=Plugin.gen_hash(self.kwargs["code"])).prefetch_related("plugin__developer").first()
        if code is None: raise NotFound("This link has expired or was already used.")
        return code

    def retrieve(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_object().plugin).data)

    def _done(self, code, status):
        logger.info(f"code {status}", plugin=code.plugin_id, user=self.request.user.pk)
        url = urlsplit(code.plugin.redirect)
        query = urlencode([*parse_qsl(url.query), ("code", self.kwargs["code"]), ("status", status)])
        return Response({"redirect": urlunsplit(url._replace(query=query))})

    @action(detail=True, methods=["post"])
    def accept(self, request, code=None, **kwargs):
        obj = self.get_object()
        _need_google(request.user)
        if not obj.accept(request.user.pk, get_hist_id(request.user)): raise NotFound("This link was already used.")
        return self._done(obj, "accepted")

    @action(detail=True, methods=["post"])
    def deny(self, request, code=None, **kwargs):
        obj = self.get_object()
        if not obj.deny(request.user.pk): raise NotFound("This link was already used.")
        return self._done(obj, "denied")

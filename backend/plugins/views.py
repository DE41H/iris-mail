import logging
from secrets import token_urlsafe
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from allauth.socialaccount.models import SocialToken
from django.contrib.auth import logout
from django.db.models import Count, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.utils.timezone import localdate
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import mixins, serializers, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from plugins.authentication import PluginKeyAuthentication
from plugins.gmail import get_hist_id, revoke
from plugins.models import Code, CustomUser, Plugin, Result, Subscription, Usage
from plugins.permissions import PluginKeyAuth, SessionPermission
from plugins.serializers import (
    CodeSerializer,
    ConnectSerializer,
    CustomUserSerializer,
    MeSerializer,
    PluginSerializer,
    ResultSerializer,
    SubscriptionSerializer,
    UsageSerializer,
)

logger = logging.getLogger(__name__)


def _param(name, field, value):
    try: return field.run_validation(value)
    except ValidationError as err: raise ValidationError({name: err.detail}) from err


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
        plugin = serializer.save(developer=request.user)
        key = plugin.rot_key()
        logger.info("Plugin created", extra={"plugin_id": plugin.pk, "user_id": request.user.pk})
        return Response({**serializer.data, "key": key}, status=201)

    def perform_destroy(self, instance):
        logger.info("Plugin deleted", extra={"plugin_id": instance.pk, "user_id": instance.developer_id})
        instance.delete()

    @action(detail=True, methods=["post"])
    def rotate_key(self, request, pk=None, **kwargs):
        plugin = self.get_object()
        key = plugin.rot_key()
        logger.info("API key rotated", extra={"plugin_id": plugin.pk, "user_id": request.user.pk})
        return Response({"key": key})


@extend_schema_view(
    list=extend_schema(exclude=True),
    destroy=extend_schema(exclude=True),
    set_active=extend_schema(exclude=True),
    remove=extend_schema(
        summary="Remove a user by id or email",
        description="Send either `user` or `email`. Ends the user's subscription to this plugin. Always 204, "
        "whether or not the user was subscribed. The user's results are deleted after 30 days.",
        request=SubscriptionSerializer,
        responses={204: OpenApiResponse(description="Removed, if subscribed.")},
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
        logger.info("Subscription removed", extra={"plugin_id": instance.plugin_id, "user_id": instance.user_id, "by": by})
        instance.delete()

    @action(detail=False, methods=["post"])
    def remove(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            errors = serializer.errors
            if errors.keys() == {"user"} and "email" not in request.data and {e.code for e in errors["user"]} == {"does_not_exist"}:
                return Response(status=204)
            raise ValidationError(errors)
        if sub := self.get_queryset().filter(user=serializer.validated_data["user"]).first():
            self.perform_destroy(sub)
        return Response(status=204)

    @action(detail=True, methods=["post"])
    def set_active(self, request, pk=None, **kwargs):
        subscription = self.get_object()
        active = _param("active", serializers.BooleanField(), request.data.get("active"))
        if active and not SocialToken.objects.filter(account__user=request.user, account__provider="google").exists():
            raise ValidationError({"google": "Reconnect Google first."})
        if active and not subscription.active:
            subscription.set_active(True, hist_from=get_hist_id(request.user))
        else:
            subscription.set_active(active)
        logger.info("Plugin turned on" if subscription.active else "Plugin turned off", extra={"plugin_id": subscription.plugin_id, "user_id": subscription.user_id})
        return Response(self.get_serializer(subscription).data)


@extend_schema_view(list=extend_schema(
    summary="List results",
    description="Newest first. Acknowledged results are deleted after 30 days; all results are deleted after 100 days.",
    parameters=[
        OpenApiParameter("user", OpenApiTypes.UUID, description="Only results for this user."),
        OpenApiParameter("version", int, description="Only results from this plugin version."),
        OpenApiParameter("fetched", bool, description="`true` for acknowledged results, `false` for new ones."),
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
        summary="Acknowledge results",
        description="Marks results as fetched. Unknown ids are ignored.",
        request=inline_serializer("Ack", {"ids": serializers.ListField(
            child=serializers.UUIDField(), min_length=1, max_length=500, help_text="Result ids, 1 to 500.")}),
        responses=inline_serializer("Acknowledged", {"acknowledged": serializers.IntegerField(help_text="Results newly marked as fetched; already acknowledged ones are not counted.")}),
    )
    @action(detail=False, methods=["post"])
    def ack(self, request, **kwargs):
        try:
            ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=False, max_length=500).run_validation(request.data.get("ids"))
        except ValidationError as err:
            raise ValidationError({"ids": err.detail}) from err
        acked = Result.objects.filter(plugin=request.auth, pk__in=ids, fetched=False).update(fetched=True)
        return Response({"acknowledged": acked})


@extend_schema(exclude=True)
class MeViewSet(mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = MeSerializer

    def get_object(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return self.request.user

    def perform_destroy(self, instance):
        logger.info("Account deleted", extra={"user_id": instance.pk})
        revoke(instance)
        logout(self.request)
        instance.delete()


@extend_schema_view(list=extend_schema(
    summary="List users",
    description="Users who have this plugin turned on.",
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
        return Usage.objects.filter(user_id=self.request.user.pk).order_by("-date")

    def list(self, request, *args, **kwargs):
        days = self.get_serializer(self.get_queryset(), many=True).data
        return Response({"today": localdate(), "days": days})


@extend_schema_view(
    create=extend_schema(
        summary="Create a connect link",
        description="Send the user to `url` within 3 minutes. They see the plugin's questions and accept or deny, then "
        "go to the plugin's redirect URL with `code` and `status` (`accepted` or `denied`) added. Each link works once. "
        "Check the outcome with `GET /codes/{code}/`; codes are deleted after a day.",
        request=None,
        responses={201: inline_serializer("ConnectLink", {
            "code": serializers.CharField(help_text="Shown once. Keep it to check the outcome."),
            "url": serializers.URLField(help_text="Link to send the user to."),
        })},
    ),
    retrieve=extend_schema(
        summary="Check a connect link",
        description="`user` and `email` are set only when the user accepted.",
        parameters=[OpenApiParameter("code", str, OpenApiParameter.PATH, description="Code from `POST /codes/`.")],
        responses={200: CodeSerializer, 404: OpenApiResponse(description="No such code for this plugin.")},
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
        logger.info("Connect code created", extra={"plugin_id": request.auth.pk})
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
        logger.info("Connect code used", extra={"plugin_id": code.plugin_id, "user_id": self.request.user.pk, "status": status})
        url = urlsplit(code.plugin.redirect)
        query = urlencode([*parse_qsl(url.query), ("code", self.kwargs["code"]), ("status", status)])
        return Response({"redirect": urlunsplit(url._replace(query=query))})

    @action(detail=True, methods=["post"])
    def accept(self, request, code=None, **kwargs):
        obj = self.get_object()
        if not SocialToken.objects.filter(account__user=request.user, account__provider="google").exists():
            raise ValidationError({"google": "Reconnect Google first."})
        if not obj.accept(request.user.pk, get_hist_id(request.user)): raise NotFound("This link was already used.")
        return self._done(obj, "accepted")

    @action(detail=True, methods=["post"])
    def deny(self, request, code=None, **kwargs):
        obj = self.get_object()
        if not obj.deny(request.user.pk): raise NotFound("This link was already used.")
        return self._done(obj, "denied")

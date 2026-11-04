import logging

from allauth.socialaccount.models import SocialToken
from django.contrib.auth import logout
from django.db.models import Count, OuterRef, Subquery
from django.db.models.functions import Coalesce
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
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from plugins.authentication import PluginKeyAuthentication
from plugins.gmail import get_hist_id, revoke
from plugins.models import CustomUser, Plugin, Result, Subscription
from plugins.permissions import PluginKeyAuth, SessionPermission
from plugins.serializers import (
    CustomUserSerializer,
    MeSerializer,
    PluginSerializer,
    ResultSerializer,
    SubscriptionSerializer,
)

logger = logging.getLogger(__name__)


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

        return Plugin.objects.filter(developer=self.request.user).annotate(
            subscriber_count=count(Subscription.objects.filter(active=True)),
            result_count=count(Result.objects.all()),
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plugin = serializer.save(developer=request.user)
        key = plugin.rot_key()
        return Response({**serializer.data, "key": key}, status=201)

    @action(detail=True, methods=["post"])
    def rotate_key(self, request, pk=None):
        plugin = self.get_object()
        key = plugin.rot_key()
        logger.info("API key rotated", extra={"plugin_id": plugin.pk, "user_id": request.user.pk})
        return Response({"key": key})


@extend_schema_view(
    list=extend_schema(exclude=True),
    set_active=extend_schema(exclude=True),
    create=extend_schema(
        summary="Add a user",
        description="Send either `user` or `email`. The plugin is added to the user's list, turned off, and receives "
        "mail once they turn it on. By `user`: 201 with the subscription. By `email`: always 202 with no body, "
        "whether or not the address has an account.",
        responses={
            201: OpenApiResponse(SubscriptionSerializer, "Subscription created."),
            202: OpenApiResponse(description="Accepted. The user is added if the address has an account."),
        },
    ),
    destroy=extend_schema(
        summary="Remove a user",
        description="Ends a subscription to this plugin. The user's results are deleted after 30 days.",
        parameters=[OpenApiParameter("id", OpenApiTypes.UUID, OpenApiParameter.PATH, description="Subscription id.")],
        responses={204: OpenApiResponse(description="Subscription removed.")},
    ),
    remove=extend_schema(
        summary="Remove a user by id or email",
        description="Send either `user` or `email`. Ends the user's subscription to this plugin. Always 204, "
        "whether or not the user was subscribed. The user's results are deleted after 30 days.",
        request=SubscriptionSerializer,
        responses={204: OpenApiResponse(description="Removed, if subscribed.")},
    ),
)
class SubscriptionViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = SubscriptionSerializer
    authentication_classes = (PluginKeyAuthentication, SessionAuthentication)

    def get_permissions(self):
        if self.action == "destroy":
            return [(PluginKeyAuth | SessionPermission)()]
        return [PluginKeyAuth()] if self.action in ("create", "remove") else [SessionPermission()]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        if isinstance(self.request.auth, Plugin):  # pyright: ignore[reportAttributeAccessIssue]
            return Subscription.objects.filter(plugin=self.request.auth).prefetch_related("plugin")  # pyright: ignore[reportAttributeAccessIssue]
        return Subscription.objects.filter(user=self.request.user).prefetch_related("plugin")

    def create(self, request, *args, **kwargs):
        if "email" not in request.data:
            return super().create(request, *args, **kwargs)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if user := serializer.validated_data["user"]:
            _, created = Subscription.objects.get_or_create(user=user, plugin=request.auth)
            if created:
                logger.info("Subscription added", extra={"plugin_id": request.auth.pk, "user_id": user.pk})
        return Response(status=202)

    def perform_create(self, serializer):
        serializer.save(plugin=self.request.auth)  # pyright: ignore[reportAttributeAccessIssue]

    def perform_destroy(self, instance):
        by = "developer" if isinstance(self.request.auth, Plugin) else "user"  # pyright: ignore[reportAttributeAccessIssue]
        logger.info("Subscription removed", extra={"subscription_id": instance.pk, "plugin_id": instance.plugin_id, "user_id": instance.user_id, "by": by})
        instance.delete()

    @action(detail=False, methods=["post"])
    def remove(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if sub := self.get_queryset().filter(user=serializer.validated_data["user"]).first():
            self.perform_destroy(sub)
        return Response(status=204)

    @action(detail=True, methods=["post"])
    def set_active(self, request, pk=None):
        subscription = self.get_object()
        active = serializers.BooleanField().run_validation(request.data.get("active"))
        if active and not SocialToken.objects.filter(account__user=request.user, account__provider="google").exists():
            raise ValidationError({"google": "Reconnect Google first."})
        if active and not subscription.active:
            subscription.set_active(True, hist_from=get_hist_id(request.user))
        else:
            subscription.set_active(active)
        logger.info("Sharing changed", extra={"subscription_id": subscription.pk, "plugin_id": subscription.plugin_id, "user_id": subscription.user_id, "active": subscription.active})
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
            queryset = queryset.filter(user=serializers.UUIDField().run_validation(user))  # pyright: ignore[reportArgumentType]
        if version := self.request.GET.get("version"):
            queryset = queryset.filter(version=serializers.IntegerField(min_value=1, max_value=32767).run_validation(version))  # pyright: ignore[reportArgumentType]
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
        responses=inline_serializer("Acknowledged", {"acknowledged": serializers.IntegerField(help_text="Results marked as fetched.")}),
    )
    @action(detail=False, methods=["post"])
    def ack(self, request):
        ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=False, max_length=500).run_validation(request.data.get("ids"))
        acked = Result.objects.filter(plugin=request.auth, pk__in=ids).update(fetched=True)
        return Response({"acknowledged": acked})


@extend_schema(exclude=True)
class MeViewSet(mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = MeSerializer

    def get_object(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return self.request.user

    def perform_destroy(self, instance):
        logger.info("Deleting account", extra={"user_id": instance.pk})
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

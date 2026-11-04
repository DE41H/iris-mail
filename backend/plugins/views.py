import logging

from django.contrib.auth import logout
from django.db.models import Count, Q
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
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from plugins.authentication import PluginKeyAuthentication
from plugins.gmail import revoke
from plugins.models import CustomUser, Plugin, Result, Subscription
from plugins.permissions import PluginKeyAuth, SessionPermission
from plugins.serializers import (
    CustomUserSerializer,
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
        return Plugin.objects.filter(developer=self.request.user).annotate(
            subscriber_count=Count("subscribers", filter=Q(subscribers__active=True), distinct=True),
            result_count=Count("results", distinct=True),
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
    destroy=extend_schema(
        description="Remove a user's subscription to this plugin. Their results stay until you delete the plugin.",
        parameters=[OpenApiParameter("id", OpenApiTypes.UUID, OpenApiParameter.PATH)],
    ),
)
class SubscriptionViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = SubscriptionSerializer
    authentication_classes = (PluginKeyAuthentication, SessionAuthentication)

    def get_permissions(self):
        if self.action == "destroy":
            return [(PluginKeyAuth | SessionPermission)()]
        return [PluginKeyAuth()] if self.action == "create" else [SessionPermission()]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        if isinstance(self.request.auth, Plugin):  # pyright: ignore[reportAttributeAccessIssue]
            return Subscription.objects.filter(plugin=self.request.auth).prefetch_related("plugin")  # pyright: ignore[reportAttributeAccessIssue]
        return Subscription.objects.filter(user=self.request.user).prefetch_related("plugin")

    def perform_create(self, serializer):
        serializer.save(plugin=self.request.auth)  # pyright: ignore[reportAttributeAccessIssue]

    def perform_destroy(self, instance):
        by = "developer" if isinstance(self.request.auth, Plugin) else "user"  # pyright: ignore[reportAttributeAccessIssue]
        logger.info("Subscription removed", extra={"subscription_id": instance.pk, "plugin_id": instance.plugin_id, "user_id": instance.user_id, "by": by})
        instance.delete()

    @action(detail=True, methods=["post"])
    def set_active(self, request, pk=None):
        subscription = self.get_object()
        subscription.set_active(serializers.BooleanField().run_validation(request.data.get("active")))
        logger.info("Sharing changed", extra={"subscription_id": subscription.pk, "plugin_id": subscription.plugin_id, "user_id": subscription.user_id, "active": subscription.active})
        return Response(self.get_serializer(subscription).data)


@extend_schema_view(list=extend_schema(parameters=[
    OpenApiParameter("user", OpenApiTypes.UUID, description="Only this user's results."),
    OpenApiParameter("fetched", bool, description="Filter by whether the result was acknowledged."),
]))
class ResultViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ResultSerializer
    authentication_classes = (PluginKeyAuthentication,)
    permission_classes = (PluginKeyAuth,)

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        queryset = Result.objects.filter(plugin=self.request.auth)  # pyright: ignore[reportAttributeAccessIssue]
        if user := self.request.GET.get("user"):
            queryset = queryset.filter(user=serializers.UUIDField().run_validation(user))  # pyright: ignore[reportArgumentType]
        fetched = self.request.GET.get("fetched")
        if fetched is None:
            return queryset
        if fetched.lower() not in ("true", "false"):
            raise ValidationError({"fetched": "Use true or false."})
        return queryset.filter(fetched=fetched.lower() == "true")

    @extend_schema(
        request=inline_serializer("Ack", {"ids": serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=500)}),
        responses=inline_serializer("Acknowledged", {"acknowledged": serializers.IntegerField()}),
    )
    @action(detail=False, methods=["post"])
    def ack(self, request):
        ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=False, max_length=500).run_validation(request.data.get("ids"))
        acked = Result.objects.filter(plugin=request.auth, pk__in=ids).update(fetched=True)
        return Response({"acknowledged": acked})


@extend_schema(exclude=True)
class MeViewSet(mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = CustomUserSerializer

    def get_object(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return self.request.user

    def perform_destroy(self, instance):
        logger.info("Deleting account", extra={"user_id": instance.pk})
        revoke(instance)
        logout(self.request)
        instance.delete()


class UserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = CustomUserSerializer
    authentication_classes = (PluginKeyAuthentication,)
    permission_classes = (PluginKeyAuth,)

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return CustomUser.objects.filter(subscriptions__plugin=self.request.auth, subscriptions__active=True)  # pyright: ignore[reportAttributeAccessIssue]

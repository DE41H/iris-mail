from rest_framework import mixins, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from plugins.authentication import PluginKeyAuthentication
from plugins.models import CustomUser, Plugin, Result, Subscription
from plugins.permissions import PluginKeyAuth, SessionPermission
from plugins.serializers import (
    CustomUserSerializer,
    PluginSerializer,
    ResultSerializer,
    SubscriptionSerializer,
)


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
        return Plugin.objects.filter(developer=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plugin = serializer.save(developer=request.user)
        key = plugin.rot_key()
        return Response({**serializer.data, "key": key}, status=201)

    @action(detail=True, methods=["post"])
    def rotate_key(self, request, pk=None):
        return Response({"key": self.get_object().rot_key()})


class SubscriptionViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = SubscriptionSerializer
    authentication_classes = (PluginKeyAuthentication, SessionAuthentication)

    def get_permissions(self):
        return [PluginKeyAuth()] if self.action == "create" else [SessionPermission()]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return Subscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(plugin=self.request.auth)  # pyright: ignore[reportAttributeAccessIssue]

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        subscription = self.get_object()
        subscription.toggle()
        return Response(self.get_serializer(subscription).data)


class ResultViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ResultSerializer
    authentication_classes = (PluginKeyAuthentication,)
    permission_classes = (PluginKeyAuth,)

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        queryset = Result.objects.filter(plugin=self.request.auth)  # pyright: ignore[reportAttributeAccessIssue]
        fetched = self.request.GET.get("fetched")
        if fetched is None:
            return queryset
        if fetched.lower() not in ("true", "false"):
            raise ValidationError({"fetched": "Use true or false."})
        return queryset.filter(fetched=fetched.lower() == "true")

    def paginate_queryset(self, queryset):
        page = super().paginate_queryset(queryset)
        if page is not None:
            Result.objects.filter(pk__in=[result.pk for result in page]).update(fetched=True)
        return page


class UserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = CustomUserSerializer
    authentication_classes = (PluginKeyAuthentication,)
    permission_classes = (PluginKeyAuth,)

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return CustomUser.objects.filter(subscriptions__plugin=self.request.auth, subscriptions__active=True)  # pyright: ignore[reportAttributeAccessIssue]


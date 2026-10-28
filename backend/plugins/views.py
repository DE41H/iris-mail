import json
from base64 import b64decode
from secrets import compare_digest

from django.conf import settings
from rest_framework import mixins, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from plugins.authentication import PluginKeyAuthentication
from plugins.models import CustomUser, Plugin, Result, Subscription
from plugins.permissions import PluginKeyAuth, SessionPermission
from plugins.serializers import (
    CustomUserSerializer,
    PluginSerializer,
    ResultSerializer,
    SubscriptionSerializer,
)
from plugins.tasks import process


class PluginViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = PluginSerializer

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return Plugin.objects.filter(developer=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plugin = serializer.save(developer=request.user)
        key = plugin.rot_key()
        return Response({**serializer.data, "key": key}, status=201)


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


class UserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = CustomUserSerializer
    authentication_classes = (PluginKeyAuthentication,)
    permission_classes = (PluginKeyAuth,)

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return CustomUser.objects.filter(subscriptions__plugin=self.request.auth, subscriptions__active=True)  # pyright: ignore[reportAttributeAccessIssue]


class PubSubView(APIView):
    authentication_classes = ()
    permission_classes = ()
    throttle_classes = ()

    def post(self, request):
        expected: str = settings.PUBSUB_PUSH_TOKEN
        token: str = request.GET.get("token", "")
        if not expected or not compare_digest(token.encode("utf-8"), expected.encode("utf-8")):
            return Response(status=403)
        try:
            event = json.loads(b64decode(request.data["message"]["data"]))
            email, hist_id = event["emailAddress"], int(event["historyId"])
        except (KeyError, TypeError, ValueError):
            return Response(status=400)
        user_id = CustomUser.objects.filter(email=email).values_list("id", flat=True).first()
        if user_id:
            process.defer(user_id=str(user_id), hist_id=hist_id)
        return Response(status=204)

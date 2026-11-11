from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.routers import SimpleRouter

from plugins.views import (
    AgentKeyViewSet,
    CodeViewSet,
    ConnectViewSet,
    MeViewSet,
    PluginViewSet,
    QuotaViewSet,
    ResultViewSet,
    SubscriptionViewSet,
    UsageViewSet,
    UserViewSet,
)

r = SimpleRouter()
r.register(r'plugins', PluginViewSet, basename='plugin')
r.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
r.register(r'results', ResultViewSet, basename='results')
r.register(r'users', UserViewSet, basename='users')
r.register(r'usage', UsageViewSet, basename='usage')
r.register(r'quota', QuotaViewSet, basename='quota')
r.register(r'codes', CodeViewSet, basename='codes')
r.register(r'connect', ConnectViewSet, basename='connect')
r.register(r'keys', AgentKeyViewSet, basename='keys')

urlpatterns: list = [
    path("me/", ensure_csrf_cookie(MeViewSet.as_view({"get": "retrieve", "delete": "destroy"})), name="me"),
    *r.urls,
]

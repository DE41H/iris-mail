from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.routers import SimpleRouter

from plugins.views import (
    CodeViewSet,
    ConnectViewSet,
    MeViewSet,
    PluginViewSet,
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
r.register(r'codes', CodeViewSet, basename='codes')
r.register(r'connect', ConnectViewSet, basename='connect')

urlpatterns: list = [
    path("me/", ensure_csrf_cookie(MeViewSet.as_view({"get": "retrieve", "delete": "destroy"})), name="me"),
    *r.urls,
]

from django.urls import path
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.views import SpectacularAPIView
from rest_framework.permissions import AllowAny
from rest_framework.routers import SimpleRouter

from plugins.views import (
    MeView,
    PluginViewSet,
    ResultViewSet,
    SubscriptionViewSet,
    UserViewSet,
)

r = SimpleRouter()
r.register(r'plugins', PluginViewSet, basename='plugin')
r.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
r.register(r'results', ResultViewSet, basename='results')
r.register(r'users', UserViewSet, basename='users')

urlpatterns: list = [
    path("me/", ensure_csrf_cookie(MeView.as_view()), name="me"),
    path("schema/", cache_page(60*60)(SpectacularAPIView.as_view(authentication_classes=[], permission_classes=[AllowAny])), name="schema"),
    *r.urls,
]

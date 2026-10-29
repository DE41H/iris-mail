from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie
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

urlpatterns: list = [path("me/", ensure_csrf_cookie(MeView.as_view()), name="me"), *r.urls]

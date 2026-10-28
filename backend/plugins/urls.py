from django.urls import path
from rest_framework.routers import SimpleRouter

from plugins.views import (
    PluginViewSet,
    PubSubView,
    ResultViewSet,
    SubscriptionViewSet,
    UserViewSet,
)

r = SimpleRouter()
r.register(r'plugins', PluginViewSet, basename='plugin')
r.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
r.register(r'results', ResultViewSet, basename='results')
r.register(r'users', UserViewSet, basename='users')

urlpatterns: list = r.urls + [ path('pubsub/', PubSubView.as_view(), name='pubsub') ]

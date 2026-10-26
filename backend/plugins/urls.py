from rest_framework.routers import SimpleRouter

from plugins.views import PluginViewSet, ResultViewSet, SubscriptionViewSet, UserViewSet

r = SimpleRouter()
r.register(r'plugins', PluginViewSet, basename='plugin')
r.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
r.register(r'results', ResultViewSet, basename='results')
r.register(r'users', UserViewSet, basename='users')

urlpatterns: list = r.urls

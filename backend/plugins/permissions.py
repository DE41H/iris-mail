from rest_framework.permissions import BasePermission

from plugins.models import Plugin


class PluginKeyAuth(BasePermission):
    def has_permission(self, request, view):  # pyright: ignore[reportIncompatibleMethodOverride]
        return isinstance(request.auth, Plugin)


class SessionPermission(BasePermission):
    def has_permission(self, request, view):  # pyright: ignore[reportIncompatibleMethodOverride]
        return request.user.is_authenticated and request.auth is None

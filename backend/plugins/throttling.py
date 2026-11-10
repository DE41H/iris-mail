from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle

from plugins.models import Plugin


class UserThrottle(UserRateThrottle):
    def get_cache_key(self, request, view):  # pyright: ignore[reportIncompatibleMethodOverride]
        return None if isinstance(request.auth, Plugin) else super().get_cache_key(request, view)


class PluginKeyThrottle(SimpleRateThrottle):
    scope = "dev"

    def get_cache_key(self, request, view):
        if not isinstance(request.auth, Plugin): return None
        return self.cache_format % {"scope": self.scope, "ident": request.auth.developer_id}  # pyright: ignore[reportAttributeAccessIssue]

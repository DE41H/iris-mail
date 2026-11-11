from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle

from plugins.models import AgentKey, Plugin

KEYS = (Plugin, AgentKey)


class UserThrottle(UserRateThrottle):
    def get_cache_key(self, request, view):  # pyright: ignore[reportIncompatibleMethodOverride]
        return None if isinstance(request.auth, KEYS) else super().get_cache_key(request, view)


class KeyThrottle(SimpleRateThrottle):
    scope = "dev"

    def get_cache_key(self, request, view):
        if not isinstance(request.auth, KEYS): return None
        return self.cache_format % {"scope": self.scope, "ident": request.user.pk}


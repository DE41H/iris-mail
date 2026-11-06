from rest_framework.throttling import SimpleRateThrottle

from plugins.models import Plugin


class PluginKeyThrottle(SimpleRateThrottle):
    scope = "dev"

    def get_cache_key(self, request, view):
        if not isinstance(request.auth, Plugin): return None
        return self.cache_format % {"scope": self.scope, "ident": request.auth.developer_id}  # pyright: ignore[reportAttributeAccessIssue]

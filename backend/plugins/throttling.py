from rest_framework.throttling import SimpleRateThrottle

from plugins.models import Plugin, UserTier

TIER_RATES = {
    UserTier.BASE: "500/hour",
    UserTier.CORE: "1000/hour",
    UserTier.PRIME: "2000/hour",
    UserTier.ULTRA: "5000/hour",
}


class PluginKeyThrottle(SimpleRateThrottle):
    scope = "developer"

    def get_rate(self):
        return None

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": request.auth.developer_id}

    def allow_request(self, request, view):
        if not isinstance(request.auth, Plugin):
            return True
        self.rate = TIER_RATES[request.auth.developer.tier]
        self.num_requests, self.duration = self.parse_rate(self.rate)
        return super().allow_request(request, view)

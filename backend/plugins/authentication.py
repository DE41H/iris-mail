from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed, Throttled
from rest_framework.throttling import BaseThrottle

from plugins.models import Plugin

MAX_FAILS = 10


class PluginKeyAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts or parts[0].decode(errors="ignore").lower() != self.keyword.lower():
            return None
        if len(parts) != 2:
            raise AuthenticationFailed("Invalid API key header.")
        ident = f"badkey:{BaseThrottle().get_ident(request)}"
        if (cache.get(ident) or 0) >= MAX_FAILS: raise Throttled()
        plugin = Plugin.auth_key(parts[1].decode(errors="ignore"))
        if plugin is None:
            cache.add(ident, 0, 60*60)
            cache.incr(ident)
            raise AuthenticationFailed("Invalid API key.")
        return plugin.developer, plugin

    def authenticate_header(self, request):  # pyright: ignore[reportIncompatibleMethodOverride]
        return self.keyword

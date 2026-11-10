import logging

from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed, Throttled
from rest_framework.throttling import BaseThrottle

from plugins.models import Plugin

logger = logging.getLogger(__name__)

MAX_FAILS = 10


class PluginKeyAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts or parts[0].decode(errors="ignore").lower() != self.keyword.lower():
            return None
        if len(parts) != 2:
            raise AuthenticationFailed("Use the header Authorization: Bearer <key>.")
        ident = f"badkey:{BaseThrottle().get_ident(request)}"
        if (cache.get(ident) or 0) >= MAX_FAILS: raise Throttled(detail="Too many invalid API keys. Try again in an hour.")
        plugin = Plugin.auth_key(parts[1].decode(errors="ignore"))
        if plugin is None:
            cache.add(ident, 0, 60*60)
            if cache.incr(ident) == MAX_FAILS:
                logger.warning("ip blocked", extra={"ip": ident.removeprefix("badkey:")})
            raise AuthenticationFailed("Invalid API key.")
        return plugin.developer, plugin

    def authenticate_header(self, request):  # pyright: ignore[reportIncompatibleMethodOverride]
        return self.keyword

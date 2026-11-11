import structlog
from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed, Throttled
from rest_framework.throttling import BaseThrottle

from plugins.models import AGENT_PREFIX, PLUGIN_PREFIX, AgentKey, Plugin

logger = structlog.get_logger(__name__)

MAX_FAILS = 10


class KeyAuthentication(BaseAuthentication):
    keyword = "Bearer"
    model: type[Plugin] | type[AgentKey]
    owner: str

    def accepts(self, key: str) -> bool:
        raise NotImplementedError

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts or parts[0].decode(errors="ignore").lower() != self.keyword.lower():
            return None
        if len(parts) != 2:
            raise AuthenticationFailed("Use the header Authorization: Bearer <key>.")
        key = parts[1].decode(errors="ignore")
        if not self.accepts(key): return None
        ident = f"badkey:{BaseThrottle().get_ident(request)}"
        if (cache.get(ident) or 0) >= MAX_FAILS: raise Throttled(detail="Too many invalid API keys. Try again in an hour.")
        obj = self.model.auth_key(key)
        if obj is None:
            cache.add(ident, 0, 60*60)
            try: fails = cache.incr(ident)
            except ValueError: fails = int(cache.add(ident, 1, 60*60))
            if fails == MAX_FAILS:
                logger.warning("ip blocked", ip=ident.removeprefix("badkey:"))
            raise AuthenticationFailed("Invalid API key.")
        return getattr(obj, self.owner), obj

    def authenticate_header(self, request):  # pyright: ignore[reportIncompatibleMethodOverride]
        return self.keyword


class PluginKeyAuthentication(KeyAuthentication):
    model, owner = Plugin, "developer"

    def accepts(self, key):
        return key.startswith(PLUGIN_PREFIX) and not key.startswith(AGENT_PREFIX)


class AgentKeyAuthentication(KeyAuthentication):
    model, owner = AgentKey, "user"

    def accepts(self, key):
        return key.startswith(AGENT_PREFIX)

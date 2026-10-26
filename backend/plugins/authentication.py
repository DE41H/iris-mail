from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from plugins.models import Plugin


class PluginKeyAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts or parts[0].decode(errors="ignore").lower() != self.keyword.lower():
            return None
        if len(parts) != 2:
            raise AuthenticationFailed("Invalid API key header.")
        plugin = Plugin.auth_key(parts[1].decode(errors="ignore"))
        if plugin is None:
            raise AuthenticationFailed("Invalid API key.")
        return plugin.developer, plugin

    def authenticate_header(self, request):  # pyright: ignore[reportIncompatibleMethodOverride]
        return self.keyword

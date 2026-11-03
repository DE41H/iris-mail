from drf_spectacular.extensions import OpenApiAuthenticationExtension


class PluginKeyScheme(OpenApiAuthenticationExtension):
    target_class = "plugins.authentication.PluginKeyAuthentication"
    name = "PluginKey"

    def get_security_definition(self, auto_schema):
        return {"type": "http", "scheme": "bearer", "description": "The plugin's API key."}

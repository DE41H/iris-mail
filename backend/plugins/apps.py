from django.apps import AppConfig


class PluginsConfig(AppConfig):
    name = 'plugins'

    def ready(self):
        from plugins import schema, signals, token  # noqa: F401  registers the receivers, the OpenAPI auth extension and token encryption

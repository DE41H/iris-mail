from django.apps import AppConfig


class PluginsConfig(AppConfig):
    name = 'plugins'

    def ready(self):
        from plugins import schema, signals  # noqa: F401  registers the receivers and the OpenAPI auth extension

from django.apps import AppConfig


class PluginsConfig(AppConfig):
    name = 'plugins'

    def ready(self):
        from plugins import signals  # noqa: F401  registers the receivers

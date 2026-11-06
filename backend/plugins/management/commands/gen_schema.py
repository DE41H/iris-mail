import json

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        versions = settings.REST_FRAMEWORK["ALLOWED_VERSIONS"]
        dir = settings.STATIC_ROOT / "schema"
        dir.mkdir(parents=True, exist_ok=True)
        for v in versions:
            call_command("spectacular", api_version=v, format="openapi-json", validate=True, fail_on_warn=True, file=str(dir / f"{v}.json"))
        (dir / "versions.json").write_text(json.dumps(versions))

import brotli
from django.contrib.staticfiles.storage import StaticFilesStorage


class BrotliStorage(StaticFilesStorage):
    def post_process(self, paths, dry_run=False, **options):
        if dry_run: return
        for name in paths:
            if name.endswith((".css", ".js", ".svg", ".json")):
                with self.open(name) as f, open(self.path(name) + ".br", "wb") as out:
                    out.write(brotli.compress(f.read()))
                yield name, name, True

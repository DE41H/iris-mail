# Procrastinate autodiscovers plugins.tasks; task names are pinned so moving code keeps queued jobs valid.
from plugins.tasks.cleanup import cleanup
from plugins.tasks.extract import process
from plugins.tasks.poll import init_hist, poll_inboxes

__all__ = ["cleanup", "process", "init_hist", "poll_inboxes"]

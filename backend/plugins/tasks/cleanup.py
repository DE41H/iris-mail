import logging
from datetime import timedelta

from django.db.models import Exists, OuterRef, Q
from django.utils.timezone import now
from procrastinate.contrib.django import app

from plugins.models import Result, Subscription

logger = logging.getLogger(__name__)

JOB_KEEP_FOR_HRS = 7 * 24
RESULT_KEEP_FOR = 30

@app.periodic(cron="0 3 * * *")
@app.task(name="plugins.tasks.cleanup")
async def cleanup(timestamp):
    await app.job_manager.delete_old_jobs(
        nb_hours=JOB_KEEP_FOR_HRS, include_failed=True, include_cancelled=True, include_aborted=True,
    )
    subscribed = Exists(Subscription.objects.filter(user=OuterRef("user"), plugin=OuterRef("plugin")))
    cutoff = now() - timedelta(days=RESULT_KEEP_FOR)
    count, _ = await Result.objects.filter(Q(fetched=True) | ~subscribed, time__lte=cutoff).adelete()
    logger.info("Cleaned up old jobs and results", extra={"results_deleted": count})

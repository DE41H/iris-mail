import logging
from asyncio import gather
from datetime import timedelta
from uuid import UUID

from django.db.models import Exists, OuterRef, Q
from django.utils.timezone import now
from procrastinate.contrib.django import app

from plugins.models import Result, Subscription
from plugins.tasks.base import retry

logger = logging.getLogger(__name__)

JOB_KEEP_FOR_HRS = 7 * 24
RESULT_KEEP_FOR = 30
RESULT_MAX_AGE = 100

def _before(days):
    # smallest uuid7 made `days` ago: its top 48 bits are the unix time in ms
    return UUID(int=int((now() - timedelta(days=days)).timestamp() * 1000) << 80)

@app.periodic(cron="0 3 * * *")
@app.task(name="plugins.tasks.cleanup")
async def cleanup(timestamp):
    delete_jobs =app.job_manager.delete_old_jobs(
        nb_hours=JOB_KEEP_FOR_HRS, include_failed=True, include_cancelled=True, include_aborted=True,
    )
    subscribed = Exists(Subscription.objects.filter(user=OuterRef("user"), plugin=OuterRef("plugin")))
    cond_1 = Q(id__lt=_before(RESULT_MAX_AGE))
    cond_2 = (Q(fetched=True) | ~subscribed)
    cond_3 = Q(id__lt=_before(RESULT_KEEP_FOR))
    condition = (cond_1) | (cond_2 & cond_3)
    clean_results = Result.objects.filter(condition).adelete()
    (count, _), _ = await gather(clean_results, delete_jobs)
    logger.info("Cleaned up old jobs and results", extra={"results_deleted": count})

@app.periodic(cron="*/5 * * * *")
@app.task(name="plugins.tasks.revive", queueing_lock="revive")
async def revive(timestamp):
    jobs = await app.job_manager.get_stalled_jobs()
    await gather(*( retry(job) for job in jobs ))
    if jobs: logger.warning("Retried stalled jobs", extra={"job_ids": [job.id for job in jobs]})

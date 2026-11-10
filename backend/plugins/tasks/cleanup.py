from asyncio import gather
from datetime import timedelta

import structlog
from django.db.models import Exists, OuterRef, Q
from procrastinate.contrib.django import app
from procrastinate.exceptions import UniqueViolation
from procrastinate.jobs import Status

from plugins.models import Code, Result, Subscription, Usage, uuid_before

logger = structlog.get_logger(__name__)


JOB_KEEP_FOR_HRS = 7 * 24
RESULT_KEEP_FOR = timedelta(days=30)
RESULT_MAX_AGE = timedelta(days=100)
USAGE_KEEP_FOR = timedelta(days=100)
CODE_KEEP_FOR = timedelta(days=1)

async def _retry(job):
    try: await app.job_manager.retry_job(job)
    except UniqueViolation: await app.job_manager.finish_job(job, Status.FAILED, delete_job=False)

@app.periodic(cron="0 3 * * *")
@app.task(name="plugins.tasks.cleanup")
async def cleanup(timestamp):
    delete_jobs =app.job_manager.delete_old_jobs(
        nb_hours=JOB_KEEP_FOR_HRS, include_failed=True, include_cancelled=True, include_aborted=True,
    )
    subscribed = Exists(Subscription.objects.filter(user=OuterRef("user"), plugin=OuterRef("plugin")))
    cond_1 = Q(id__lt=uuid_before(RESULT_MAX_AGE))
    cond_2 = (Q(fetched=True) | ~subscribed)
    cond_3 = Q(id__lt=uuid_before(RESULT_KEEP_FOR))
    condition = (cond_1) | (cond_2 & cond_3)
    clean_results = Result.objects.filter(condition).adelete()
    clean_usage = Usage.objects.filter(id__lt=uuid_before(USAGE_KEEP_FOR)).adelete()
    clean_codes = Code.objects.filter(id__lt=uuid_before(CODE_KEEP_FOR)).adelete()
    (count, _), (usage, _), (codes, _), _ = await gather(clean_results, clean_usage, clean_codes, delete_jobs)
    logger.info("cleanup", results=count, usage=usage, codes=codes)

@app.periodic(cron="*/5 * * * *")
@app.task(name="plugins.tasks.revive", queueing_lock="revive")
async def revive(timestamp):
    jobs = await app.job_manager.get_stalled_jobs()
    await gather(*( _retry(job) for job in jobs ))
    if jobs: logger.warning("jobs retried", jobs=[job.id for job in jobs])

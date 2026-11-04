from procrastinate.contrib.django import app
from procrastinate.exceptions import UniqueViolation
from procrastinate.jobs import Status


async def retry(job):
    try: await app.job_manager.retry_job(job)
    except UniqueViolation: await app.job_manager.finish_job(job, Status.FAILED, delete_job=False)

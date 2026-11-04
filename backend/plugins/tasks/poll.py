from contextlib import suppress

from procrastinate.contrib.django import app
from procrastinate.exceptions import AlreadyEnqueued

from plugins.gmail import get_hist_id
from plugins.models import CustomUser
from plugins.tasks.extract import process


@app.task(name="plugins.tasks.init_hist", retry=5)
def init_hist(user_id):
    user = CustomUser.objects.get(pk=user_id)
    CustomUser.objects.filter(pk=user_id, hist_id__isnull=True).invalidated_update(hist_id=get_hist_id(user))  # pyright: ignore[reportAttributeAccessIssue]

@app.periodic(cron="*/3 * * * *")
@app.task(name="plugins.tasks.poll_hist")
def poll_hist(timestamp):
    user_ids = CustomUser.objects.filter(subscriptions__active=True, socialaccount__provider="google").values_list("pk", flat=True).distinct()
    for user_id in user_ids:
        with suppress(AlreadyEnqueued):
            process.configure(lock=str(user_id), queueing_lock=str(user_id)).defer(user_id=str(user_id))

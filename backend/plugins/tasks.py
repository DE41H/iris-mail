import logging
from functools import cache

import laya
from django.db.transaction import atomic
from googleapiclient.errors import HttpError
from laya.structured import SchemaError
from procrastinate.contrib.django import app
from simplegmail import Gmail

from plugins.gmail import client, get_hist_id, save_token
from plugins.models import CustomUser, Result, Subscription

logger = logging.getLogger(__name__)

@cache
def _laya():
    return laya.Router()

def _get_msgs(gmail: Gmail, start):
    msgs, page = [], None
    while True:
        data = gmail.service.users().history().list(  # pyright: ignore[reportAttributeAccessIssue]
            userId="me", startHistoryId=start, historyTypes=["messageAdded"], labelId="INBOX", pageToken=page,
        ).execute()
        msgs += [gmail._build_message_from_ref("me", m["message"], attachments="ignore") for h in data.get("history", []) for m in h.get("messagesAdded", [])]
        page = data.get("nextPageToken")
        if not page:
            return msgs, int(data["historyId"])

@app.task(retry=3)
@atomic
def process(user_id):
    user = CustomUser.objects.select_for_update().get(pk=user_id)
    if user.hist_id is None: return
    gmail = client(user)
    try:
        msgs, latest = _get_msgs(gmail, user.hist_id)
    except HttpError as error:
        if error.resp.status != 404: raise
        logger.warning("Gmail history expired for user %s, resetting baseline", user_id)
        CustomUser.objects.filter(pk=user_id).update(hist_id=get_hist_id(user))
        return
    save_token(user, gmail)
    done ={(bytes(b), p) for b, p in Result.objects.filter(user=user, message__in=[bytes.fromhex(m.id) for m in msgs]).values_list("message", "plugin_id")}
    subs = tuple(Subscription.objects.filter(user=user, active=True).select_related("plugin"))
    results = []
    for message in msgs:
        key = bytes.fromhex(message.id)
        plugins = [s.plugin for s in subs if (key, s.plugin_id) not in done]  # pyright: ignore[reportAttributeAccessIssue]
        if not plugins:
            continue
        state = laya.email_state(message.subject, message.plain or "")
        for plugin in plugins:
            try:
                output = laya.decide(_laya(), state, schema=plugin.schema)
            except SchemaError:
                logger.exception("Plugin %s has a schema Laya cannot answer", plugin.id)
                continue
            results.append(Result(user=user, plugin=plugin, output=output, message=key))
            done.add((key, plugin.id))
    Result.objects.bulk_create(results)
    CustomUser.objects.filter(pk=user_id).update(hist_id=latest)

@app.task(retry=5)
def init_hist(user_id):
    user = CustomUser.objects.get(pk=user_id)
    CustomUser.objects.filter(pk=user_id, hist_id__isnull=True).update(hist_id=get_hist_id(user))

@app.periodic(cron="*/3 * * * *")
@app.task
def poll_inboxes(timestamp):
    user_ids = CustomUser.objects.filter(subscriptions__active=True, socialaccount__provider="google").values_list("pk", flat=True).distinct()
    for user_id in user_ids:
        process.defer(user_id=str(user_id))

import logging
from functools import cache
from types import SimpleNamespace

import laya
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
    ids, page = {}, None
    while True:
        data = gmail.service.users().history().list(  # pyright: ignore[reportAttributeAccessIssue]
            userId="me", startHistoryId=start, historyTypes=["messageAdded"], labelId="INBOX", pageToken=page,
        ).execute()
        ids.update((m["message"]["id"], None) for h in data.get("history", []) for m in h.get("messagesAdded", []))
        page = data.get("nextPageToken")
        if not page:
            break
    msgs = []
    def add(msg_id, raw, error):
        if error is not None:
            if error.resp.status != 404: raise error
            # Deleted between the history entry and the fetch: skip only this message.
            logger.info("Gmail message %s is gone, skipping", msg_id)
            return
        parts = gmail._evaluate_message_payload(raw["payload"], "me", msg_id, "ignore")
        subject = next((h["value"] for h in raw["payload"]["headers"] if h["name"].lower() == "subject"), "")
        plain = "\n".join(p["body"] for p in parts if p["part_type"] == "plain") or None
        msgs.append(SimpleNamespace(id=msg_id, subject=subject, plain=plain))
    ids = list(ids)
    for i in range(0, len(ids), 50):  # Gmail allows 100 calls per batch but advises 50
        batch = gmail.service.new_batch_http_request(callback=add)  # pyright: ignore[reportAttributeAccessIssue]
        for msg_id in ids[i:i + 50]:
            batch.add(gmail.service.users().messages().get(userId="me", id=msg_id), request_id=msg_id)  # pyright: ignore[reportAttributeAccessIssue]
        batch.execute()
    return msgs, int(data["historyId"])

@app.task(retry=3)
def process(user_id):
    user = CustomUser.objects.get(pk=user_id)
    if user.hist_id is None: return
    gmail = client(user)
    try:
        msgs, latest = _get_msgs(gmail, user.hist_id)
    except HttpError as error:
        if error.resp.status != 404: raise
        logger.warning("Gmail history expired for user %s, resetting baseline", user_id)
        CustomUser.objects.filter(pk=user_id).invalidated_update(hist_id=get_hist_id(user))  # pyright: ignore[reportAttributeAccessIssue]
        return
    save_token(user, gmail)
    done ={(bytes(b), p) for b, p in Result.objects.filter(user=user, message__in=[bytes.fromhex(m.id) for m in msgs]).values_list("message", "plugin_id")}
    subs = tuple(Subscription.objects.filter(user=user, active=True).prefetch_related("plugin"))
    results = []
    try:
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
    finally:
        Result.objects.bulk_create(results, ignore_conflicts=True)
    CustomUser.objects.filter(pk=user_id).invalidated_update(hist_id=latest)  # pyright: ignore[reportAttributeAccessIssue]

@app.task(retry=5)
def init_hist(user_id):
    user = CustomUser.objects.get(pk=user_id)
    CustomUser.objects.filter(pk=user_id, hist_id__isnull=True).invalidated_update(hist_id=get_hist_id(user))  # pyright: ignore[reportAttributeAccessIssue]

@app.periodic(cron="*/3 * * * *")
@app.task
def poll_inboxes(timestamp):
    user_ids = CustomUser.objects.filter(subscriptions__active=True, socialaccount__provider="google").values_list("pk", flat=True).distinct()
    for user_id in user_ids:
        process.configure(lock=str(user_id)).defer(user_id=str(user_id))

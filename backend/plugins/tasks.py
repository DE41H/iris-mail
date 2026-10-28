import logging
from functools import cache

import laya
from allauth.socialaccount.models import SocialAccount, SocialToken
from django.db.transaction import atomic
from google.auth.exceptions import GoogleAuthError
from googleapiclient.errors import HttpError
from laya.structured import SchemaError
from procrastinate.contrib.django import app
from simplegmail import Gmail

from plugins.gmail import client, save_token, watch
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
def process(user_id, hist_id):
    user = CustomUser.objects.select_for_update().get(pk=user_id)
    gmail = client(user)
    try:
        msgs, latest = _get_msgs(gmail, user.hist_id or hist_id - 1)
    except HttpError as error:
        if error.resp.status != 404: raise
        logger.warning("Gmail history expired for user %s, restarting from notification", user_id)
        msgs, latest = _get_msgs(gmail, hist_id - 1)
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
def start_watch(user_id):
    user = CustomUser.objects.get(pk=user_id)
    response = watch(user)
    CustomUser.objects.filter(pk=user_id, hist_id__isnull=True).update(hist_id=int(response["historyId"]))

@app.periodic(cron="0 3 * * *")
@app.task
def renew_watch(timestamp):
    for account in SocialAccount.objects.filter(provider="google").select_related("user"):
        try: watch(account.user)
        except (GoogleAuthError, HttpError, SocialToken.DoesNotExist):
            logger.exception("Gmail watch renewal failed for account %s", account.pk)

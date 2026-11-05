import logging

import laya
import re2
from bs4 import BeautifulSoup
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError
from laya.structured import SchemaError
from procrastinate.contrib.django import app

from plugins.gmail import client, disconnect, fetch, get_hist, reset_hist, save_token
from plugins.models import CustomUser, Result, Subscription
from plugins.validation import MAX_MATCHES, RE2

logger = logging.getLogger(__name__)

ROUTER = laya.Router(max_loaded=1)
CHUNK_SIZE = 250


def _match(plugin, content):
    out = {}
    for name, pattern in plugin.rules.items():
        try:
            found = re2.compile(pattern, RE2).findall(content)
        except re2.error:
            logger.warning("Rule does not compile, skipped", extra={"plugin_id": plugin.id, "rule": name})
            found = []
        out[name] = [next((g for g in m if g), m[0]) if isinstance(m, tuple) else m for m in found[:MAX_MATCHES]]
    return out


def _decide(plugin, states):
    return laya.decide_batch(ROUTER, states, schema=plugin.schema, model="multilingual", batch_size=32)


def _guess(user, plugin, msgs, states):
    if not plugin.schema.get("properties"): return [(m, {}) for m in msgs]
    extra = {"plugin_id": plugin.id, "user_id": user.pk}
    try:
        return list(zip(msgs, _decide(plugin, [states[m.id] for m in msgs]), strict=True))
    except SchemaError:
        logger.exception("Laya cannot answer plugin schema, skipped", extra=extra)
        return []


def _extract(user, subs, msgs, added):
    bodies = {m.id: m.plain or BeautifulSoup(m.html or "", "lxml").get_text("\n") for m in msgs}
    states = {m.id: laya.email_state(m.subject, bodies[m.id], sender=m.sender) for m in msgs}
    done = {(bytes(b), p) for b, p in Result.objects.filter(user=user, message__in=[bytes.fromhex(m.id) for m in msgs]).values_list("message", "plugin_id")}
    results = []
    try:
        for sub in subs:
            plugin = sub.plugin
            todo = [m for m in msgs if added[m.id] > sub.hist_from and (bytes.fromhex(m.id), plugin.id) not in done]
            for m, output in _guess(user, plugin, todo, states):
                if plugin.rules: output["rules"] = _match(plugin, f"{m.subject or ''}\n{bodies[m.id]}")
                results.append(Result(user=user, plugin=plugin, version=plugin.version, output=output, message=bytes.fromhex(m.id)))
    finally:
        Result.objects.bulk_create(results, ignore_conflicts=True)
    return len(results)


@app.task(name="plugins.tasks.process")
def process(user_id):
    user = CustomUser.objects.filter(pk=user_id).first()
    if user is None: return
    if user.hist_id is None: return reset_hist(user, "no history id")
    gmail = client(user)
    try:
        added, latest = get_hist(gmail, user.hist_id)
    except RefreshError as error:
        if error.retryable: raise
        return disconnect(user)
    except HttpError as error:
        if error.resp.status != 404: raise
        return reset_hist(user, "history expired")
    Subscription.objects.filter(user=user, active=True, hist_from=None).invalidated_update(hist_from=latest)  # pyright: ignore[reportAttributeAccessIssue]
    subs = Subscription.objects.filter(user=user, active=True).prefetch_related("plugin")
    low = min((s.hist_from for s in subs), default=latest)
    ids = sorted((i for i, h in added.items() if h > low), key=added.__getitem__)
    fetched = saved = 0
    for n in range(0, len(ids), CHUNK_SIZE):
        msgs = fetch(gmail, ids[n:n + CHUNK_SIZE])
        save_token(user, gmail)
        fetched += len(msgs)
        saved += _extract(user, subs, msgs, added)
        if n + CHUNK_SIZE < len(ids):
            CustomUser.objects.filter(pk=user.pk).invalidated_update(hist_id=added[ids[n + CHUNK_SIZE]] - 1)  # pyright: ignore[reportAttributeAccessIssue]
    CustomUser.objects.filter(pk=user.pk).invalidated_update(hist_id=latest)  # pyright: ignore[reportAttributeAccessIssue]
    if added:
        logger.info("Mail processed", extra={"user_id": user.pk, "seen": len(added), "fetched": fetched, "results": saved})

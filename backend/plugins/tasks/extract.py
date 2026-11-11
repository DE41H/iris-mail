import re
from contextlib import suppress
from functools import cache, lru_cache
from itertools import islice
from urllib.parse import urlsplit

import re2
import structlog
from allauth.socialaccount.models import SocialToken
from bs4 import BeautifulSoup
from django.db import IntegrityError
from django.db.models import Min
from django.utils.timezone import localdate
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError
from procrastinate.contrib.django import app
from structlog.contextvars import bind_contextvars, bound_contextvars, clear_contextvars

from plugins.gmail import (
    client,
    disconnect,
    fetch,
    get_hist,
    reset_hist,
    revoked,
    save_token,
)
from plugins.models import CustomUser, Result, Subscription, Usage
from plugins.tasks import llm
from plugins.validation import MAX_MATCH_LENGTH, MAX_MATCHES, RE2

logger = structlog.get_logger(__name__)

CHUNK_SIZE = 100
INVISIBLE = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff\u034f\u00ad"))
STRIP = ["head", "style", "script", "noscript", "template"]
URL = re.compile(r"https?://[^\s<>\"')\]]+")
IMAGE = re.compile(r"\[image:[^\]]*\]", re.IGNORECASE)
FWD = re.compile(r"\s*(?:fwd?|fw)\s*:", re.IGNORECASE)
CUT = re.compile(
    r"^(?:On [^\n]{0,200}(?:\n[^\n]{0,200})?wrote:|-{2,} ?Original Message ?-{2,}|_{10,}|-- ?|Sent from my .*|Get Outlook for .*"
    r"|From: .*\n(?:.*\n){0,3}?Sent: .*)$",
    re.IGNORECASE | re.MULTILINE,
)
FOOTER = re.compile(
    r"unsubscribe|view (?:this email |it |this )?(?:in|on) (?:your |a )?(?:browser|web)|privacy policy|terms of (?:service|use)"
    r"|all rights reserved|©|\(c\) \d{4}|(?:email|manage|update) (?:your )?(?:email |notification )?(?:preferences|settings)"
    r"|you (?:are )?receiv(?:ed|ing) this|no longer wish|this (?:e-?mail|message) was sent to|(?:do not|don't) reply"
    r"|confidentiality notice|intended (?:solely )?for the (?:use of the )?(?:named |intended )?(?:addressee|recipient)",
    re.IGNORECASE,
)


@lru_cache(maxsize=1024)
def _regex(pattern):
    try: return re2.compile(pattern, RE2)
    except re2.error: return None


def _rules(plugin):
    rules = {name: _regex(pattern) for name, pattern in plugin.rules.items()}
    for name in (n for n, r in rules.items() if r is None):
        logger.warning("bad rule", rule=name)
    return rules


def _first(m):
    groups = m.groups()
    return (next((g for g in groups if g), groups[0] or "") if groups else m.group(0))[:MAX_MATCH_LENGTH]


def _match(rules, content):
    return {name: [_first(m) for m in islice(r.finditer(content), MAX_MATCHES)] if r else [] for name, r in rules.items()}


def _refine(html):
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(STRIP):
        tag.decompose()
    text = soup.get_text("\n").replace("\xa0", " ").translate(INVISIBLE)
    return "\n".join(line for line in (" ".join(raw.split()) for raw in text.splitlines()) if line)


def _url(m):
    try: u = urlsplit(m.group(0))
    except ValueError: return ""
    short = f"{u.scheme}://{u.netloc}{u.path}".rstrip("/")
    return short if len(short) <= 80 else f"{u.scheme}://{u.netloc}"


def _trim(subject, text):
    text = IMAGE.sub("", URL.sub(_url, text.translate(INVISIBLE)))
    text = "\n".join(line for line in (" ".join(raw.split()) for raw in text.splitlines()) if line and not line.startswith(">"))
    if not FWD.match(subject or "") and (cut := CUT.search(text)) and cut.start(): text = text[:cut.start()]
    out, seen, pos = [], set(), 0
    for line in text.splitlines():
        pos += len(line) + 1
        if line in seen or not any(c.isalnum() for c in line): continue
        if len(line) <= 200 and FOOTER.search(line):
            if pos > len(text) / 2: break  # footer block reached
            continue
        seen.add(line)
        out.append(line)
    return "\n".join(out)[:llm.MAX_BODY]


def _guess(plugin, msgs, state):
    if not msgs: return []
    props = plugin.schema.get("properties")
    if not props: return [(m, {}) for m in msgs]
    usage, _ = Usage.objects.get_or_create(user_id=plugin.developer_id, date=localdate())
    if usage.used >= plugin.developer.quota:
        logger.info("quota reached", dev=plugin.developer_id)
        return []
    answers = llm.answer(plugin.schema, [state(m) for m in msgs])
    pairs = [(m, a) for m, a in zip(msgs, answers, strict=True) if not isinstance(a, Exception)]
    if errors := [a for a in answers if isinstance(a, Exception)]:
        logger.warning("llm failed", failed=len(errors), error=type(errors[0]).__name__, status=getattr(errors[0], "status_code", None))
    if pairs: usage.consume(len(pairs) * len(props))
    return pairs


def _done(user, ids):
    rows = Result.objects.filter(user=user, message__in=[bytes.fromhex(i) for i in ids]).values_list("message", "plugin_id")
    return {(b.hex(), p) for b, p in rows}


def _extract(user, todo, msgs):
    @cache
    def body(m): return m.plain or _refine(m.html or "")

    @cache
    def state(m): return llm.email(m.sender, m.subject, _trim(m.subject, body(m)))

    answered = 0
    for sub, want in todo:
        plugin = sub.plugin
        with bound_contextvars(plugin=plugin.id):
            pairs = _guess(plugin, [m for m in msgs if m.id in want], state)
            rules = _rules(plugin) if pairs and plugin.rules else None
        results = []
        for m, output in pairs:
            if rules: output["rules"] = _match(rules, f"{m.subject or ''}\n{body(m)}")  # pyright: ignore[reportIndexIssue]
            results.append(Result(user=user, plugin=plugin, version=plugin.version, output=output, message=bytes.fromhex(m.id)))
        with suppress(IntegrityError):
            Result.objects.bulk_create(results, ignore_conflicts=True)
        answered += len(results)
    return answered


@app.task(name="plugins.tasks.process")
def process(user_id):
    clear_contextvars()
    bind_contextvars(user=user_id)
    user = CustomUser.objects.filter(pk=user_id).first()
    if user is None: return
    active = Subscription.objects.filter(user=user, active=True)
    start = max(user.hist_id or 0, active.aggregate(m=Min("hist_from"))["m"] or 0)
    try: gmail = client(user)
    except SocialToken.DoesNotExist: return disconnect(user)
    if not start: return reset_hist(user, "no history id", gmail)
    try: added, latest = get_hist(gmail, start)
    except (RefreshError, HttpError) as error:
        if revoked(error): return disconnect(user, gmail)
        if isinstance(error, HttpError) and error.resp.status == 404: return reset_hist(user, "history expired", gmail)
        raise
    save_token(user, gmail)
    active.filter(hist_from=None).invalidated_update(hist_from=latest)  # pyright: ignore[reportAttributeAccessIssue]
    subs = list(active.filter(hist_from__isnull=False).prefetch_related("plugin__developer"))
    low = min((s.hist_from for s in subs), default=latest)
    ids = sorted((i for i, h in added.items() if h > low), key=added.__getitem__)
    fetched = answered = 0
    for n in range(0, len(ids), CHUNK_SIZE):
        chunk = ids[n:n + CHUNK_SIZE]
        live = set(active.nocache().values_list("pk", flat=True))  # pyright: ignore[reportAttributeAccessIssue]
        subs = [s for s in subs if s.pk in live]
        done = _done(user, chunk)
        todo = [(s, {i for i in chunk if added[i] > s.hist_from and (i, s.plugin_id) not in done}) for s in subs]  # pyright: ignore[reportAttributeAccessIssue]
        need = set().union(*(want for _, want in todo))
        try: msgs = fetch(gmail, [i for i in chunk if i in need]) if need else []
        except (RefreshError, HttpError) as error:
            if revoked(error): return disconnect(user, gmail)
            raise
        fetched += len(msgs)
        answered += _extract(user, todo, msgs)
        if n + CHUNK_SIZE < len(ids):
            CustomUser.objects.filter(pk=user.pk).invalidated_update(hist_id=added[ids[n + CHUNK_SIZE]] - 1)  # pyright: ignore[reportAttributeAccessIssue]
    if latest != user.hist_id:
        CustomUser.objects.filter(pk=user.pk).invalidated_update(hist_id=latest)  # pyright: ignore[reportAttributeAccessIssue]
    if added:
        logger.info("processed", seen=len(added), fetched=fetched, answered=answered)

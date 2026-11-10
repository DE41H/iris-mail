from concurrent.futures import ThreadPoolExecutor
from datetime import UTC
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import structlog
from allauth.socialaccount.models import SocialToken
from django.conf import settings
from django.db.transaction import atomic
from django.utils import timezone
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from simplegmail import Gmail

from plugins.models import CustomUser, Subscription

logger = structlog.get_logger(__name__)

TOKEN_URI = "https://oauth2.googleapis.com/token"
REVOKE_URI = "https://oauth2.googleapis.com/revoke"
THREADS = 12

def client(user: CustomUser):
    token = SocialToken.objects.select_related("account").get(
        account__user=user, account__provider="google"
    )
    app = settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]
    return Gmail(
        credentials=Credentials(
            token=token.token,
            refresh_token=token.token_secret,
            token_uri=TOKEN_URI,
            client_id=app["client_id"],
            client_secret=app["secret"],
            expiry=(token.expires_at or timezone.now()).replace(tzinfo=None),
        )
    )

def save_token(user: CustomUser, gmail: Gmail):
    creds = gmail.creds
    if creds.token is None or creds.expiry is None: return
    SocialToken.objects.filter(account__user=user, account__provider="google").update(
        token=creds.token, expires_at=creds.expiry.replace(tzinfo=UTC)
    )

def _read_hist_id(user: CustomUser) -> int:
    gmail = client(user)
    response = gmail.service.users().getProfile(userId="me").execute()  # type: ignore[attr-defined]
    save_token(user, gmail)
    return int(response["historyId"])

def get_hist_id(user: CustomUser) -> int | None:
    try:
        return _read_hist_id(user)
    except Exception:
        logger.warning("history id failed", user=user.pk, exc_info=True)
        return None

def revoked(error):
    if isinstance(error, RefreshError): return not error.retryable
    status = error.resp.status
    return status == 401 or (status == 403 and b"insufficientPermissions" in error.content)

def reset_hist(user, reason):
    try:
        hist_id = _read_hist_id(user)
    except (RefreshError, HttpError) as error:
        if not revoked(error): raise
        return disconnect(user)
    logger.warning("history reset", user=user.pk, reason=reason)
    CustomUser.objects.filter(pk=user.pk).invalidated_update(hist_id=hist_id)  # pyright: ignore[reportAttributeAccessIssue]

def get_hist(gmail: Gmail, start):
    ids, page = {}, None
    while True:
        data = gmail.service.users().history().list(  # pyright: ignore[reportAttributeAccessIssue]
            userId="me", startHistoryId=start, historyTypes=["messageAdded"], labelId="INBOX", pageToken=page,
        ).execute()
        for h in data.get("history", []):
            for m in h.get("messagesAdded", []):
                ids.setdefault(m["message"]["id"], int(h["id"]))
        page = data.get("nextPageToken")
        if not page:
            return ids, int(data["historyId"])

def get(gmail: Gmail, id):
    try:
        return gmail._build_message_from_ref("me", {"id": id}, attachments="ignore")
    except HttpError as error:
        if error.resp.status != 404: raise
    except Exception:
        logger.warning("mail unreadable", mail=id, exc_info=True)

def fetch(gmail: Gmail, ids):
    size = -(-len(ids) // THREADS)
    def part(n):
        g = Gmail(credentials=gmail.creds)
        try: return [m for m in (get(g, i) for i in ids[n:n + size]) if m]
        finally: g.service.close()

    with ThreadPoolExecutor(THREADS) as pool:
        return [m for ms in pool.map(part, range(0, len(ids), size or 1)) for m in ms]

def revoke(user: CustomUser):
    token = SocialToken.objects.filter(account__user=user, account__provider="google").first()
    if token is None: return
    try:
        urlopen(Request(REVOKE_URI, data=urlencode({"token": token.token_secret or token.token}).encode()), timeout=10)
    except OSError:
        logger.warning("revoke failed", user=user.pk, exc_info=True)

def disconnect(user):
    logger.warning("google revoked", user=user.pk)
    with atomic():
        SocialToken.objects.filter(account__user=user, account__provider="google").delete()
        Subscription.objects.filter(user=user, active=True).invalidated_update(active=False)  # pyright: ignore[reportAttributeAccessIssue]

import logging
from datetime import UTC
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from allauth.socialaccount.models import SocialToken
from django.conf import settings
from django.db.transaction import atomic
from django.utils import timezone
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from simplegmail import Gmail

from plugins.models import CustomUser, Subscription

logger = logging.getLogger(__name__)

TOKEN_URI = "https://oauth2.googleapis.com/token"
REVOKE_URI = "https://oauth2.googleapis.com/revoke"

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

def get_hist_id(user: CustomUser) -> int | None:
    try:
        gmail = client(user)
        response = gmail.service.users().getProfile(userId="me").execute()  # type: ignore[attr-defined]
        save_token(user, gmail)
        return int(response["historyId"])
    except Exception:
        logger.warning("Could not read Gmail history id", extra={"user_id": user.pk}, exc_info=True)
        return None

def reset_hist(user, reason):
    logger.warning("Gmail history reset, older mail skipped", extra={"user_id": user.pk, "reason": reason})
    CustomUser.objects.filter(pk=user.pk).invalidated_update(hist_id=get_hist_id(user))  # pyright: ignore[reportAttributeAccessIssue]

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
        logger.info("Gmail message deleted before fetch, skipped", extra={"message_id": id})

def fetch(gmail: Gmail, ids):
    try:
        return gmail._get_messages_from_refs("me", [{"id": i} for i in ids], attachments="ignore")
    except HttpError as error:
        if error.resp.status != 404: raise
    return [m for m in (get(gmail, id) for id in ids) if m]

def revoke(user: CustomUser):
    token = SocialToken.objects.filter(account__user=user, account__provider="google").first()
    if token is None: return
    try:
        urlopen(Request(REVOKE_URI, data=urlencode({"token": token.token_secret or token.token}).encode()), timeout=10)
    except OSError:
        logger.warning("Could not revoke Google token", extra={"user_id": user.pk}, exc_info=True)

def disconnect(user):
    logger.warning("Google access revoked, plugins turned off", extra={"user_id": user.pk})
    with atomic():
        SocialToken.objects.filter(account__user=user, account__provider="google").delete()
        Subscription.objects.filter(user=user, active=True).invalidated_update(active=False)  # pyright: ignore[reportAttributeAccessIssue]

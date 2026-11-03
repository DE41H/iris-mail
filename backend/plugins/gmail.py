import logging
from datetime import UTC
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from allauth.socialaccount.models import SocialToken
from django.conf import settings
from django.utils import timezone
from google.oauth2.credentials import Credentials
from simplegmail import Gmail

from plugins.models import CustomUser

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

def get_hist_id(user: CustomUser) -> int:
    gmail = client(user)
    response = gmail.service.users().getProfile(userId="me").execute()  # type: ignore[attr-defined]
    save_token(user, gmail)
    return int(response["historyId"])

def revoke(user: CustomUser):
    token = SocialToken.objects.filter(account__user=user, account__provider="google").first()
    if token is None: return
    try:
        urlopen(Request(REVOKE_URI, data=urlencode({"token": token.token_secret or token.token}).encode()), timeout=10)
    except OSError:
        logger.warning("Google token revoke failed", extra={"user_id": user.id}, exc_info=True)

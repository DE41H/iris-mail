from allauth.socialaccount.models import SocialToken
from django.conf import settings
from django.utils import timezone
from google.oauth2.credentials import Credentials
from simplegmail import Gmail

from plugins.models import CustomUser

TOKEN_URI = "https://oauth2.googleapis.com/token"

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

def watch(user: CustomUser):
    body = {"topicName": settings.GMAIL_PUBSUB_TOPIC, "labelIds": ["INBOX"]}
    return client(user).service.users().watch(userId="me", body=body).execute()  # type: ignore[attr-defined]

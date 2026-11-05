import logging

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Error

REQUIRED_GOOGLE_SCOPES = {
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.readonly",
}

logger = logging.getLogger(__name__)

class GmailGoogleOAuth2Adapter(GoogleOAuth2Adapter):
    def complete_login(self, request, app, token, **kwargs):
        scopes = set(kwargs["response"].get("scope", "").split())
        if not REQUIRED_GOOGLE_SCOPES.issubset(scopes):
            logger.info("Google sign-in missing scopes", extra={"missing": sorted(REQUIRED_GOOGLE_SCOPES - scopes)})
            raise OAuth2Error("Allow Iris to see your profile, email and read-only Gmail.")
        return super().complete_login(request, app, token, **kwargs)

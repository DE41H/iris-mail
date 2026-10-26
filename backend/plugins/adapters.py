from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Error

REQUIRED_GOOGLE_SCOPES = {
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.readonly",
}

class GmailGoogleOAuth2Adapter(GoogleOAuth2Adapter):
    def complete_login(self, request, app, token, **kwargs):
        scopes = set(kwargs["response"].get("scope", "").split())
        if not REQUIRED_GOOGLE_SCOPES.issubset(scopes):
            raise OAuth2Error("Google access was not granted for profile, email and Gmail read-only.")
        return super().complete_login(request, app, token, **kwargs)

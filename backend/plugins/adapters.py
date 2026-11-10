from urllib.parse import urlencode

import structlog
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from django.http import HttpResponseRedirect
from django.urls import reverse

REQUIRED_GOOGLE_SCOPES = {
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.readonly",
}

logger = structlog.get_logger(__name__)


class SocialAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        token = sociallogin.token
        if not token or token.token_secret: return
        if token.pk: token.delete()
        logger.info("consent needed", user=sociallogin.user.pk)  # pyright: ignore[reportOptionalMemberAccess]
        query = urlencode({"action": "reauthenticate", "next": sociallogin.state.get("next") or ""})
        raise ImmediateHttpResponse(HttpResponseRedirect(f"{reverse('google_login')}?{query}"))


class GmailGoogleOAuth2Adapter(GoogleOAuth2Adapter):
    def complete_login(self, request, app, token, **kwargs):
        scopes = set(kwargs["response"].get("scope", "").split())
        if not REQUIRED_GOOGLE_SCOPES.issubset(scopes):
            logger.info("scopes missing", missing=sorted(REQUIRED_GOOGLE_SCOPES - scopes))
            raise OAuth2Error("Allow Iris to see your profile, email and read-only Gmail.")
        return super().complete_login(request, app, token, **kwargs)

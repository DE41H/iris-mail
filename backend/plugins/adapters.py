import logging
from urllib.parse import urlencode

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

logger = logging.getLogger(__name__)


class SocialAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        token, retried = sociallogin.token, request.session.pop("google_consent", False)
        if not token or token.token_secret or retried: return
        if token.pk: token.delete()
        request.session["google_consent"] = True
        logger.info("Google sign-in without refresh token, asking for consent", extra={"user_id": sociallogin.user.pk})  # pyright: ignore[reportOptionalMemberAccess]
        query = urlencode({"action": "reauthenticate", "next": sociallogin.state.get("next") or ""})
        raise ImmediateHttpResponse(HttpResponseRedirect(f"{reverse('google_login')}?{query}"))


class GmailGoogleOAuth2Adapter(GoogleOAuth2Adapter):
    def complete_login(self, request, app, token, **kwargs):
        scopes = set(kwargs["response"].get("scope", "").split())
        if not REQUIRED_GOOGLE_SCOPES.issubset(scopes):
            logger.info("Google sign-in missing scopes", extra={"missing": sorted(REQUIRED_GOOGLE_SCOPES - scopes)})
            raise OAuth2Error("Allow Iris to see your profile, email and read-only Gmail.")
        return super().complete_login(request, app, token, **kwargs)

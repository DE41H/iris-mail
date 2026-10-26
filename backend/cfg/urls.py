from allauth.socialaccount import views as socialaccount_views
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2CallbackView,
    OAuth2LoginView,
)
from django.contrib import admin
from django.urls import include, path

from plugins.adapters import GmailGoogleOAuth2Adapter

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/google/login/", OAuth2LoginView.adapter_view(GmailGoogleOAuth2Adapter), name="google_login"),
    path("accounts/google/login/callback/", OAuth2CallbackView.adapter_view(GmailGoogleOAuth2Adapter), name="google_callback"),
    path("accounts/login/cancelled/", socialaccount_views.login_cancelled, name="socialaccount_login_cancelled"),
    path("signup/", socialaccount_views.signup, name="socialaccount_signup"),
    path("accounts/", include("allauth.account.urls")),
    path("api/", include("plugins.urls")),
]

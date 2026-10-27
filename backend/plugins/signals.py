from allauth.account.signals import user_signed_up
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.signals import social_account_added
from django.db import transaction
from django.dispatch import receiver

from plugins.tasks import start_watch


@receiver([social_account_added, user_signed_up])
def watch_on_connect(sender, request=None, sociallogin=None, user=None, **kwargs):
    user = user or (sociallogin and sociallogin.user)
    if user and SocialAccount.objects.filter(user=user, provider="google").exists():
        transaction.on_commit(lambda: start_watch.defer(user_id=str(user.pk)))

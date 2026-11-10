import structlog
from allauth.account.signals import user_signed_up
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.signals import social_account_added
from django.db import transaction
from django.dispatch import receiver

from plugins.tasks import init_hist

logger = structlog.get_logger(__name__)


@receiver([social_account_added, user_signed_up])
def init_poll(sender, request=None, sociallogin=None, user=None, **kwargs):
    user = user or (sociallogin and sociallogin.user)
    if user and SocialAccount.objects.filter(user=user, provider="google").exists():
        logger.info("google connected", user=user.pk)
        transaction.on_commit(lambda: init_hist.defer(user_id=str(user.pk)))

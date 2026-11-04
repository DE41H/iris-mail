from hashlib import sha256
from secrets import compare_digest, token_urlsafe

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import IntegrityError, models
from django.db.models.functions import Upper
from django.db.transaction import atomic
from uuid6 import uuid7

from plugins.validation import RuleValidator, SchemaValidator


class UserTier(models.IntegerChoices):
    BASE = 1, "Base"
    CORE = 2, "Core"
    PRIME = 3, "Prime"
    ULTRA = 4, "Ultra"

class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    email = models.EmailField(unique=True)
    tier = models.PositiveSmallIntegerField(choices=UserTier.choices, default=UserTier.BASE)
    hist_id = models.PositiveBigIntegerField(null=True, blank=True)

    class Meta(AbstractUser.Meta):
        indexes = (models.Index(Upper("email"), name="user_email_upper_idx"),)  # email__iexact


class Plugin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    developer = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dev_plugins", db_index=False)  # covered by unique (developer, name)
    name = models.SlugField(max_length=255, db_index=False)  # covered by unique (developer, name)
    desc = models.TextField(max_length=1024, default="")
    schema = models.JSONField(default=dict, validators=[SchemaValidator()])
    rules = models.JSONField(default=dict, blank=True, validators=[RuleValidator()])
    version = models.PositiveSmallIntegerField(default=1, editable=False)
    key = models.BinaryField(max_length=32, blank=True, null=True)  # looked up by unique prefix
    prefix = models.CharField(max_length=16, unique=True, blank=True, null=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("developer", "name"),
                name="unique_developer_plugin_name",
            ),
            models.CheckConstraint(
                condition=models.Q(key__isnull=True, prefix__isnull=True) | models.Q(key__isnull=False, prefix__isnull=False),
                name="plugin_key_prefix_together",
            ),
        )

    @classmethod
    def gen_hash(cls, content: str) -> bytes:
        return sha256(content.encode("utf-8")).digest()

    @classmethod
    def gen_key(cls):
        secret = token_urlsafe(32)
        pre = f"iris_{secret[:11]}"
        full = f"{pre}_{secret}"
        hash = cls.gen_hash(full)
        return pre, hash, full

    @classmethod
    def auth_key(cls, key: str):
        if not key or not key.startswith("iris_") or len(key) != 60: return None
        hash = cls.gen_hash(key)
        plugin = cls.objects.nocache().prefetch_related("developer").filter(prefix__isnull=False, prefix=key[:16]).first()  # pyright: ignore[reportAttributeAccessIssue]
        return plugin if plugin and compare_digest(bytes(plugin.key), hash) else None

    def rot_key(self):
        pre, hash, full = self.__class__.gen_key()
        while True:
            try:
                with atomic():
                    updated = self.__class__.objects.filter(pk=self.pk).invalidated_update(key=hash, prefix=pre)  # pyright: ignore[reportAttributeAccessIssue]
                    if updated: self.refresh_from_db(fields=("key", "prefix"))
                    return full if updated else None
            except IntegrityError:
                pre, hash, full = self.__class__.gen_key()


class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions", db_index=False)  # covered by unique (user, plugin)
    plugin = models.ForeignKey(to=Plugin, on_delete=models.CASCADE, related_name="subscribers")
    active = models.BooleanField(default=False)
    hist_from = models.PositiveBigIntegerField(null=True, blank=True)  # Gmail history id when turned on; None: set on next poll
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("user", "plugin"),
                name="unique_user_plugin_subscription",
            ),
        )
        indexes = (
            models.Index(fields=("user",), condition=models.Q(active=True), name="subscription_active_user_idx"),
        )

    def set_active(self, active: bool, **fields):
        self.__class__.objects.filter(pk=self.pk).invalidated_update(active=active, **fields)  # pyright: ignore[reportAttributeAccessIssue]
        self.refresh_from_db(fields=("active", *fields))


class Result(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="results", db_index=False)  # covered by unique (user, message, plugin)
    plugin = models.ForeignKey(to=Plugin, on_delete=models.CASCADE, related_name="results", db_index=False)  # covered by (plugin, -id)
    output = models.JSONField(default=dict)
    version = models.PositiveSmallIntegerField(default=1)
    message = models.BinaryField(max_length=8)
    fetched = models.BooleanField(default=False)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("user", "message", "plugin"),
                name="unique_result_per_message",
            ),
        )
        indexes = (
            models.Index(
                fields=("plugin", "-id"),
                condition=models.Q(fetched=False),
                name="result_plugin_unfetched_idx",
            ),
            models.Index(fields=("plugin", "-id")),
            models.Index(fields=("plugin", "user", "-id")),
            models.Index(fields=("plugin", "version", "-id")),
        )

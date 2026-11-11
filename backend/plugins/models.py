from datetime import timedelta
from hashlib import sha256
from secrets import compare_digest, token_urlsafe
from uuid import UUID

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import URLValidator
from django.db import models
from django.db.models.functions import Upper
from django.db.transaction import atomic
from django.utils.timezone import now
from uuid6 import uuid7

from plugins.validation import RuleValidator, SchemaValidator

AGENT_PREFIX = "iris_agent_"
PLUGIN_PREFIX = "iris_"


class UserTier(models.IntegerChoices):
    BASE = 1, "Base"
    CORE = 2, "Core"
    PRIME = 3, "Prime"
    ULTRA = 4, "Ultra"


QUOTAS = {
    UserTier.BASE: 200,
    UserTier.CORE: 1_000,
    UserTier.PRIME: 5_000,
    UserTier.ULTRA: 25_000,
}

CODE_TTL = timedelta(minutes=3)


def uuid_before(delta: timedelta) -> UUID:
    return UUID(int=int((now() - delta).timestamp() * 1000) << 80)


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    email = models.EmailField(unique=True)
    tier = models.PositiveSmallIntegerField(choices=UserTier.choices, default=UserTier.BASE)
    hist_id = models.PositiveBigIntegerField(null=True, blank=True)

    class Meta(AbstractUser.Meta):
        indexes = (models.Index(Upper("email"), name="user_email_upper_idx"),)

    @property
    def quota(self) -> int:
        return QUOTAS.get(self.tier, 0)


class Usage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="usage", db_index=False)
    date = models.DateField()
    used = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = (models.UniqueConstraint(fields=("user", "date"), name="unique_user_usage_date"),)

    def consume(self, value: int):
        self.__class__.objects.filter(pk=self.id).update(used=models.F("used") + value)


class Plugin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    developer = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dev_plugins", db_index=False)
    name = models.SlugField(max_length=255, db_index=False)
    desc = models.TextField(max_length=1024, default="")
    schema = models.JSONField(default=dict, validators=[SchemaValidator()])
    rules = models.JSONField(default=dict, blank=True, validators=[RuleValidator()])
    version = models.PositiveSmallIntegerField(default=1, editable=False)
    key = models.BinaryField(max_length=32)
    prefix = models.CharField(max_length=16, unique=True)
    redirect = models.URLField(max_length=256, validators=[URLValidator(schemes=["https"])])

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("developer", "name"),
                name="unique_developer_plugin_name",
            ),
        )

    @classmethod
    def gen_hash(cls, content: str) -> bytes:
        return sha256(content.encode("utf-8")).digest()

    @classmethod
    def gen_key(cls):
        secret = token_urlsafe(32)
        pre = f"{PLUGIN_PREFIX}{secret[:11]}"
        full = f"{pre}_{secret}"
        hash = cls.gen_hash(full)
        return pre, hash, full

    @classmethod
    def auth_key(cls, key: str):
        if not key or not key.startswith(PLUGIN_PREFIX) or len(key) != 60: return None
        hash = cls.gen_hash(key)
        plugin = cls.objects.nocache().prefetch_related("developer").filter(prefix=key[:16]).first()  # pyright: ignore[reportAttributeAccessIssue]
        return plugin if plugin and compare_digest(bytes(plugin.key), hash) else None


class CodeStatus(models.IntegerChoices):
    PENDING = 0, "Pending"
    ACCEPTED = 1, "Accepted"
    DENIED = 2, "Denied"


class Code(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    hash = models.BinaryField(max_length=32, unique=True)
    plugin = models.ForeignKey(to=Plugin, on_delete=models.CASCADE, related_name="codes", db_index=False)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="codes", null=True, blank=True, db_index=False)
    status = models.PositiveSmallIntegerField(choices=CodeStatus.choices, default=CodeStatus.PENDING)

    class Meta:
        constraints = (
            models.CheckConstraint(
                condition=models.Q(status=CodeStatus.PENDING, user__isnull=True) | (~models.Q(status=CodeStatus.PENDING) & models.Q(user__isnull=False)),
                name="code_user_iff_used",
            ),
        )

    @property
    def expired(self) -> bool:
        return self.status == CodeStatus.PENDING and self.id < uuid_before(CODE_TTL)

    @classmethod
    def pending(cls):
        return cls.objects.filter(status=CodeStatus.PENDING, id__gte=uuid_before(CODE_TTL))

    @atomic
    def accept(self, user_id, hist_from=None) -> bool:
        if not self.__class__.pending().filter(pk=self.pk).update(user_id=user_id, status=CodeStatus.ACCEPTED): return False
        sub, created = Subscription.objects.get_or_create(user_id=user_id, plugin_id=self.plugin_id, defaults={"active": True, "hist_from": hist_from})  # pyright: ignore[reportAttributeAccessIssue]
        if not created and not sub.active: sub.set_active(True, hist_from=hist_from)
        return True

    def deny(self, user_id) -> bool:
        return bool(self.__class__.pending().filter(pk=self.pk).update(user_id=user_id, status=CodeStatus.DENIED))


class AgentKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    name = models.CharField(max_length=256, db_index=False)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="keys", db_index=False)
    prefix = models.CharField(max_length=22, unique=True)
    key = models.BinaryField(max_length=32)

    class Meta:
        indexes = (models.Index(fields=("user", "-id")),)

    @classmethod
    def gen_key(cls):
        secret = token_urlsafe(32)
        pre = f"{AGENT_PREFIX}{secret[:11]}"
        full = f"{pre}_{secret}"
        return pre, Plugin.gen_hash(full), full

    @classmethod
    def auth_key(cls, key: str):
        if not key or not key.startswith(AGENT_PREFIX) or len(key) != 66: return None
        agent = cls.objects.prefetch_related("user").filter(prefix=key[:22]).first()
        return agent if agent and compare_digest(bytes(agent.key), Plugin.gen_hash(key)) else None


class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions", db_index=False)  # covered by unique (user, plugin)
    plugin = models.ForeignKey(to=Plugin, on_delete=models.CASCADE, related_name="subscribers")
    active = models.BooleanField(default=False)
    hist_from = models.PositiveBigIntegerField(null=True, blank=True)
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
        if self.active == active and not fields: return
        self.__class__.objects.filter(pk=self.pk).invalidated_update(active=active, **fields)  # pyright: ignore[reportAttributeAccessIssue]
        self.refresh_from_db(fields=("active", *fields))


class Result(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="results", db_index=False)
    plugin = models.ForeignKey(to=Plugin, on_delete=models.CASCADE, related_name="results", db_index=False)
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

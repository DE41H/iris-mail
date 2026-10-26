from hashlib import sha256
from secrets import compare_digest, token_urlsafe

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions.uuid import UUID7

# Create your models here.

class UserTier(models.IntegerChoices):
    BASE = 1, "Base"
    CORE = 2, "Core"
    PRIME = 3, "Prime"

class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=UUID7, editable=False)
    tier = models.PositiveSmallIntegerField(choices=UserTier.choices, default=UserTier.BASE)


class Plugin(models.Model):
    id = models.UUIDField(primary_key=True, default=UUID7, editable=False)
    developer = models.ForeignKey(to=CustomUser, on_delete=models.CASCADE, related_name="dev_plugins")
    name = models.SlugField(max_length=255)
    desc = models.TextField(blank=True, null=True)
    schema = models.JSONField(default=list)
    hint = models.CharField(max_length=512, blank=True, null=True)
    key = models.BinaryField(max_length=32, unique=True, blank=True, null=True)
    prefix = models.CharField(max_length=16, unique=True, blank=True, null=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("developer", "name"),
                name="unique_developer_plugin_name",
            ),
        )

    @classmethod
    def get_hash(cls, content: str) -> bytes:
        return sha256(content.encode("utf-8")).digest()

    @classmethod
    def authenticate(cls, key: str):
        if not key or not key.startswith("iris_") or len(key) != 60: return None
        hash = cls.get_hash(key)
        plugin = cls.objects.filter(prefix__isnull=False, prefix=key[:16]).first()
        return plugin if plugin and compare_digest(bytes(plugin.key), hash) else None

    def rotate_key(self):
        secret = token_urlsafe(32)
        pre = f"iris_{secret[:11]}"
        full = f"{pre}_{secret}"
        hash = self.__class__.get_hash(full)
        if self.__class__.objects.filter(pk=self.pk).update(key=hash, prefix=pre):
            self.refresh_from_db(fields=("key", "prefix"))
        return full

    def __str__(self) -> str:
        return f"{self.name} by {self.developer}"


class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=UUID7, editable=False)
    user = models.ForeignKey(to=CustomUser, on_delete=models.CASCADE, related_name="subscriptions")
    plugin = models.ForeignKey(to=Plugin, on_delete=models.CASCADE, related_name="subscribers")
    active = models.BooleanField(default=True)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("user", "plugin"),
                name="unique_user_plugin_subscription"
            ),
        )
        indexes = (
            models.Index(fields=("user", "active")),
        )

    def toggle(self):
        self.__class__.objects.filter(pk=self.pk).update(active=~models.F("active"))
        self.refresh_from_db(fields=("active",))

    def __str__(self) -> str:
        return f"{self.user} on {self.plugin} at {self.time}"


class Result(models.Model):
    id = models.UUIDField(primary_key=True, default=UUID7, editable=False)
    user = models.ForeignKey(to=CustomUser, on_delete=models.CASCADE, related_name="results")
    plugin = models.ForeignKey(to=Plugin, on_delete=models.CASCADE, related_name="results")
    output = models.JSONField()
    fetched = models.BooleanField(default=False)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = (
            models.Index(
                fields=("plugin", "-time"),
                condition=models.Q(fetched=False),
            ),
        )

    def __str__(self) -> str:
        return f"For {self.user} by {self.plugin} at {self.time}"

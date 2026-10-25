from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.functions.uuid import UUID7

# Create your models here.

User = get_user_model()


class Plugin(models.Model):
    id = models.UUIDField(primary_key=True, default=UUID7, editable=False)
    developer = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="dev_plugins")
    name = models.SlugField(max_length=255)
    desc = models.TextField(blank=True, null=True)
    schema = models.JSONField(default=list)
    hint = models.CharField(max_length=512, blank=True, null=True)
    key = models.CharField(max_length=128, unique=True, blank=True, null=True)
    prefix = models.CharField(max_length=16, blank=True, null=True, db_index=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("developer", "name"),
                name="unique_developer_plugin_name",
            ),
        )

    def __str__(self) -> str:
        return f"{self.name} by {self.developer}"


class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=UUID7, editable=False)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="subscriptions")
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

    def __str__(self) -> str:
        return f"{self.user} on {self.plugin} at {self.time}"


class Result(models.Model):
    id = models.UUIDField(primary_key=True, default=UUID7, editable=False)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="results")
    plugin = models.ForeignKey(to=Plugin, on_delete=models.CASCADE, related_name="results")
    hash = models.CharField(max_length=256, db_index=True)
    output = models.JSONField()
    fetched = models.BooleanField(default=False)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = (
            models.Index(fields=("plugin", "fetched", "-time")),
            models.Index(fields=("user", "plugin", "-time")),
        )

    def __str__(self) -> str:
        return f"For {self.user} by {self.plugin} at {self.time}"

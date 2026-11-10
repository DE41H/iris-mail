from uuid import UUID

from allauth.socialaccount.models import SocialAccount, SocialToken
from django.core.validators import URLValidator
from django.db.models import F
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from plugins.models import (
    QUOTAS,
    Code,
    CodeStatus,
    CustomUser,
    Plugin,
    Result,
    Subscription,
    Usage,
    UserTier,
)
from plugins.validation import EMPTY_SCHEMA

NAME_TAKEN = "You already have a plugin with this name."


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id", "username", "email")
        read_only_fields = fields


class MeSerializer(CustomUserSerializer):
    google = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    tier = serializers.CharField(source="get_tier_display", read_only=True)
    quota = serializers.IntegerField(read_only=True)
    tiers = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = (*CustomUserSerializer.Meta.fields, "tier", "google", "avatar", "quota", "tiers")
        read_only_fields = fields

    def get_google(self, user) -> bool:
        return SocialToken.objects.filter(account__user=user, account__provider="google").exists()

    def get_tiers(self, user) -> list[dict[str, int | str]]:
        return [{"tier": t.value, "name": str(t.label), "quota": QUOTAS[t]} for t in UserTier]

    def get_avatar(self, user) -> str | None:
        account = SocialAccount.objects.filter(user=user, provider="google").first()
        return account.extra_data.get("picture") if account else None


class PluginSerializer(serializers.ModelSerializer):
    subscriber_count = serializers.IntegerField(read_only=True)
    result_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Plugin
        fields = ("id", "developer", "name", "desc", "schema", "rules", "redirect", "version", "prefix", "subscriber_count", "result_count")
        read_only_fields = ("id", "developer", "version", "prefix")
        extra_kwargs = {"desc": {"allow_blank": True}, "redirect": {"required": True, "validators": [URLValidator(schemes=["https"])]}}  # noqa: RUF012

    def validate(self, attrs):
        schema = attrs.get("schema", getattr(self.instance, "schema", None) or EMPTY_SCHEMA)
        rules = attrs.get("rules", getattr(self.instance, "rules", {}))
        if not schema.get("properties") and not rules:
            raise serializers.ValidationError("Add at least one question or rule.")
        if self.instance is None: attrs.setdefault("schema", EMPTY_SCHEMA)
        return attrs

    def update(self, instance, validated_data):
        if any(k in validated_data and validated_data[k] != getattr(instance, k) for k in ("schema", "rules")):
            validated_data["version"] = F("version") % 32767 + 1
        instance = super().update(instance, validated_data)
        if "version" in validated_data: instance.refresh_from_db(fields=("version",))
        return instance


class SubscriptionSerializer(serializers.ModelSerializer):
    plugin_name = serializers.CharField(source="plugin.name", read_only=True)
    plugin_desc = serializers.CharField(source="plugin.desc", read_only=True)
    user = serializers.UUIDField(source="user_id", required=False)
    email = serializers.EmailField(write_only=True, required=False)

    class Meta:
        model = Subscription
        fields = ("id", "user", "email", "plugin", "plugin_name", "plugin_desc", "active", "time")
        read_only_fields = ("id", "plugin", "plugin_name", "plugin_desc", "active", "time")

    def validate(self, attrs):
        email = attrs.pop("email", None)
        if ("user_id" in attrs) == (email is not None):
            raise serializers.ValidationError("Send `user` or `email`")
        if email is not None:
            attrs["user_id"] = CustomUser.objects.filter(email__iexact=email).values_list("pk", flat=True).first()
        return attrs


class ResultSerializer(serializers.ModelSerializer):
    output = serializers.DictField(read_only=True)

    class Meta:
        model = Result
        fields = ("id", "user", "plugin", "version", "output", "fetched", "time")
        read_only_fields = fields


class UsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usage
        fields = ("date", "used")
        read_only_fields = fields


class CodeSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = Code
        fields = ("status", "user", "email")
        read_only_fields = fields

    @extend_schema_field(serializers.ChoiceField(choices=["pending", "accepted", "denied", "expired"]))
    def get_status(self, code) -> str:
        return "expired" if code.expired else CodeStatus(code.status).name.lower()

    def get_user(self, code) -> UUID | None:
        return code.user_id if code.status == CodeStatus.ACCEPTED else None

    def get_email(self, code) -> str | None:
        return code.user.email if code.status == CodeStatus.ACCEPTED else None


class ConnectSerializer(serializers.ModelSerializer):
    developer = serializers.CharField(source="developer.username", read_only=True)

    class Meta:
        model = Plugin
        fields = ("id", "name", "desc", "developer", "schema", "rules")
        read_only_fields = fields

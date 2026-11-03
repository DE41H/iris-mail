from django.shortcuts import get_object_or_404
from rest_framework import serializers

from plugins.models import CustomUser, Plugin, Result, Subscription


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id", "username", "email", "tier")
        read_only_fields = fields


class PluginSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plugin
        fields = ("id", "developer", "name", "desc", "schema", "hint", "prefix")
        read_only_fields = ("id", "developer", "prefix")
        extra_kwargs = {  # noqa: RUF012
            "desc": {"allow_blank": True},
            "hint": {"allow_blank": True},
            "schema": {"required": True},
        }

    def validate_name(self, value):
        user = self.context["request"].user
        if Plugin.objects.filter(developer=user, name=value).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError("You already have a plugin with this name.")
        return value


class SubscriptionSerializer(serializers.ModelSerializer):
    plugin_name = serializers.CharField(source="plugin.name", read_only=True)
    plugin_desc = serializers.CharField(source="plugin.desc", read_only=True)
    email = serializers.EmailField(write_only=True, required=False)

    class Meta:
        model = Subscription
        fields = ("id", "user", "email", "plugin", "plugin_name", "plugin_desc", "active", "time")
        read_only_fields = ("id", "plugin", "plugin_name", "plugin_desc", "active", "time")
        extra_kwargs = {"user": {"required": False}}  # noqa: RUF012

    def validate(self, attrs):
        email = attrs.pop("email", None)
        if ("user" in attrs) == (email is not None):
            raise serializers.ValidationError("Give either user or email.")
        if email is not None:
            attrs["user"] = get_object_or_404(CustomUser, email=email)
        plugin = self.context["request"].auth
        if Subscription.objects.filter(user=attrs["user"], plugin=plugin).exists():
            raise serializers.ValidationError("This user already has a subscription to this plugin.")
        return attrs


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ("id", "user", "plugin", "output", "fetched", "time")
        read_only_fields = fields

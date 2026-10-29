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
        }

    def validate_name(self, value):
        user = self.context["request"].user
        if Plugin.objects.filter(developer=user, name=value).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError("You already have a plugin with this name.")
        return value


class SubscriptionSerializer(serializers.ModelSerializer):
    plugin_name = serializers.CharField(source="plugin.name", read_only=True)
    plugin_desc = serializers.CharField(source="plugin.desc", read_only=True)

    class Meta:
        model = Subscription
        fields = ("id", "user", "plugin", "plugin_name", "plugin_desc", "active", "time")
        read_only_fields = ("id", "plugin", "plugin_name", "plugin_desc", "active", "time")

    def validate(self, attrs):
        plugin = self.context["request"].auth
        if Subscription.objects.filter(user=attrs["user"], plugin=plugin).exists():
            raise serializers.ValidationError("This user already has a subscription to this plugin.")
        return attrs


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ("id", "user", "plugin", "output", "fetched", "time")
        read_only_fields = fields

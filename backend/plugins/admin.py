from allauth.core.ratelimit import consume_or_429
from allauth.socialaccount.models import SocialToken
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django_otp.admin import OTPAdminSite

from plugins.models import CustomUser, Plugin, Result, Subscription, Usage

admin.site.__class__ = OTPAdminSite
admin.site.site_header = admin.site.site_title = "Iris admin"
_login = admin.site.login

def login(request, extra_context=None):
    if request.method == 'POST':
        key = request.POST.get('username', '').lower()
        if limited := consume_or_429(request, action='login_failed', key=key):
            return limited
    return _login(request, extra_context)

admin.site.login = login
admin.site.unregister(SocialToken)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "username", "tier", "quota", "is_staff", "date_joined", "last_login")
    list_filter = ("tier", "is_staff", "is_superuser", "is_active")
    list_editable = ("tier",)
    search_fields = ("email", "username")
    ordering = ("-id",)
    readonly_fields = ("hist_id", "quota", "last_login", "date_joined")
    fieldsets = (*UserAdmin.fieldsets, ("Iris", {"fields": ("tier", "quota", "hist_id")}))  # pyright: ignore[reportOptionalIterable]

    @admin.display(description="Daily quota")
    def quota(self, obj):
        return obj.quota


@admin.register(Plugin)
class PluginAdmin(admin.ModelAdmin):
    list_display = ("name", "developer", "version", "prefix", "subs")
    list_select_related = ()
    search_fields = ("name", "developer__email")
    autocomplete_fields = ("developer",)
    readonly_fields = ("version", "prefix")

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("developer").annotate(subs=Count("subscribers"))

    @admin.display(description="Subscribers", ordering="subs")
    def subs(self, obj):
        return obj.subs


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plugin", "active", "time")
    list_filter = ("active",)
    list_select_related = ()
    search_fields = ("user__email", "plugin__name")
    autocomplete_fields = ("user", "plugin")
    readonly_fields = ("hist_from", "time")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("user", "plugin")


class ReadOnly(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Usage)
class UsageAdmin(ReadOnly):
    list_display = ("user", "date", "used")
    search_fields = ("user__email",)
    ordering = ("-id",)
    list_select_related = ()

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("user")


@admin.register(Result)
class ResultAdmin(ReadOnly):
    list_display = ("id", "user", "plugin", "version", "fetched", "time")
    list_filter = ("fetched",)
    search_fields = ("user__email", "plugin__name")
    ordering = ("-id",)
    list_select_related = ()
    show_full_result_count = False

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("user", "plugin")

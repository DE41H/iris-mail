from allauth.core.ratelimit import consume_or_429
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django_otp.admin import OTPAdminSite

from plugins.models import CustomUser, Plugin, Result, Subscription

admin.site.__class__ = OTPAdminSite
_login = admin.site.login

def login(request, extra_context=None):
    if request.method == 'POST':
        key = request.POST.get('username', '').lower()
        if limited := consume_or_429(request, action='login_failed', key=key):
            return limited
    return _login(request, extra_context)

admin.site.login = login
admin.site.register(CustomUser, UserAdmin)
admin.site.register(Plugin)
admin.site.register(Subscription)
admin.site.register(Result)

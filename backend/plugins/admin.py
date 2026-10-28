from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from plugins.models import CustomUser, Plugin, Result, Subscription

admin.site.register(CustomUser, UserAdmin)
admin.site.register(Plugin)
admin.site.register(Subscription)
admin.site.register(Result)

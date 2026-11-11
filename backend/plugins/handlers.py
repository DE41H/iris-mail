from django.utils.timezone import localdate
from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler as drf_handler

from plugins.models import Usage
from plugins.throttling import KEYS


def exception_handler(exc, context):
    response = drf_handler(exc, context)
    request = context["request"]
    if response is not None and isinstance(response.data, dict) and isinstance(exc, Throttled) and isinstance(request.auth, KEYS):
        used = Usage.objects.filter(user_id=request.user.pk, date=localdate()).values_list("used", flat=True).first() or 0
        response.data.update(quota=request.user.quota, left=max(request.user.quota - used, 0))  # pyright: ignore[reportOptionalMemberAccess]
    return response

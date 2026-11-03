from urllib.parse import parse_qs, urlparse

from django.core.cache import cache
from rest_framework.pagination import CursorPagination

from plugins.models import Plugin, Result


class UUIDCursorPagination(CursorPagination):
    ordering = "-id"


class AckCursorPagination(UUIDCursorPagination):
    def paginate_queryset(self, queryset, request, view=None):
        plugin: Plugin = request.auth
        cursor = request.query_params.get(self.cursor_query_param)
        if cursor and (ids := cache.get(f"ack:{plugin.pk}:{cursor}")):
            Result.objects.filter(plugin=plugin, pk__in=ids).update(fetched=True)
            cache.delete(f"ack:{plugin.pk}:{cursor}")
        page = super().paginate_queryset(queryset, request, view)
        if page and not self.has_next:
            self.has_next, self.next_position = True, None
        if page:
            next_cursor = parse_qs(urlparse(self.get_next_link()).query)[self.cursor_query_param][0]  # pyright: ignore[reportArgumentType]
            cache.set(f"ack:{plugin.pk}:{next_cursor}", [result.pk for result in page], timeout=60*60*24)
        return page

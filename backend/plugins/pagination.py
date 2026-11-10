from rest_framework.pagination import CursorPagination


class UUIDCursorPagination(CursorPagination):
    ordering = "-id"
    cursor_query_description = "From `next`/`previous`."

    def get_paginated_response_schema(self, schema):
        schema = super().get_paginated_response_schema(schema)
        for link in ("next", "previous"):
            schema["properties"][link].pop("example", None)
        return schema

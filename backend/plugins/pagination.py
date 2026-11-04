from rest_framework.pagination import CursorPagination


class UUIDCursorPagination(CursorPagination):
    ordering = "-id"
    cursor_query_description = "Opaque cursor taken from a previous page's `next` or `previous` link."

    def get_paginated_response_schema(self, schema):
        schema = super().get_paginated_response_schema(schema)
        for link in ("next", "previous"):
            schema["properties"][link].pop("example", None)
            schema["properties"][link]["description"] = f"URL of the {link} page, or null."
        return schema

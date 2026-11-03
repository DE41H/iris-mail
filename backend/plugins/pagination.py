from rest_framework.pagination import CursorPagination


class UUIDCursorPagination(CursorPagination):
    ordering = "-id"

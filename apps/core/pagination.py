from rest_framework.pagination import CursorPagination


class CursorPage(CursorPagination):
    """DRF's own CursorPagination defaults `ordering` to "-created", which
    does not exist on any model here — every model uses TimeStampedModel's
    `created_at`. That default silently 500s the moment anything actually
    triggers pagination (rest_framework.pagination.CursorPagination direct
    as DEFAULT_PAGINATION_CLASS was never exercised until the first
    ModelViewSet was added)."""

    ordering = "-created_at"
    page_size = 50

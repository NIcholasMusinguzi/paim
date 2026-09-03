from django.db.models import ProtectedError
from rest_framework import status, viewsets
from rest_framework.response import Response


class ProtectedDestroyMixin:
    """Turns a PROTECT-FK IntegrityError into a clean 409 instead of a 500
    — e.g. deleting a district that still has subcounties under it."""

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "This record is still referenced by other data and cannot be deleted."},
                status=status.HTTP_409_CONFLICT,
            )


class AdminModelViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    """Base for the admin configuration API. Unpaginated: these are small
    reference tables (districts, crops, seasons, ...) and an editable admin
    table wants the whole list, not a cursor slice."""

    pagination_class = None

"""Permission classes shared by several apps."""
from django.conf import settings
from rest_framework.permissions import BasePermission


class StaffOrDebug(BasePermission):
    """Open in development, staff only in production (API schema and docs)."""

    def has_permission(self, request, view):
        if settings.DEBUG:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff)

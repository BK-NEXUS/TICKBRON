"""Bir neshe app ortaq paydalanatuǵın ruxsat klasları."""
from django.conf import settings
from rest_framework.permissions import BasePermission


class StaffOrDebug(BasePermission):
    """Development te ashıq, production ta tek staff (API schema hám hújjetler)."""

    def has_permission(self, request, view):
        if settings.DEBUG:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff)

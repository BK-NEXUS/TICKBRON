"""
Celery tasks for bookings.
"""
from celery import shared_task

from bookings.models import Booking


@shared_task
def expire_pending_bookings():
    """
    Cancel pending bookings whose payment window has passed and release their inventory.

    Scheduled by CELERY_BEAT_SCHEDULE. Raises if any booking could not be
    expired, so the failure is visible in Celery monitoring; the other
    bookings are still processed first.
    """
    return Booking.process_expired_bookings(raise_on_error=True)

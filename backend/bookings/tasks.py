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


@shared_task
def complete_finished_stays():
    """
    Confirmed stays whose check-out date has passed become completed (R12).

    Scheduled at 00:05 Asia/Tashkent (CELERY_BEAT_SCHEDULE). Raises after the run if
    any booking could not be completed, so the failure shows in Celery monitoring.
    """
    from bookings.completion import CompletionError, complete_finished_stays as run

    result = run(trigger='beat')
    if result['failed']:
        raise CompletionError(f"{result['failed']} finished stay(s) could not be completed")
    return result


@shared_task
def cancel_unarrived_bookings():
    """
    Cancel confirmed bookings whose guest has not arrived ARRIVAL_GRACE_HOURS after the arrival time they gave.

    Scheduled every 10 minutes (CELERY_BEAT_SCHEDULE). Raises after the run if any booking could not be
    cancelled, so the failure shows in Celery monitoring; the others are still processed first.
    """
    from bookings.arrival import ArrivalCancellationError, cancel_unarrived_bookings as run

    result = run()
    if result['failed']:
        raise ArrivalCancellationError(f"{result['failed']} unarrived booking(s) could not be cancelled")
    return result


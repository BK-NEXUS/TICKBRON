"""
Celery tasks for bookings.
"""
from celery import shared_task

from bookings.models import Booking
from bookings.notices import send_notice


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



# ignore_result: nobody reads the answer, and the result store is not touched (with Redis down that cost 20 s a call)
@shared_task(ignore_result=True)
def send_booking_notice(booking_id, kind):
    """Mail one booking notice. The booking was saved before this runs, so a slow mail server shows nothing."""
    booking = Booking.objects.select_related('guest', 'property__owner').filter(pk=booking_id).first()
    if booking is not None:
        send_notice(booking, kind)

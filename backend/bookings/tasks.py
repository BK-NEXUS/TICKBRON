"""
Bronlar ushın Celery task lar.
"""
from celery import shared_task

from bookings.models import Booking
from bookings.notices import send_notice


@shared_task
def expire_pending_bookings():
    """
    Tólem oynası ótken kútip turǵan bronlardı biykar etiw hám inventory dı bosatıw.

    CELERY_BEAT_SCHEDULE boyınsha rejelestirilgen. Qanday da bron múddeti ótken dep belgilenbese
    kóteredi, sol sebepli qátelik Celery monitoring inde kórinedi; basqa
    bronlar aldın islenedi.
    """
    return Booking.process_expired_bookings(raise_on_error=True)


@shared_task
def complete_finished_stays():
    """
    Shıǵıw sanası ótken tastıyıqlanǵan turıwlar completed boladı (R12).

    Asia/Tashkent 00:05 te rejelestirilgen (CELERY_BEAT_SCHEDULE). Qanday da bron juwmaqlanbasa,
    isleniwden keyin kóteredi, sol sebepli qátelik Celery monitoring inde kórinedi.
    """
    from bookings.completion import CompletionError, complete_finished_stays as run

    result = run(trigger='beat')
    if result['failed']:
        raise CompletionError(f"{result['failed']} finished stay(s) could not be completed")
    return result


@shared_task
def cancel_unarrived_bookings():
    """
    Mehmanı bergen keliw waqtınan keyin ARRIVAL_GRACE_HOURS saat ótkenshe kelmegen tastıyıqlanǵan bronlardı biykar etiw.

    Hár 10 minutta rejelestirilgen (CELERY_BEAT_SCHEDULE). Qanday da bron biykar etilmese, isleniwden keyin
    kóteredi, sol sebepli qátelik Celery monitoring inde kórinedi; basqaları aldın islenedi.
    """
    from bookings.arrival import ArrivalCancellationError, cancel_unarrived_bookings as run

    result = run()
    if result['failed']:
        raise ArrivalCancellationError(f"{result['failed']} unarrived booking(s) could not be cancelled")
    return result


# ignore_result: juwaptı hesh kim oqımaydı, hám natiyje saqlaw orınına tiyilmeydi (Redis óship qalsa bul hár shaqırıwǵa 20 s
# ketti)
@shared_task(ignore_result=True)
def send_booking_notice(booking_id, kind):
    """Bir bron xabarlandırıwın e-mail ge jiberiw. Bron bul isleniwden aldın saqlanǵan, sol sebepli sekin e-mail server hesh
    nárse kórsetpeydi."""
    booking = Booking.objects.select_related('guest', 'property__owner').filter(pk=booking_id).first()
    if booking is not None:
        send_notice(booking, kind)

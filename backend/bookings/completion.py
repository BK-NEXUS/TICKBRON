"""
Pitken turıwlardı avtomat juwmaqlaw (R12).

Shıǵıw sanası is sanasınan (common.dates.business_today, Asia/Tashkent) burın bolǵan
tastıyıqlanǵan bron `completed` boladı. Tańlaw "check_out < today" boyınsha, "== yesterday" emes, sol sebepli
ótkizip jiberilgen isleniw ózi túzeledi. Kútip turǵan no-show esabatı bar bronlar ótkizip jiberiledi (aldın staff
sheshedi; esabat biykar etilse yamasa qaytarıp alınsa, keyingi isleniw onı juwmaqlaydı). Hár bron
óz transaction ında Booking.complete_booking() arqalı ótedi (qatar qulıpı, state
machine, PaymentAuditLog), sol sebepli bir qátelik basqalardı biykar etpeydi. Basqa hesh nárse
tiyilmeydi: pending, cancelled, completed hám no_show qatarlar hesh qashan tańlanbaydı.

Celery beat jazbası `complete-finished-stays` (00:05 Asia/Tashkent) hám
`python manage.py complete_finished_stays [--dry-run]` tárepinen isletiledi.
"""
import logging

from django.utils import timezone

from bookings.models import AutoCompletionRun, Booking
from common.dates import business_today

logger = logging.getLogger(__name__)


class CompletionError(Exception):
    """Task tárepinen, ayırım bronlar juwmaqlanbaǵan isleniwden keyin kóteriledi."""


def finished_stays(today=None):
    """Shıǵıw sanası ótip ketken tastıyıqlanǵan bronlar (eń eski shıǵıw birinshi)."""
    today = today or business_today()
    return (Booking.objects.filter(status='confirmed', check_out__lt=today)
            .exclude(no_show_reports__status='pending').order_by('check_out', 'pk'))


def complete_finished_stays(dry_run=False, trigger='command'):
    """Hár pitken turıwdı juwmaqlaw. {'eligible', 'changed', 'failed'} qaytaradı; haqıyqıy isleniwlerdi jazadı."""
    started_at = timezone.now()
    ids = list(finished_stays().values_list('pk', flat=True))
    result = {'eligible': len(ids), 'changed': 0, 'failed': 0}
    if dry_run:
        return result
    for booking in Booking.objects.filter(pk__in=ids).order_by('check_out', 'pk'):
        try:
            booking.complete_booking()
            result['changed'] += 1
        except Exception:
            # Dizim jasalǵannan keyin basqa soraw tárepinen biykar etilgen, juwmaqlanǵan yamasa xabarlanǵan,
            # yamasa database qátesi: tek id menen log qa jazıladı, qalǵanları isleye beredi
            if Booking.objects.filter(pk=booking.pk).exclude(status='confirmed').exists():
                continue
            logger.exception('Auto-completion failed for booking %s', booking.pk)
            result['failed'] += 1
    AutoCompletionRun.objects.create(
        trigger=trigger, started_at=started_at, finished_at=timezone.now(),
        changed=result['changed'], failed=result['failed'],
    )
    return result

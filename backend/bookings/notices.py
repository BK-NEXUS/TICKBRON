"""
Mehmanǵa hám mehmanxana iyesine bron haqqında xabarlaw: saytıń dizimindegi bir qatar hám e-mail.
Mehmanǵa tolıq tastıyıqlaw baradı; iyege e-mail bir qatar hám mehmann maǵlıwmatın óz ishine almaydı.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string

from accounts import notify
from bookings.confirmation_mail import confirmation_body

logger = logging.getLogger(__name__)

SUBJECT = 'TICKBRON: bron / бронь / booking'

# kind -> kimge e-mail barıwı hám uz / ru / en degi tekst ({code} bron reference i)
MAILS = {
    # Mehmannıń e-mail ı tolıq tastıyıqlaw (bookings/confirmation_mail.py), sol sebepli bul jerde óz teksti joq
    'guest_confirmed': {'to': 'guest', 'path': '/bookings'},
    'owner_new': {
        'to': 'owner', 'path': '/partner',
        'uz': "Mehmonxonangizga yangi bron: {code}.",
        'ru': "Новая бронь в вашем отеле: {code}.",
        'en': "New booking at your hotel: {code}.",
    },
    'owner_cancelled': {
        'to': 'owner', 'path': '/partner',
        'uz': "Mehmon {code} raqamli bronni bekor qildi, xona yana bo'sh.",
        'ru': "Гость отменил бронь {code}, номер снова свободен.",
        'en': "The guest cancelled booking {code}; the room is free again.",
    },
}


def mail_for(booking, kind):
    """Bir xabarlandırıwdıń (subject, body, recipient) i, yamasa adamǵa e-mail jiberip bolmasa None."""
    spec = MAILS[kind]
    user = booking.guest if spec['to'] == 'guest' else booking.property.owner
    if not user.is_active or not user.email:
        return None
    link = f'{settings.FRONTEND_URL}{spec["path"]}'
    if kind == 'guest_confirmed':
        return f'{SUBJECT} {booking.confirmation_code}', confirmation_body(booking, link), user.email
    texts = {language: spec[language].format(code=booking.confirmation_code) for language in ('uz', 'ru', 'en')}
    return SUBJECT, render_to_string('bookings/notice.txt', {**texts, 'link': link}), user.email


def send_notice(booking, kind):
    notice = mail_for(booking, kind)
    if notice:
        subject, body, recipient = notice
        send_mail(subject, body, None, [recipient])


def _params(booking):
    return {
        'booking_id': booking.id, 'booking_reference': booking.confirmation_code,
        'check_in': booking.check_in, 'check_out': booking.check_out,
    }


# Broker óship qalsa da bron birden juwap beriwi kerek: bir tez urınıw, ádettegi qayta urınıwlardı kútpew
FAST_FAIL = {'max_retries': 1, 'interval_start': 0, 'interval_step': 0.2, 'interval_max': 0.2}


def _queue(booking, kinds):
    """E-mail lerdi worker ge beriw; buzılǵan náwbet saqlanıp bolǵan bronnıń sátsiz bolıwına yamasa sekinlewine sebep bolmawı
    kerek."""
    from bookings.tasks import send_booking_notice
    from config.celery import app

    for kind in kinds:
        try:
            with app.connection_for_write(transport_options=FAST_FAIL) as connection:
                send_booking_notice.apply_async(args=(booking.pk, kind), retry=False, connection=connection)
        except Exception:
            logger.exception('Could not queue the %s notice of booking %s', kind, booking.pk)


def tell_booked(booking):
    try:
        notify(booking.guest, 'booking_confirmed', _params(booking), booking=booking)
        notify(booking.property.owner, 'new_booking', _params(booking), booking=booking)
    except Exception:
        logger.exception('Could not store the notices of booking %s', booking.pk)
    transaction.on_commit(lambda: _queue(booking, ('guest_confirmed', 'owner_new')))


def tell_cancelled_by_guest(booking):
    try:
        notify(booking.property.owner, 'booking_cancelled_by_guest', _params(booking), booking=booking)
    except Exception:
        logger.exception('Could not store the cancel notice of booking %s', booking.pk)
    transaction.on_commit(lambda: _queue(booking, ('owner_cancelled',)))

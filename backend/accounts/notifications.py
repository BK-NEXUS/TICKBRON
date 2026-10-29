"""
R12 1d: in-app notifications with a machine-readable code.

`notify(user, code, params, booking=None)` stores the code, the params and an English
fallback title/message. The frontend renders its own uz/ru/en text from `code` + `params`.

`params` hold ids, amounts, currencies, percents and dates only, never personal data
(names, emails, phones, free text): every key must be known and every value must pass the
validator of its key, otherwise `NotificationParamsError` is raised and nothing is stored.
"""
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from .models import Notification


class NotificationParamsError(ValueError):
    pass


def _id(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise NotificationParamsError('must be a positive integer id')
    return value


_REFERENCE = re.compile(r'^[A-Z0-9-]{4,20}$')


def _reference(value):
    if not isinstance(value, str) or not _REFERENCE.match(value):
        raise NotificationParamsError('must be a booking reference code')
    return value


_AMOUNT = re.compile(r'^\d{1,15}(\.\d{1,2})?$')


def _amount(value):
    if isinstance(value, bool) or not isinstance(value, (int, Decimal, str)):
        raise NotificationParamsError('must be an amount')
    text = str(value)
    if not _AMOUNT.match(text):
        raise NotificationParamsError('must be a non-negative amount')
    try:
        Decimal(text)
    except InvalidOperation:
        raise NotificationParamsError('must be an amount')
    return text


def _currency(value):
    if not isinstance(value, str) or not re.match(r'^[A-Z]{3}$', value):
        raise NotificationParamsError('must be an ISO currency code')
    return value


def _percent(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
        raise NotificationParamsError('must be an integer 0-100')
    return value


def _date(value):
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            pass
    raise NotificationParamsError('must be an ISO date')


# The only keys a notification may carry. Anything else (email, phone, name, comment ...) is refused.
PARAM_VALIDATORS = {
    'booking_id': _id,
    'report_id': _id,
    'refund_id': _id,
    'review_id': _id,
    'property_id': _id,
    'fee_id': _id,
    'booking_reference': _reference,
    'amount': _amount,
    'currency': _currency,
    'percent': _percent,
    'check_in': _date,
    'check_out': _date,
    'due_date': _date,
}

# code -> notification type, required params and the English fallback text (str.format on params).
NOTIFICATION_CODES = {
    'no_show_report_approved': {
        'type': 'booking',
        'params': ('report_id', 'booking_id', 'booking_reference'),
        'title': 'No-show report approved',
        'message': 'Your no-show report for booking {booking_reference} was approved.',
    },
    'no_show_report_rejected': {
        'type': 'booking',
        'params': ('report_id', 'booking_id', 'booking_reference'),
        'title': 'No-show report rejected',
        'message': 'Your no-show report for booking {booking_reference} was rejected.',
    },
    'no_show_marked': {
        'type': 'booking',
        'params': ('booking_id', 'booking_reference', 'amount', 'currency', 'percent'),
        'title': 'Booking {booking_reference} marked as a no-show',
        'message': (
            'Your booking {booking_reference} was marked as a no-show; '
            '{amount} {currency} ({percent}%) will be refunded.'
        ),
    },
    'no_show_marked_no_refund': {
        'type': 'booking',
        'params': ('booking_id', 'booking_reference'),
        'title': 'Booking {booking_reference} marked as a no-show',
        'message': 'Your booking {booking_reference} was marked as a no-show by the hotel.',
    },
    'booking_not_arrived': {
        'type': 'booking',
        'params': ('booking_id', 'booking_reference'),
        'title': 'Booking {booking_reference} cancelled',
        'message': 'You did not arrive in time, so booking {booking_reference} was cancelled and the room was released.',
    },
    'guest_not_arrived': {
        'type': 'booking',
        'params': ('booking_id', 'booking_reference'),
        'title': 'Booking {booking_reference} cancelled: guest did not arrive',
        'message': 'The guest of booking {booking_reference} did not arrive in time; the booking was cancelled and the room is free again.',
    },
    'booking_confirmed': {
        'type': 'booking',
        'params': ('booking_id', 'booking_reference', 'check_in', 'check_out'),
        'title': 'Booking {booking_reference} confirmed',
        'message': 'Your booking {booking_reference} is confirmed for {check_in} - {check_out}.',
    },
    'new_booking': {
        'type': 'booking',
        'params': ('booking_id', 'booking_reference', 'check_in', 'check_out'),
        'title': 'New booking {booking_reference}',
        'message': 'A guest booked {check_in} - {check_out} (booking {booking_reference}).',
    },
    'booking_cancelled_by_guest': {
        'type': 'booking',
        'params': ('booking_id', 'booking_reference', 'check_in', 'check_out'),
        'title': 'Booking {booking_reference} cancelled by the guest',
        'message': 'The guest cancelled booking {booking_reference} ({check_in} - {check_out}); the room is free again.',
    },
    'review_approved': {
        'type': 'review',
        'params': ('review_id', 'property_id'),
        'title': 'Your review is published',
        'message': 'Your review was approved and everyone can read it now.',
    },
    'review_rejected': {
        'type': 'review',
        'params': ('review_id', 'property_id'),
        'title': 'Your review was not approved',
        'message': 'Your review was not approved, so it is not shown to others.',
    },
    'new_review': {
        'type': 'review',
        'params': ('review_id', 'property_id'),
        'title': 'New guest review',
        'message': 'A guest review of your hotel was approved and is now public. You can answer it.',
    },
    'review_reply': {
        'type': 'review',
        'params': ('review_id', 'property_id'),
        'title': 'The hotel answered your review',
        'message': 'The hotel wrote an answer to your review.',
    },
    'fee_due': {
        'type': 'payment',
        'params': ('fee_id', 'property_id', 'amount', 'currency', 'due_date'),
        'title': 'Monthly fee is due',
        'message': 'The monthly fee of {amount} {currency} for your hotel is due on {due_date}.',
    },
    'fee_overdue': {
        'type': 'payment',
        'params': ('fee_id', 'property_id', 'amount', 'currency', 'due_date'),
        'title': 'Monthly fee is overdue',
        'message': 'The monthly fee of {amount} {currency} for your hotel, due on {due_date}, is not paid yet.',
    },
    'fee_last_warning': {
        'type': 'payment',
        'params': ('fee_id', 'property_id', 'amount', 'currency', 'due_date'),
        'title': 'Last reminder: monthly fee',
        'message': (
            'The monthly fee of {amount} {currency} for your hotel, due on {due_date}, is still not paid. '
            'Please pay it soon, otherwise the hotel may be removed from the site.'
        ),
    },
    'fee_paid': {
        'type': 'payment',
        'params': ('fee_id', 'property_id', 'amount', 'currency', 'due_date'),
        'title': 'Monthly fee received',
        'message': 'Thank you, the monthly fee of {amount} {currency} due on {due_date} is marked as paid.',
    },
    'refund_succeeded': {
        'type': 'payment',
        'params': ('refund_id', 'booking_id', 'booking_reference', 'amount', 'currency'),
        'title': 'Refund sent',
        'message': 'A refund of {amount} {currency} for booking {booking_reference} was sent.',
    },
}


def clean_params(code, params):
    spec = NOTIFICATION_CODES[code]
    params = dict(params or {})
    unknown = set(params) - set(PARAM_VALIDATORS)
    if unknown:
        raise NotificationParamsError(f'unknown notification params: {sorted(unknown)}')
    missing = set(spec['params']) - set(params)
    if missing:
        raise NotificationParamsError(f'missing notification params: {sorted(missing)}')
    cleaned = {}
    for key, value in params.items():
        try:
            cleaned[key] = PARAM_VALIDATORS[key](value)
        except NotificationParamsError as exc:
            raise NotificationParamsError(f'{key} {exc}') from None
    return cleaned


def notify(user, code, params, booking=None):
    """Create one in-app notification for `user` with `code` + `params` and an English fallback."""
    if code not in NOTIFICATION_CODES:
        raise ValueError(f'unknown notification code: {code}')
    spec = NOTIFICATION_CODES[code]
    cleaned = clean_params(code, params)
    return Notification.objects.create(
        user=user,
        notification_type=spec['type'],
        code=code,
        params=cleaned,
        title=spec['title'].format(**cleaned)[:200],
        message=spec['message'].format(**cleaned),
        booking=booking,
    )

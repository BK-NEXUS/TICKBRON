"""
The rules of the monthly hotel fee (plan .ai/PLAN_SUBSCRIPTION.md). Views and the daily task only call this module.

A hotel is free for FREE_PERIOD after it first becomes active. From the first 1st-of-the-month after that, a fee
is created on the 1st of every month. The owner is reminded on day 0, 3 and 5 after the due date. Nothing happens
to the hotel in PR 1: the Telegram question and hiding come in the next step of the plan.
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from accounts import notify
from common.dates import business_today
from properties.models import Property
from subscriptions.models import FeeSettings, HotelFeeAccount, MonthlyFee

logger = logging.getLogger(__name__)

FREE_PERIOD = timedelta(days=30)
GRACE_DAYS = 5
REMINDER_DAYS = (0, 3, 5)
REMINDER_CODES = ('fee_due', 'fee_overdue', 'fee_last_warning')
CURRENCY = 'UZS'


class FeeStateError(Exception):
    """The fee is not in the state the action needs (already paid, not paid)."""


def ensure_account(property, today=None):
    """The hotel's fee account; the free period starts the first time this is called for the hotel."""
    today = today or business_today()
    return HotelFeeAccount.objects.get_or_create(property=property, defaults={'free_until': today + FREE_PERIOD})[0]


def ensure_accounts(today):
    """Hotels that were already active before the feature existed start their free period now."""
    missing = Property.objects.filter(status='active', is_deleted=False, fee_account__isnull=True)
    return sum(1 for hotel in missing if HotelFeeAccount.objects.get_or_create(
        property=hotel, defaults={'free_until': today + FREE_PERIOD})[1])


def create_due_fees(today):
    """This month's fee for every active hotel whose free period ended before the 1st; nothing twice."""
    amount = FeeSettings.load().monthly_amount
    if not amount:
        return 0
    month = today.replace(day=1)
    accounts = (HotelFeeAccount.objects
                .filter(property__status='active', property__is_deleted=False, free_until__lt=month)
                .exclude(property__monthly_fees__month=month)
                .select_related('property'))
    return sum(1 for account in accounts if MonthlyFee.objects.get_or_create(
        property=account.property, month=month, defaults={'amount': amount})[1])


def days_late(fee, today):
    return (today - fee.month).days


def phase(fee, today):
    """paid, due (inside the waiting time) or late (the waiting time is over)."""
    if fee.status == MonthlyFee.STATUS_PAID:
        return 'paid'
    return 'late' if days_late(fee, today) > GRACE_DAYS else 'due'


def _notice_params(fee):
    return {'fee_id': fee.id, 'property_id': fee.property_id, 'amount': fee.amount, 'currency': CURRENCY,
            'due_date': fee.month}


def _tell_owner(fee, code):
    """A notice never blocks the money action or the daily run; the caller learns whether it was stored."""
    try:
        notify(fee.property.owner, code, _notice_params(fee))
    except Exception:
        logger.exception('Fee notice %s for fee %s was not stored', code, fee.pk)
        return False
    return True


def send_reminders(today):
    """The latest reminder the fee has reached (day 0, 3 or 5), once; a missed day does not send the old ones."""
    sent = 0
    fees = (MonthlyFee.objects.filter(status=MonthlyFee.STATUS_DUE, reminder_stage__lt=len(REMINDER_CODES))
            .select_related('property__owner'))
    for fee in fees:
        stage = sum(1 for day in REMINDER_DAYS if days_late(fee, today) >= day)
        if stage > fee.reminder_stage and _tell_owner(fee, REMINDER_CODES[stage - 1]):
            fee.reminder_stage = stage
            fee.save(update_fields=['reminder_stage', 'updated_at'])
            sent += 1
    return sent


def run_daily(today=None):
    today = today or business_today()
    return {'accounts': ensure_accounts(today), 'fees': create_due_fees(today), 'notices': send_reminders(today)}


def confirm_paid(fee, actor, via=MonthlyFee.VIA_PANEL, note=''):
    with transaction.atomic():
        fee = MonthlyFee.objects.select_for_update().select_related('property__owner').get(pk=fee.pk)
        if fee.status == MonthlyFee.STATUS_PAID:
            raise FeeStateError(_('This fee is already marked as paid.'))
        fee.status = MonthlyFee.STATUS_PAID
        fee.paid_at = timezone.now()
        fee.confirmed_by = actor
        fee.confirmed_via = via
        fee.note = note
        fee.save()
    _tell_owner(fee, 'fee_paid')
    return fee


def undo_paid(fee):
    with transaction.atomic():
        fee = MonthlyFee.objects.select_for_update().get(pk=fee.pk)
        if fee.status != MonthlyFee.STATUS_PAID:
            raise FeeStateError(_('This fee is not marked as paid.'))
        fee.status = MonthlyFee.STATUS_DUE
        fee.paid_at = None
        fee.confirmed_by = None
        fee.confirmed_via = ''
        fee.note = ''
        fee.save()
    return fee


def set_monthly_amount(amount):
    settings = FeeSettings.load()
    settings.monthly_amount = amount
    settings.save(update_fields=['monthly_amount'])
    return settings

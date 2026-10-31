"""
The commission the site takes from hotel owners: one place for the rules.

- Counted bookings (confirmed or completed, see bookings.metrics.COUNTED_STATUSES) of the owner's hotels, by the
  month of check-in, each currency apart. Nothing is converted.
- The owner's percent of a month is the latest CommissionRate not after it; no rate, no commission.
- commission = the month's gross x percent, rounded to cents (once per month and currency).
- A month is confirmed as paid only after it has ended; the amounts are copied into the CommissionPayment.
- Year totals are shown only for an account that is at least a year old.
"""
import re
from collections import defaultdict
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import IntegrityError, transaction
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils.translation import gettext_lazy as _

from bookings.metrics import counted_q
from bookings.models import Booking
from common.dates import business_today
from partner.models import CommissionPayment, CommissionRate

CENT = Decimal('0.01')
YEAR_DAYS = 365
MONTH_FORMAT = re.compile(r'^(20\d\d)-(0[1-9]|1[0-2])$')


class CommissionError(Exception):
    """A request the rules refuse; `code` picks the HTTP answer in the view."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def month_start(day):
    return day.replace(day=1)


def next_month(first):
    return date(first.year + (first.month == 12), first.month % 12 + 1, 1)


def month_label(first):
    return f'{first.year}-{first.month:02d}'


def parse_month(text):
    """The first day of 'YYYY-MM', or None for anything else."""
    found = MONTH_FORMAT.match(text or '')
    return date(int(found.group(1)), int(found.group(2)), 1) if found else None


def _money(amount):
    return f'{amount:.2f}'


def _amounts(by_currency):
    return [{'currency': currency, 'amount': _money(amount)} for currency, amount in sorted(by_currency.items())]


def _commission_of(gross, percent):
    return {currency: (amount * percent / 100).quantize(CENT, ROUND_HALF_UP) for currency, amount in gross.items()}


def _percent_for(rates, month):
    chosen = None
    for rate in rates:
        if rate.effective_from <= month:
            chosen = rate.percent
    return chosen


def _booking_rows(owner):
    rows = (Booking.objects.filter(counted_q(), property__owner=owner)
            .annotate(month=TruncMonth('check_in')).values('month', 'currency')
            .annotate(bookings=Count('id'), amount=Sum('total_price')))
    months = defaultdict(lambda: {'bookings': 0, 'gross': {}})
    for row in rows:
        entry = months[row['month']]
        entry['bookings'] += row['bookings']
        entry['gross'][row['currency']] = row['amount']
    return months


def _paid_of(payment):
    return {'by': payment.confirmed_by_name, 'role': payment.confirmed_by_role,
            'at': payment.confirmed_at.isoformat(), 'amounts': payment.amounts}


def _year_rows(months):
    years = {}
    for row in months:
        entry = years.setdefault(row['first'].year, {'bookings': 0, 'gross': defaultdict(Decimal), 'commission': None})
        entry['bookings'] += row['bookings']
        for currency, amount in row['gross'].items():
            entry['gross'][currency] += amount
        if row['commission_by_currency'] is not None:
            entry['commission'] = entry['commission'] or defaultdict(Decimal)
            for currency, amount in row['commission_by_currency'].items():
                entry['commission'][currency] += amount
    return [{'year': year, 'bookings': entry['bookings'], 'gross': _amounts(entry['gross']),
             'commission': None if entry['commission'] is None else _amounts(entry['commission'])}
            for year, entry in sorted(years.items(), reverse=True)]


def _month_rows(owner, today):
    rates = list(CommissionRate.objects.filter(owner=owner).order_by('effective_from'))
    booked = _booking_rows(owner)
    paid = {payment.month: payment for payment in CommissionPayment.objects.filter(owner=owner)}
    wanted = set(booked) | {month_start(today)}
    rows = []
    for first in sorted(wanted, reverse=True):
        gross = booked[first]['gross'] if first in booked else {}
        percent = _percent_for(rates, first)
        rows.append({'first': first, 'bookings': booked[first]['bookings'] if first in booked else 0, 'gross': gross,
                     'percent': percent,
                     'commission_by_currency': None if percent is None else _commission_of(gross, percent),
                     'payment': paid.get(first)})
    return rows, rates


def _public_month(row):
    commission = row['commission_by_currency']
    return {'month': month_label(row['first']), 'bookings': row['bookings'], 'gross': _amounts(row['gross']),
            'percent': None if row['percent'] is None else _money(row['percent']),
            'commission': None if commission is None else _amounts(commission),
            'paid': _paid_of(row['payment']) if row['payment'] else None}


def statement(owner):
    """Everything the owner's commission screen and the staff detail screen show."""
    today = business_today()
    rows, rates = _month_rows(owner, today)
    old_enough = owner.date_joined.date() <= today - timedelta(days=YEAR_DAYS)
    return {
        'percent': _money(rates[-1].percent) if rates else None,
        'percent_since': rates[-1].effective_from.isoformat() if rates else None,
        'months': [_public_month(row) for row in rows],
        'years': _year_rows(rows) if old_enough else None,
    }


def list_summary(owner):
    """One row of the staff list: the percent, this month, and the commission of ended months not yet confirmed."""
    today = business_today()
    rows, rates = _month_rows(owner, today)
    this_month = next(row for row in rows if row['first'] == month_start(today))
    unpaid = defaultdict(Decimal)
    for row in rows:
        if row['first'] < month_start(today) and row['payment'] is None and row['commission_by_currency']:
            for currency, amount in row['commission_by_currency'].items():
                unpaid[currency] += amount
    commission = this_month['commission_by_currency']
    return {
        'percent': _money(rates[-1].percent) if rates else None,
        'this_month': {'month': month_label(this_month['first']), 'bookings': this_month['bookings'],
                       'gross': _amounts(this_month['gross']),
                       'commission': None if commission is None else _amounts(commission)},
        'unpaid': _amounts({currency: amount for currency, amount in unpaid.items() if amount}),
    }


def set_percent(owner, percent, actor):
    """The percent from this month on (setting it again in the same month replaces it)."""
    CommissionRate.objects.update_or_create(
        owner=owner, effective_from=month_start(business_today()), defaults={'percent': percent, 'set_by': actor})


def _confirmer_name(actor):
    return actor.get_full_name() or actor.email.split('@')[0]


def confirm_paid(owner, first, actor):
    """Record that the owner paid the commission of the month `first`; refuse what cannot be paid."""
    today = business_today()
    if first >= month_start(today):
        raise CommissionError('not_ended', _('This month has not ended yet.'))
    rows, _rates = _month_rows(owner, today)
    row = next((item for item in rows if item['first'] == first), None)
    if row is None or row['commission_by_currency'] is None:
        raise CommissionError('no_percent', _('There is no commission percent for this month.'))
    if not any(row['commission_by_currency'].values()):
        raise CommissionError('nothing', _('There is nothing to pay for this month.'))
    try:
        with transaction.atomic():
            CommissionPayment.objects.create(
                owner=owner, month=first, confirmed_by=actor, confirmed_by_name=_confirmer_name(actor),
                confirmed_by_role='super_admin' if actor.is_superuser else 'staff',
                amounts=_amounts(row['commission_by_currency']))
    except IntegrityError:
        raise CommissionError('already', _('This month is already confirmed as paid.'))


def undo_paid(owner, first):
    deleted = CommissionPayment.objects.filter(owner=owner, month=first).delete()[0]
    if not deleted:
        raise CommissionError('missing', _('This month was not confirmed as paid.'))

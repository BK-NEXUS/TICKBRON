"""
Sayt mehmanxana iyelerinen alatuǵın komissiya: qaǵıydalar ushın bir orın.

- Iyeniń mehmanxanalarınıń esaplanatuǵın bronları (confirmed yamasa completed, qarań bookings.metrics.COUNTED_STATUSES),
  kiriw ayı boyınsha, hár valyuta bólek. Hesh nárse konvertaciyalanbaydı.
- Iyeniń ay ushın procenti sol aydan keyin bolmaǵan eń sońǵı CommissionRate; kurs joq bolsa, komissiya joq.
- komissiya = aydıń jalpı summası x procent, sentke shekem jumalaqlanǵan (hár ay hám valyuta ushın bir márte).
- Ay tek pitkennen keyin ǵana tólengen dep tastıyıqlanadı; summalar CommissionPayment ke kóshiriledi.
- Jıllıq jıynaqlar tek eń keminde bir jıllıq akkaunt ushın kórsetiledi.
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
    """Qaǵıydalar biykar etetuǵın soraw; `code` view de HTTP juwabın tańlaydı."""

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
    """'YYYY-MM' diń birinshi kúni, yamasa basqa hár nárse ushın None."""
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


def _booking_rows(owner_ids):
    """Barlıq iyeler ushın bir query de {iye id si: {ay: {'bookings', 'gross'}}}."""
    rows = (Booking.objects.filter(counted_q(), property__owner_id__in=owner_ids)
            .annotate(month=TruncMonth('check_in')).values('property__owner_id', 'month', 'currency')
            .annotate(bookings=Count('id'), amount=Sum('total_price')))
    by_owner = defaultdict(lambda: defaultdict(lambda: {'bookings': 0, 'gross': {}}))
    for row in rows:
        entry = by_owner[row['property__owner_id']][row['month']]
        entry['bookings'] += row['bookings']
        entry['gross'][row['currency']] = row['amount']
    return by_owner


def _load(owner_ids):
    """Barlıq iyeler procentleri, bronlanǵan sanları hám tólengen ayları: sanı qansha bolsa da úsh query."""
    rates = defaultdict(list)
    for rate in CommissionRate.objects.filter(owner_id__in=owner_ids).order_by('effective_from'):
        rates[rate.owner_id].append(rate)
    paid = defaultdict(dict)
    for payment in CommissionPayment.objects.filter(owner_id__in=owner_ids):
        paid[payment.owner_id][payment.month] = payment
    return rates, _booking_rows(owner_ids), paid


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


def _month_rows(owner_id, loaded, today):
    all_rates, all_booked, all_paid = loaded
    rates, booked, paid = all_rates[owner_id], all_booked[owner_id], all_paid[owner_id]
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
    """Iyeniń komissiya ekranı hám staff tolıq maǵlıwmat ekranı kórsetetuǵın hámme nárse."""
    today = business_today()
    rows, rates = _month_rows(owner.id, _load([owner.id]), today)
    old_enough = owner.date_joined.date() <= today - timedelta(days=YEAR_DAYS)
    return {
        'percent': _money(rates[-1].percent) if rates else None,
        'percent_since': rates[-1].effective_from.isoformat() if rates else None,
        'months': [_public_month(row) for row in rows],
        'years': _year_rows(rows) if old_enough else None,
    }


def list_summaries(owners):
    """Bir bettegi iyeler ushın {iye id si: staff dizimniń qatarı}, database ge jámi úsh ret soralıp."""
    loaded = _load([owner.id for owner in owners])
    today = business_today()
    return {owner.id: _summary(*_month_rows(owner.id, loaded, today), today) for owner in owners}


def list_summary(owner):
    """Bir iyeniń qatarı (`list_summaries` degi birdey sanlar)."""
    return list_summaries([owner])[owner.id]


def _summary(rows, rates, today):
    """Staff dizimniń bir qatarı: procent, usı ay hám tastıyıqlanbaǵan pitken aylardıń komissiyası."""
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
    """Usı aydan baslap procent (sol ayda qayta belgilew onı almastıradı)."""
    CommissionRate.objects.update_or_create(
        owner=owner, effective_from=month_start(business_today()), defaults={'percent': percent, 'set_by': actor})


def _confirmer_name(actor):
    return actor.get_full_name() or actor.email.split('@')[0]


def confirm_paid(owner, first, actor):
    """Iye `first` ayınıń komissiyasın tólegenin jazıw; tólenip bolmaytuǵın nárseden bas tartıw."""
    today = business_today()
    if first >= month_start(today):
        raise CommissionError('not_ended', _('This month has not ended yet.'))
    rows, _rates = _month_rows(owner.id, _load([owner.id]), today)
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

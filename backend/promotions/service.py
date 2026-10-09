"""All promotion rules in one place: dates, overlap, who is shown now, order, lifecycle, audit."""
import hashlib
import re
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from admin_panel.models import AdminAccessLog
from common.dates import business_today
from promotions.models import Promotion
from properties.models import Property

MAX_DAYS = 365
MAX_START_AHEAD_DAYS = 730
MAX_PRIORITY = 100
MAX_NOTE = 500
MAX_PRICE = Decimal('999999999999.99')
EDITABLE_STATUSES = (Promotion.STATUS_SCHEDULED, Promotion.STATUS_ACTIVE, Promotion.STATUS_PAUSED)
CURRENCY_RE = re.compile(r'^[A-Z]{3}$')
UPDATABLE_FIELDS = frozenset({
    'start_date', 'end_date', 'priority', 'country_ref', 'region_ref', 'city_ref',
    'price_amount', 'price_currency', 'note'})


class PromotionError(Exception):
    def __init__(self, code, message=''):
        super().__init__(message or code)
        self.code = code
        self.message = message or code


def _audit(actor, action, promotion):
    details = {'promotion_id': promotion.pk, 'property_id': promotion.property_id,
               'start_date': promotion.start_date.isoformat(), 'end_date': promotion.end_date.isoformat()}
    if action in ('promotion_create', 'promotion_mark_paid') and promotion.price_amount is not None:
        details['amount'] = str(promotion.price_amount)
        details['currency'] = promotion.price_currency
    AdminAccessLog.record(actor, action, details=details)


def _check_dates(start, end, today, *, check_start_in_past):
    if end < start:
        raise PromotionError('bad_dates', 'End date is before the start date')
    if check_start_in_past and start < today:
        raise PromotionError('start_in_past', 'Start date is in the past')
    if (start - today).days > MAX_START_AHEAD_DAYS:
        raise PromotionError('start_too_far', f'Start date is more than {MAX_START_AHEAD_DAYS} days ahead')
    if (end - start).days + 1 > MAX_DAYS:
        raise PromotionError('too_long', f'A promotion lasts at most {MAX_DAYS} days')


def _check_values(priority, price_amount, price_currency, note):
    if not 0 <= priority <= MAX_PRIORITY:
        raise PromotionError('bad_priority', f'Priority must be between 0 and {MAX_PRIORITY}')
    if price_amount is not None and not Decimal('0') <= price_amount <= MAX_PRICE:
        raise PromotionError('bad_price', 'Price is out of range')
    if not CURRENCY_RE.match(price_currency):
        raise PromotionError('bad_currency', 'Currency must be a three letter code')
    if len(note) > MAX_NOTE:
        raise PromotionError('note_too_long', f'Note is longer than {MAX_NOTE} characters')


def _check_scope(country, region, city):
    if city and region and city.region_id != region.pk:
        raise PromotionError('bad_scope', 'City is not in the chosen region')
    if region and country and region.country_id != country.pk:
        raise PromotionError('bad_scope', 'Region is not in the chosen country')
    if city and country and city.region.country_id != country.pk:
        raise PromotionError('bad_scope', 'City is not in the chosen country')


def _check_overlap(property_id, start, end, exclude_pk=None):
    clash = Promotion.objects.filter(
        property_id=property_id, is_deleted=False, status__in=Promotion.HOLDING_STATUSES,
        start_date__lte=end, end_date__gte=start)
    if exclude_pk:
        clash = clash.exclude(pk=exclude_pk)
    if clash.exists():
        raise PromotionError('overlap', 'This hotel already has a promotion in these dates')


def _lock_property(property_id):
    # Serialises concurrent changes for one hotel so the overlap check cannot be raced
    Property.objects.select_for_update().only('id').get(pk=property_id)


def _lock_promotion(promotion):
    # Re-reads the row under a lock so two admins acting at once see each other's result
    promotion.refresh_from_db(from_queryset=Promotion.objects.select_for_update())


def create_promotion(*, actor, property, start_date, end_date, priority=0, country_ref=None, region_ref=None,
                     city_ref=None, price_amount=None, price_currency='UZS', note=''):
    price_currency = (price_currency or '').strip().upper()
    note = (note or '').strip()
    _check_dates(start_date, end_date, business_today(), check_start_in_past=True)
    _check_values(priority, price_amount, price_currency, note)
    _check_scope(country_ref, region_ref, city_ref)
    with transaction.atomic():
        _lock_property(property.pk)
        _check_overlap(property.pk, start_date, end_date)
        promotion = Promotion.objects.create(
            property=property, start_date=start_date, end_date=end_date, priority=priority,
            country_ref=country_ref, region_ref=region_ref, city_ref=city_ref, price_amount=price_amount,
            price_currency=price_currency, note=note, created_by=actor)
        _audit(actor, 'promotion_create', promotion)
    return promotion


def update_promotion(promotion, *, actor, **changes):
    unknown = set(changes) - UPDATABLE_FIELDS
    if unknown:
        raise PromotionError('bad_field', f'Cannot change: {sorted(unknown)}')
    with transaction.atomic():
        _lock_property(promotion.property_id)
        _lock_promotion(promotion)
        if promotion.status not in EDITABLE_STATUSES:
            raise PromotionError('bad_status', 'This promotion can no longer be changed')
        if 'price_currency' in changes:
            changes['price_currency'] = (changes['price_currency'] or '').strip().upper()
        if 'note' in changes:
            changes['note'] = (changes['note'] or '').strip()
        old_start = promotion.start_date
        for name, value in changes.items():
            setattr(promotion, name, value)
        _check_dates(promotion.start_date, promotion.end_date, business_today(),
                     check_start_in_past=promotion.start_date != old_start)
        _check_values(promotion.priority, promotion.price_amount, promotion.price_currency, promotion.note)
        _check_scope(promotion.country_ref, promotion.region_ref, promotion.city_ref)
        _check_overlap(promotion.property_id, promotion.start_date, promotion.end_date, exclude_pk=promotion.pk)
        promotion.save()
        _audit(actor, 'promotion_update', promotion)
    return promotion


def _transition(promotion, actor, action, allowed, new_status, **extra):
    with transaction.atomic():
        _lock_promotion(promotion)
        if promotion.status not in allowed:
            raise PromotionError('bad_status', f'Cannot do this to a {promotion.status} promotion')
        promotion.status = new_status
        for name, value in extra.items():
            setattr(promotion, name, value)
        promotion.save()
        _audit(actor, action, promotion)
    return promotion


def pause(promotion, *, actor):
    return _transition(promotion, actor, 'promotion_pause',
                       (Promotion.STATUS_SCHEDULED, Promotion.STATUS_ACTIVE), Promotion.STATUS_PAUSED)


def resume(promotion, *, actor):
    started_and_paid = promotion.paid_at is not None and promotion.start_date <= business_today()
    return _transition(promotion, actor, 'promotion_resume', (Promotion.STATUS_PAUSED,),
                       Promotion.STATUS_ACTIVE if started_and_paid else Promotion.STATUS_SCHEDULED)


def cancel(promotion, *, actor, reason):
    reason = (reason or '').strip()
    if not reason:
        raise PromotionError('reason_required', 'A reason is required')
    if len(reason) > 255:
        raise PromotionError('reason_too_long', 'Reason is longer than 255 characters')
    return _transition(promotion, actor, 'promotion_cancel', EDITABLE_STATUSES,
                       Promotion.STATUS_CANCELLED, cancelled_reason=reason)


def mark_paid(promotion, *, actor):
    with transaction.atomic():
        _lock_promotion(promotion)
        if promotion.paid_at is not None:
            raise PromotionError('already_paid', 'Payment is already recorded')
        if promotion.status not in EDITABLE_STATUSES:
            raise PromotionError('bad_status', 'This promotion can no longer be changed')
        promotion.paid_at = timezone.now()
        promotion.paid_marked_by = actor
        promotion.save()
        _audit(actor, 'promotion_mark_paid', promotion)
    return promotion


def _scope_matches_property():
    """A promotion with a place only shows for hotels in that place; an empty level matches all."""
    return (
        (Q(country_ref__isnull=True) | Q(country_ref_id=F('property__country_ref_id')))
        & (Q(region_ref__isnull=True) | Q(region_ref_id=F('property__region_ref_id')))
        & (Q(city_ref__isnull=True) | Q(city_ref_id=F('property__city_ref_id')))
    )


def shown_now(today: date | None = None):
    """Promotions that may be served right now. Computed from the facts, never from `status` alone."""
    today = today or business_today()
    return Promotion.objects.filter(
        is_deleted=False, status__in=(Promotion.STATUS_SCHEDULED, Promotion.STATUS_ACTIVE),
        paid_at__isnull=False, start_date__lte=today, end_date__gte=today,
        property__is_active=True, property__is_deleted=False, property__status='active',
    ).filter(_scope_matches_property()).select_related('property')


def _rotation_key(promotion, today):
    digest = hashlib.sha256(f'{today.isoformat()}:{promotion.pk}'.encode()).hexdigest()
    return -promotion.priority, digest


def ordered(queryset, today: date | None = None, limit: int | None = None):
    """Highest priority first; equal priorities rotate fairly, a different order each business day."""
    today = today or business_today()
    items = sorted(queryset, key=lambda promotion: _rotation_key(promotion, today))
    return items[:limit] if limit is not None else items


def blocked_reason(promotion):
    """Why a promotion cannot be seen by guests even though it is paid and running, or None."""
    prop = promotion.property
    if prop.is_deleted or not prop.is_active or prop.status != 'active':
        return 'hotel_not_active'
    for ref in ('country_ref', 'region_ref', 'city_ref'):
        wanted = getattr(promotion, f'{ref}_id')
        if wanted is not None and wanted != getattr(prop, f'{ref}_id'):
            return 'outside_scope'
    return None


def is_shown_now(promotion, today: date | None = None):
    today = today or business_today()
    return (
        not promotion.is_deleted
        and promotion.status in (Promotion.STATUS_SCHEDULED, Promotion.STATUS_ACTIVE)
        and promotion.paid_at is not None
        and promotion.start_date <= today <= promotion.end_date
        and blocked_reason(promotion) is None
    )


def tidy_statuses(today: date | None = None):
    """
    Nightly: expired promotions become `ended`, paid ones whose period has begun become `active`.
    Only keeps `status` readable in the admin lists; serving is computed by `shown_now()`.
    """
    today = today or business_today()
    live = Promotion.objects.filter(is_deleted=False)
    ended = live.filter(status__in=Promotion.HOLDING_STATUSES, end_date__lt=today).update(
        status=Promotion.STATUS_ENDED)
    activated = live.filter(
        status=Promotion.STATUS_SCHEDULED, paid_at__isnull=False, start_date__lte=today, end_date__gte=today,
    ).update(status=Promotion.STATUS_ACTIVE)
    return {'ended': ended, 'activated': activated}

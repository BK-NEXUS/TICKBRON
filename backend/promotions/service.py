"""
Barlıq reklama biznes qaǵıydaları usı jerde; view ler tek usı funkciyalardı shaqıradı.

Reklama nede: bir tólengen dáwir, onıń dawamında bir mehmanxana banner karuselinde kóriniwi múmkin.
  1. create_promotion / update_promotion  sanalardı, bahanı, ornın hám "bir mehmanxana ushın kesilispew" ti tekseredi
  2. pause / resume / cancel / mark_paid   jaǵdaydı ózgertedi (hár ózgeris audit logına jazıladı)
  3. shown_now / ordered                   mehmanlar qaysı reklamanı hám qanday tártipte kóretuǵının sheshedi
  4. tidy_statuses                         `status` baǵanasın túnde tazalaw (Celery task paydalanadı)
"""
import hashlib
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Exists, F, Max, OuterRef, Q
from django.utils import timezone

from admin_panel.models import AdminAccessLog
from common.dates import business_today
from common.image_rules import AD_BANNER, image_upload_error
from common.images import shrink_upload
from geography.models import Region
from promotions.models import AdRenewal, Promotion, PromotionPhoto
from properties.models import Property

MAX_DAYS = 365                # eń uzın bir reklama
MAX_START_AHEAD_DAYS = 730    # 2062 jıl sıyaqlı qátelerdi tutadı; haqıyqıy bron hesh qashan onshama aldınan rejelestirilmeydi
MAX_PRIORITY = 100            # 0 = ádettegi, joqarı = karuselde erterek kórsetiledi
MAX_NOTE = 500                # ishki jazba uzınlıǵı (admin bul jerge baylanıs maǵlıwmatın qoymawı kerek)
MAX_PRICE = Decimal('999999999999.99')  # DecimalField(14, 2) baǵanasına sıyadı
MAX_PHOTOS = 10               # bir reklamadaǵı súwretler (banner mehmanxananıń óz súwretlerinen sonshasın kórsetedi)
# Reklama ele ózgertilip bolatuǵın jaǵdaylar; pitken hám biykar etilgenler tariyx
EDITABLE_STATUSES = (Promotion.STATUS_SCHEDULED, Promotion.STATUS_ACTIVE, Promotion.STATUS_PAUSED)
CURRENCY_RE = re.compile(r'^[A-Z]{3}$')
# update_promotion qabıllaytuǵın jalǵız maydanlar: mehmanxana, status hám tólem onıń arqalı hesh qashan ózgertilmeydi
UPDATABLE_FIELDS = frozenset({
    'start_date', 'end_date', 'priority', 'country_ref', 'region_ref',
    'price_amount', 'price_currency', 'note'})


class PromotionError(Exception):
    """Qaǵıyda buzıldı. `code` API qaytaratuǵın turaqlı mashina oqıytuǵın at; `message` adamlar ushın."""

    def __init__(self, code, message=''):
        super().__init__(message or code)
        self.code = code
        self.message = message or code


def _audit(actor, action, promotion):
    """Bir audit qatarın jazıw. Tek id ler, sanalar hám kelisilgen summa: at, jazba yamasa baylanıs maǵlıwmatı joq."""
    details = {'promotion_id': promotion.pk, 'property_id': promotion.property_id,
               'start_date': promotion.start_date.isoformat(), 'end_date': promotion.end_date.isoformat()}
    if action in ('promotion_create', 'promotion_mark_paid') and promotion.price_amount is not None:
        details['amount'] = str(promotion.price_amount)
        details['currency'] = promotion.price_currency
    AdminAccessLog.record(actor, action, details=details)


def _check_dates(start, end, today, *, check_start_in_past):
    """Islep atırǵan reklamanıń eski baslanıw sanasın saqlaytuǵın ózgertiwde `check_start_in_past` óshiriledi."""
    if end < start:
        raise PromotionError('bad_dates', 'End date is before the start date')
    if check_start_in_past and start < today:
        raise PromotionError('start_in_past', 'Start date is in the past')
    if (start - today).days > MAX_START_AHEAD_DAYS:
        raise PromotionError('start_too_far', f'Start date is more than {MAX_START_AHEAD_DAYS} days ahead')
    if (end - start).days + 1 > MAX_DAYS:
        raise PromotionError('too_long', f'A promotion lasts at most {MAX_DAYS} days')


def _check_values(priority, price_amount, price_currency, note):
    """Admin jazatuǵın ápiwayı mánisler ushın aralıq tekseriwleri."""
    if not 0 <= priority <= MAX_PRIORITY:
        raise PromotionError('bad_priority', f'Priority must be between 0 and {MAX_PRIORITY}')
    if price_amount is not None and not Decimal('0') <= price_amount <= MAX_PRICE:
        raise PromotionError('bad_price', 'Price is out of range')
    if not CURRENCY_RE.match(price_currency):
        raise PromotionError('bad_currency', 'Currency must be a three letter code')
    if len(note) > MAX_NOTE:
        raise PromotionError('note_too_long', f'Note is longer than {MAX_NOTE} characters')


def _check_scope(country, region):
    """Orın shegi izbe-iz bolıwı kerek: tańlanǵan region tańlanǵan mámleket ishinde."""
    if region and country and region.country_id != country.pk:
        raise PromotionError('bad_scope', 'Region is not in the chosen country')


def _check_overlap(property_id, start, end, exclude_pk=None):
    """Bir mehmanxana birdey kúnde eki reklama ustap tura almaydı. Biykar etilgen hám pitken dáwirler esaplanbaydı."""
    clash = Promotion.objects.filter(
        property_id=property_id, is_deleted=False, status__in=Promotion.HOLDING_STATUSES,
        start_date__lte=end, end_date__gte=start)
    if exclude_pk:
        clash = clash.exclude(pk=exclude_pk)
    if clash.exists():
        raise PromotionError('overlap', 'This hotel already has a promotion in these dates')


def _lock_property(property_id):
    # Bir mehmanxana ushın birdey waqıttaǵı ózgerislerdi izbe-iz etedi, sol sebepli kesilisiw tekseriwin jarıstırıp ótip
    # bolmaydı
    Property.objects.select_for_update().only('id').get(pk=property_id)


def _lock_promotion(promotion):
    # Qatardı qulıp astında qayta oqıydı, sonda birdey waqıtta háreket etken eki admin bir-birinıń nátiyjesin kóredi
    promotion.refresh_from_db(from_queryset=Promotion.objects.select_for_update())


def create_promotion(*, actor, property, start_date, end_date, priority=0, country_ref=None, region_ref=None,
                     price_amount=None, price_currency='UZS', note=''):
    """
    Tólenbegen reklama jaratıw (status `scheduled`). Ol tek mark_paid() ten keyin hám tek óz sanaları ishinde kórsetiledi.
    Tekseriw waqtında mehmanxana qatarı qulıplanadı, sol sebepli birdey waqıtta jaratatuǵın eki admin ekewi de ótip ala
    almaydı.
    """
    price_currency = (price_currency or '').strip().upper()
    note = (note or '').strip()
    _check_dates(start_date, end_date, business_today(), check_start_in_past=True)
    _check_values(priority, price_amount, price_currency, note)
    _check_scope(country_ref, region_ref)
    with transaction.atomic():
        _lock_property(property.pk)
        _check_overlap(property.pk, start_date, end_date)
        promotion = Promotion.objects.create(
            property=property, start_date=start_date, end_date=end_date, priority=priority,
            country_ref=country_ref, region_ref=region_ref, price_amount=price_amount,
            price_currency=price_currency, note=note, created_by=actor)
        _audit(actor, 'promotion_create', promotion)
    return promotion


def update_promotion(promotion, *, actor, **changes):
    """Sanalardı, dáwirdi, ornın, bahanı yamasa jazbanı ózgertiw. Sanalar jaratıw menen birdey tekseriwlerden ótedi (óz
    dáwiri itibarǵa alınbaydı)."""
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
        _check_scope(promotion.country_ref, promotion.region_ref)
        _check_overlap(promotion.property_id, promotion.start_date, promotion.end_date, exclude_pk=promotion.pk)
        promotion.save()
        _audit(actor, 'promotion_update', promotion)
    return promotion


def _transition(promotion, actor, action, allowed, new_status, **extra):
    """Házirgi status `allowed` ishinde bolsa `new_status` ke ótiw; jarıstan qorǵaw ushın qulıp astında qayta oqıw."""
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
    """Reklamanı házirshe jasırıw; sanaları rezervlengen qaladı."""
    return _transition(promotion, actor, 'promotion_pause',
                       (Promotion.STATUS_SCHEDULED, Promotion.STATUS_ACTIVE), Promotion.STATUS_PAUSED)


def resume(promotion, *, actor):
    """Qayta kórsetiw: aldınan tólengen hám baslanǵan bolsa `active`, bolmasa `scheduled` ke qaytıw."""
    started_and_paid = promotion.paid_at is not None and promotion.start_date <= business_today()
    return _transition(promotion, actor, 'promotion_resume', (Promotion.STATUS_PAUSED,),
                       Promotion.STATUS_ACTIVE if started_and_paid else Promotion.STATUS_SCHEDULED)


def cancel(promotion, *, actor, reason):
    """Mángige toqtatıw hám sanalardı bosatıw. Esap ushın sebep májbúriy; qaytarıwlar sırtta sheshiledi."""
    reason = (reason or '').strip()
    if not reason:
        raise PromotionError('reason_required', 'A reason is required')
    if len(reason) > 255:
        raise PromotionError('reason_too_long', 'Reason is longer than 255 characters')
    return _transition(promotion, actor, 'promotion_cancel', EDITABLE_STATUSES,
                       Promotion.STATUS_CANCELLED, cancelled_reason=reason)


def mark_paid(promotion, *, actor):
    """Klienttiń tólegenin jazıw (platforma sırtında). Reklama tek endi kórsetile aladı."""
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
    """Orını bar reklama tek sol orındaǵı mehmanxanalarǵa kórsetiledi; bos dáreje hámmesine sáykes keledi."""
    return (
        (Q(country_ref__isnull=True) | Q(country_ref_id=F('property__country_ref_id')))
        & (Q(region_ref__isnull=True) | Q(region_ref_id=F('property__region_ref_id')))
    )


def shown_now(today: date | None = None):
    """Házir kórsetile alatuǵın reklamalar. Faktlardan esaplanadı, hesh qashan tek `status` tan emes."""
    today = today or business_today()
    awaiting_answer = Exists(AdRenewal.objects.filter(
        promotion=OuterRef('pk'), status=AdRenewal.STATUS_PENDING, deadline__gte=today))
    return Promotion.objects.filter(
        is_deleted=False, status__in=(Promotion.STATUS_SCHEDULED, Promotion.STATUS_ACTIVE),
        paid_at__isnull=False, start_date__lte=today,
        property__is_active=True, property__is_deleted=False, property__status='active',
    ).filter(Q(end_date__gte=today) | awaiting_answer).filter(_scope_matches_property()).select_related('property')


def _rotation_key(promotion, today):
    """Tártiplew kilti: joqarı priority birinshi; (sana, id) hash i birdey priority lerdi kúnine bir ret aralastıradı."""
    digest = hashlib.sha256(f'{today.isoformat()}:{promotion.pk}'.encode()).hexdigest()
    return -promotion.priority, digest


def ordered(queryset, today: date | None = None, limit: int | None = None):
    """Eń joqarı priority birinshi; birdey priority ler ádil aylanadı, hár is kúni ayrıqsha tártip."""
    today = today or business_today()
    items = sorted(queryset, key=lambda promotion: _rotation_key(promotion, today))
    return items[:limit] if limit is not None else items


def blocked_reason(promotion):
    """Reklama tólengen hám islep tursa da mehmanlar nege kóre almaydı, yamasa None."""
    prop = promotion.property
    if prop.is_deleted or not prop.is_active or prop.status != 'active':
        return 'hotel_not_active'
    for ref in ('country_ref', 'region_ref'):
        wanted = getattr(promotion, f'{ref}_id')
        if wanted is not None and wanted != getattr(prop, f'{ref}_id'):
            return 'outside_scope'
    return None


def _awaiting_answer(promotion, today):
    """Reklama pitti, biraq "mehmanxana keyingi ay ushın tóledi me?" sorawı ele ashıq (renewals.py)."""
    return any(renewal.status == AdRenewal.STATUS_PENDING and renewal.deadline >= today
               for renewal in promotion.renewals.all())


def is_shown_now(promotion, today: date | None = None):
    """Bir júklengen reklama ushın shown_now() tiń Python juwıbı (admin ekranları). Ekewin birge jańalap turıń."""
    today = today or business_today()
    return (
        not promotion.is_deleted
        and promotion.status in (Promotion.STATUS_SCHEDULED, Promotion.STATUS_ACTIVE)
        and promotion.paid_at is not None
        and promotion.start_date <= today
        and (today <= promotion.end_date or _awaiting_answer(promotion, today))
        and blocked_reason(promotion) is None
    )


def tidy_statuses(today: date | None = None):
    """
    Túnde: múddeti ótken reklamalar `ended` boladı (jańalaw sorawı ashıq waqıtta emes), dáwiri baslanǵan tólengenleri
    `active` boladı.
    Tek admin dizimlerinde `status` dı oqılatuǵın etip saqlaydı; kórsetiw shown_now() menen esaplanadı.
    """
    today = today or business_today()
    live = Promotion.objects.filter(is_deleted=False)
    ended = live.filter(status__in=Promotion.HOLDING_STATUSES, end_date__lt=today).exclude(
        renewals__status=AdRenewal.STATUS_PENDING).update(status=Promotion.STATUS_ENDED)
    activated = live.filter(
        status=Promotion.STATUS_SCHEDULED, paid_at__isnull=False, start_date__lte=today, end_date__gte=today,
    ).update(status=Promotion.STATUS_ACTIVE)
    return {'ended': ended, 'activated': activated}


def _audit_photo(actor, action, promotion, photo):
    """Tek id ler, hár audit qatarı sıyaqlı."""
    AdminAccessLog.record(actor, action, details={
        'promotion_id': promotion.pk, 'property_id': promotion.property_id, 'object_id': photo.pk})


def add_photo(*, actor, promotion, photo):
    """Ele ózgertilip bolatuǵın reklamaǵa bir súwret qoyıw: eń kóbi MAX_PHOTOS, haqıyqıy súwret, júklew tártibinde
    kórsetiledi."""
    error = image_upload_error(photo, AD_BANNER)
    if error:
        raise PromotionError('bad_image', error)
    with transaction.atomic():
        _lock_promotion(promotion)
        if promotion.status not in EDITABLE_STATUSES:
            raise PromotionError('bad_status', 'This promotion can no longer be changed')
        live = PromotionPhoto.objects.filter(promotion=promotion, is_deleted=False)
        if live.count() >= MAX_PHOTOS:
            raise PromotionError('too_many_photos', f'An ad can have at most {MAX_PHOTOS} photos')
        order = (live.aggregate(top=Max('display_order'))['top'] or 0) + 1
        row = PromotionPhoto.objects.create(
            promotion=promotion, photo=shrink_upload(photo, AD_BANNER.max_side), display_order=order)
        _audit_photo(actor, 'promotion_photo_add', promotion, row)
    return row


def remove_photo(*, actor, promotion, photo_id):
    """Reklamadan bir súwretti alıp taslaw (soft delete; fayl diskte qaladı)."""
    with transaction.atomic():
        row = PromotionPhoto.objects.select_for_update().filter(
            pk=photo_id, promotion=promotion, is_deleted=False).first()
        if row is None:
            raise PromotionError('not_found', 'Photo not found')
        row.soft_delete()
        _audit_photo(actor, 'promotion_photo_remove', promotion, row)


def regions_panel(today: date | None = None):
    """
    Hár aktiv region, onda házir neshe reklama islep atırǵanı (`running`, mehmanxanalar menen) hám neshewi ele islewi
    yamasa tólemdi kútiwi kerek (`waiting`). Eń kóp isleytuǵın reklamalı regionlar birinshi, sonda admin
    bos regionlardı da kóredi: reklamanı sol jerde ele satıw múmkin.
    """
    today = today or business_today()
    holding = Promotion.objects.filter(
        is_deleted=False, status__in=Promotion.HOLDING_STATUSES, end_date__gte=today,
        property__is_deleted=False, property__region_ref__isnull=False).select_related('property')
    running, waiting = defaultdict(list), defaultdict(int)
    for promotion in holding:
        region_id = promotion.property.region_ref_id
        if is_shown_now(promotion, today):
            running[region_id].append({'id': promotion.property_id, 'name': promotion.property.display_name()})
        else:
            waiting[region_id] += 1
    regions = Region.objects.filter(is_deleted=False, is_active=True, country__is_deleted=False).select_related('country')
    rows = [{
        'id': region.pk, 'country_code': region.country.code,
        'name_uz': region.name_uz, 'name_ru': region.name_ru, 'name_en': region.name_en,
        'running': len(running[region.pk]), 'waiting': waiting[region.pk], 'hotels': running[region.pk],
    } for region in regions]
    return sorted(rows, key=lambda row: (-row['running'], -row['waiting'], row['country_code'], row['name_en']))

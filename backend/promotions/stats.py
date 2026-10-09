"""Counting views and clicks: once per visitor per hour, no personal data kept."""
import hashlib
import logging

from django.conf import settings
from django.core.cache import cache
from django.db.models import F

from common.dates import business_today
from common.request import get_client_ip
from promotions.models import PromotionDailyStat

logger = logging.getLogger(__name__)

DEDUPE_SECONDS = 3600
IMPRESSION = 'impression'
CLICK = 'click'
_COLUMN = {IMPRESSION: 'impressions', CLICK: 'clicks'}


def _visitor_hash(request):
    # Salted with SECRET_KEY so the cache never holds a usable IP address
    raw = f'{settings.SECRET_KEY}:{get_client_ip(request) or ""}'
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _is_first_event(kind, promotion_id, visitor):
    try:
        return cache.add(f'promo:{kind}:{promotion_id}:{visitor}', 1, DEDUPE_SECONDS)
    except Exception:
        # Fail closed: a missed count is better than a wrong invoice
        logger.warning('Promotion counter skipped: cache unavailable')
        return False


def record(kind, promotion_ids, request):
    """Count `kind` for each promotion the visitor has not triggered it for in the last hour."""
    visitor = _visitor_hash(request)
    today = business_today()
    column = _COLUMN[kind]
    for promotion_id in promotion_ids:
        if not _is_first_event(kind, promotion_id, visitor):
            continue
        row, _ = PromotionDailyStat.objects.get_or_create(promotion_id=promotion_id, date=today)
        # One atomic UPDATE, never read-modify-write
        PromotionDailyStat.objects.filter(pk=row.pk).update(**{column: F(column) + 1})

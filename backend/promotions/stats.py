"""Kóriwlerdi hám bosıwlardı sanaw: hár kelwshi ushın saatına bir ret, jeke maǵlıwmat saqlanbaydı."""
import hashlib
import logging

from django.conf import settings
from django.core.cache import cache
from django.db.models import F

from common.dates import business_today
from common.request import get_client_ip, network_key
from promotions.models import PromotionDailyStat

logger = logging.getLogger(__name__)

DEDUPE_SECONDS = 3600
IMPRESSION = 'impression'
CLICK = 'click'
_COLUMN = {IMPRESSION: 'impressions', CLICK: 'clicks'}


def _visitor_hash(request):
    # SECRET_KEY penen duzlanǵan, sonda kesh hesh qashan paydalanıp bolatuǵın IP mánzildi saqlamaydı
    raw = f'{settings.SECRET_KEY}:{network_key(get_client_ip(request)) or ""}'
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _is_first_event(kind, promotion_id, visitor):
    try:
        return cache.add(f'promo:{kind}:{promotion_id}:{visitor}', 1, DEDUPE_SECONDS)
    except Exception:
        # Qáte bolǵanda jabıw: jiberilip qalǵan san qáte esap-fakturadan jaqsı
        logger.warning('Promotion counter skipped: cache unavailable')
        return False


def record(kind, promotion_ids, request):
    """Kelwshi sońǵı saatta iske túsirmegen hár reklama ushın `kind` di sanaw."""
    visitor = _visitor_hash(request)
    today = business_today()
    column = _COLUMN[kind]
    for promotion_id in promotion_ids:
        if not _is_first_event(kind, promotion_id, visitor):
            continue
        row, _ = PromotionDailyStat.objects.get_or_create(promotion_id=promotion_id, date=today)
        # Bir atomic UPDATE, hesh qashan oqıw-ózgertiw-jazıw emes
        PromotionDailyStat.objects.filter(pk=row.pk).update(**{column: F(column) + 1})

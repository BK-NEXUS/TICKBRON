"""The hotel owner's view of the ads of their own hotels: how they run, views and clicks, the open renewal question. Read only."""
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from common.dates import business_today
from partner.status import bad_request, own_properties
from partner.views import IsHotelOwner
from promotions import service
from promotions.models import AdRenewal, Promotion


def _click_rate(impressions, clicks):
    return f'{clicks / impressions * 100:.1f}' if impressions else None


def _open_question(promotion, today):
    """The renewal question still waiting for an answer, or None."""
    for renewal in promotion.renewals.all():
        if renewal.status == AdRenewal.STATUS_PENDING:
            return {'ends_on': renewal.ends_on.isoformat(), 'deadline': renewal.deadline.isoformat(),
                    'days_left': (renewal.deadline - today).days}
    return None


def _row(promotion, today):
    hotel = promotion.property
    return {
        'id': promotion.id, 'property': {'id': hotel.id, 'name': hotel.display_name()},
        'start_date': promotion.start_date.isoformat(), 'end_date': promotion.end_date.isoformat(),
        'status': promotion.status, 'paid': promotion.paid_at is not None,
        'is_shown_now': service.is_shown_now(promotion, today), 'blocked_reason': service.blocked_reason(promotion),
        'impressions': promotion.sum_impressions, 'clicks': promotion.sum_clicks,
        'click_rate': _click_rate(promotion.sum_impressions, promotion.sum_clicks),
        'renewal': _open_question(promotion, today),
    }


@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsHotelOwner])
def partner_promotions(request):
    """
    Ads of the owner's hotels, newest first. `?status=` (scheduled, active, paused, ended, cancelled) and
    `?property=<own hotel id>` narrow the list. The agreed price and the staff's note are not part of it.
    """
    own = own_properties(request.user)
    ads = (Promotion.objects.filter(property__in=own, is_deleted=False)
           .select_related('property').prefetch_related('property__translations', 'renewals')
           .annotate(sum_impressions=Coalesce(Sum('daily_stats__impressions'), 0),
                     sum_clicks=Coalesce(Sum('daily_stats__clicks'), 0))
           .order_by('-start_date', '-id'))
    wanted = request.query_params.get('status')
    if wanted:
        if wanted not in dict(Promotion.STATUS_CHOICES):
            return Response({'status': [_('Choose one of: scheduled, active, paused, ended, cancelled.')]},
                            status=status.HTTP_400_BAD_REQUEST)
        ads = ads.filter(status=wanted)
    hotel_id = (request.query_params.get('property') or '').strip()
    if hotel_id:
        if not hotel_id.isdigit():
            return bad_request('property', 'property must be a hotel id.')
        ads = ads.filter(property=get_object_or_404(own, pk=int(hotel_id)))
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(ads, request)
    today = business_today()
    return paginator.get_paginated_response([_row(promotion, today) for promotion in page])

"""The super admin's Renewals section: ads waiting for the answer "did the hotel pay for the next month?"."""
from django.utils.translation import gettext as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from admin_panel.views import IsSuperAdmin, IsSuperAdminOrStaff
from common.dates import business_today
from promotions import renewals
from promotions.models import AdRenewal
from promotions.renewals import RenewalError

STATUSES = (AdRenewal.STATUS_PENDING, AdRenewal.STATUS_RENEWED, AdRenewal.STATUS_DECLINED, AdRenewal.STATUS_EXPIRED)


def _row(renewal, today):
    promotion = renewal.promotion
    hotel = promotion.property
    owner = hotel.owner
    return {
        'id': renewal.id, 'promotion_id': promotion.id, 'property_id': hotel.id, 'hotel_name': hotel.display_name(),
        'city': hotel.city, 'address': hotel.address_line1,
        'latitude': str(hotel.latitude) if hotel.latitude is not None else None,
        'longitude': str(hotel.longitude) if hotel.longitude is not None else None,
        'owner_name': ' '.join(part for part in (owner.first_name, owner.last_name) if part),
        'owner_phone': owner.phone_number or '', 'owner_email': owner.email,
        'start_date': promotion.start_date.isoformat(), 'end_date': promotion.end_date.isoformat(),
        'price_amount': str(promotion.price_amount) if promotion.price_amount is not None else None,
        'price_currency': promotion.price_currency, 'ends_on': renewal.ends_on.isoformat(),
        'deadline': renewal.deadline.isoformat(), 'days_left': (renewal.deadline - today).days,
        'status': renewal.status, 'decided_via': renewal.decided_via, 'decided_at': renewal.decided_at,
    }


def _queryset():
    return AdRenewal.objects.filter(promotion__is_deleted=False).select_related(
        'promotion__property__owner').prefetch_related('promotion__property__translations')


@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def renewal_list(request):
    """Renewals by status (`?status=`, default pending), nearest deadline first; the others newest first."""
    wanted = request.query_params.get('status', AdRenewal.STATUS_PENDING)
    if wanted not in STATUSES:
        return Response({'error': _('Choose one of: pending, renewed, declined, expired.'), 'code': 'invalid_query'},
                        status=status.HTTP_400_BAD_REQUEST)
    ordering = ('deadline', 'id') if wanted == AdRenewal.STATUS_PENDING else ('-decided_at', '-id')
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(_queryset().filter(status=wanted).order_by(*ordering), request)
    today = business_today()
    return paginator.get_paginated_response([_row(renewal, today) for renewal in page])


def _answer(request, renewal_id, action):
    renewal = _queryset().filter(pk=renewal_id).first()
    if renewal is None:
        return Response({'error': _('Not found.'), 'code': 'not_found'}, status=status.HTTP_404_NOT_FOUND)
    try:
        renewal = action(renewal, actor=request.user)
    except RenewalError as error:
        return Response({'error': error.message, 'code': error.code}, status=status.HTTP_409_CONFLICT)
    return Response(_row(renewal, business_today()))


@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def renewal_confirm(request, renewal_id):
    return _answer(request, renewal_id, renewals.confirm)


@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def renewal_decline(request, renewal_id):
    return _answer(request, renewal_id, renewals.decline)

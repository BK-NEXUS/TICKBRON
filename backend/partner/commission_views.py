"""The commission screens: the owner's own statement, and the staff list, detail, percent and "paid" confirmation."""
from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from admin_panel.models import AdminAccessLog
from admin_panel.views import IsSuperAdmin, IsSuperAdminOrStaff
from common.request import object_body
from partner import commission
from partner.views import IsHotelOwner
from users.models import User

ERROR_STATUS = {'not_ended': 400, 'no_percent': 400, 'nothing': 400, 'already': 409, 'missing': 404}
PERCENT_STEP = Decimal('0.01')


class OwnerListPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def parse_percent(value):
    """A Decimal 0..100 with at most two decimals, or None for anything else (text, NaN, lists, too many digits)."""
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    try:
        percent = Decimal(str(value).strip())
    except InvalidOperation:
        return None
    if not percent.is_finite() or not Decimal(0) <= percent <= Decimal(100) or percent != percent.quantize(PERCENT_STEP):
        return None
    return percent.quantize(PERCENT_STEP)


def percent_error():
    return {'percent': [_('Enter a percent from 0 to 100 with at most two decimals.')]}


def hotel_owners():
    return User.objects.filter(is_deleted=False, role__name='hotel-owner')


def owner_of(owner_id):
    return get_object_or_404(hotel_owners(), pk=owner_id)


def month_or_404(text):
    first = commission.parse_month(text)
    if first is None:
        from django.http import Http404
        raise Http404
    return first


def refusal(error):
    return Response({'detail': str(error.message)}, status=ERROR_STATUS[error.code])


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsHotelOwner])
def partner_commission(request):
    """The signed-in owner's percent, months (newest first) and, for an account a year old, year totals."""
    return Response(commission.statement(request.user))


def owner_row(owner):
    return {'id': owner.id, 'name': owner.get_full_name() or owner.email, 'email': owner.email,
            'phone_number': owner.phone_number, **commission.list_summary(owner)}


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_commission_list(request):
    """Hotel owners with their percent, this month and unconfirmed commission. ?search= name, e-mail, phone or hotel name."""
    owners = hotel_owners().order_by('full_name', 'email')
    term = (request.query_params.get('search') or '').strip()[:100]
    if term:
        owners = owners.filter(
            Q(full_name__icontains=term) | Q(first_name__icontains=term) | Q(last_name__icontains=term)
            | Q(email__icontains=term) | Q(phone_number__icontains=term)
            | Q(properties__translations__name__icontains=term, properties__is_deleted=False)).distinct()
    paginator = OwnerListPagination()
    page = paginator.paginate_queryset(owners, request)
    return paginator.get_paginated_response([owner_row(owner) for owner in page])


@extend_schema(responses=OpenApiTypes.OBJECT, operation_id='v1_admin_panel_commission_detail')
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_commission_detail(request, owner_id):
    return Response(commission.statement(owner_of(owner_id)))


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['PUT'])
@permission_classes([IsSuperAdmin])
def admin_commission_rate(request, owner_id):
    """Set the owner's percent from this month on (super admin only). Body: percent."""
    owner = owner_of(owner_id)
    percent = parse_percent(object_body(request).get('percent'))
    if percent is None:
        return Response(percent_error(), status=status.HTTP_400_BAD_REQUEST)
    commission.set_percent(owner, percent, request.user)
    AdminAccessLog.record(request.user, 'commission_rate_set', target_user_id=owner.id, details={'percent': str(percent)})
    return Response(commission.statement(owner))


@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
@api_view(['POST', 'DELETE'])
@permission_classes([IsSuperAdminOrStaff])
def admin_commission_paid(request, owner_id, month):
    """POST: confirm that the owner paid this ended month; DELETE: take the confirmation back. Staff or super admin."""
    owner = owner_of(owner_id)
    first = month_or_404(month)
    try:
        if request.method == 'POST':
            commission.confirm_paid(owner, first, request.user)
            action = 'commission_paid'
        else:
            commission.undo_paid(owner, first)
            action = 'commission_unpaid'
    except commission.CommissionError as error:
        return refusal(error)
    AdminAccessLog.record(request.user, action, target_user_id=owner.id, details={'month': month})
    return Response(commission.statement(owner))

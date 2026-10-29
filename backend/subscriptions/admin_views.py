"""The super admin's Payments tab: a month of hotels with their fee state, mark a fee paid or undo it, the amount."""
import re
from datetime import date

from django.db.models import Q
from django.utils.translation import gettext as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from admin_panel.models import AdminAccessLog
from admin_panel.views import IsSuperAdmin, IsSuperAdminOrStaff
from common.dates import business_today
from common.validators import validate_free_text
from properties.models import Property
from subscriptions import services
from subscriptions.models import FeeSettings, MonthlyFee

MAX_AMOUNT = 2_000_000_000
NOTE_MAX_LENGTH = 200
STATUS_FILTERS = ('free', 'due', 'late', 'paid', 'not_billed')
# Late first, then the hotels still waiting to pay, then the rest
PHASE_ORDER = {'late': 0, 'due': 1, 'not_billed': 2, 'paid': 3, 'free': 4}
MONTH_FORMAT = re.compile(r'^(\d{4})-(0[1-9]|1[0-2])$')


class NoteSerializer(serializers.Serializer):
    note = serializers.CharField(max_length=NOTE_MAX_LENGTH, required=False, allow_blank=True, trim_whitespace=True,
                                 validators=[validate_free_text])


class AmountSerializer(serializers.Serializer):
    monthly_amount = serializers.IntegerField(min_value=0, max_value=MAX_AMOUNT)


def _owner_name(owner):
    return ' '.join(part for part in (owner.first_name, owner.last_name) if part)


def _row(hotel, fee, month, today, free_until):
    owner = hotel.owner
    if fee is not None:
        row_phase, late = services.phase(fee, today), services.days_late(fee, today)
    else:
        row_phase, late = ('free' if free_until and month <= free_until else 'not_billed'), None
    return {
        'property_id': hotel.id, 'fee_id': fee.id if fee else None, 'name': hotel.display_name(),
        'city': hotel.city, 'address': hotel.address_line1,
        'latitude': str(hotel.latitude) if hotel.latitude is not None else None,
        'longitude': str(hotel.longitude) if hotel.longitude is not None else None,
        'property_status': hotel.status, 'owner_name': _owner_name(owner), 'owner_phone': owner.phone_number or '',
        'owner_email': owner.email, 'month': month.strftime('%Y-%m'), 'amount': fee.amount if fee else None,
        'phase': row_phase, 'status': fee.status if fee else None,
        'due_date': fee.month.isoformat() if fee else None, 'days_late': late,
        'paid_at': fee.paid_at if fee else None, 'confirmed_via': fee.confirmed_via if fee else '',
        'note': fee.note if fee else '', 'free_until': free_until.isoformat() if free_until else None,
    }


def _rows_of_the_month(month, today):
    fees = {fee.property_id: fee for fee in MonthlyFee.objects.filter(month=month)}
    hotels = (Property.objects.filter(is_deleted=False).filter(Q(status='active') | Q(id__in=fees))
              .select_related('owner', 'fee_account').prefetch_related('translations'))
    rows = []
    for hotel in hotels:
        account = getattr(hotel, 'fee_account', None)
        rows.append(_row(hotel, fees.get(hotel.id), month, today, account.free_until if account else None))
    rows.sort(key=lambda row: (PHASE_ORDER[row['phase']], -(row['days_late'] or 0), row['name'].lower(), row['property_id']))
    return rows


def _summary(rows):
    counts = {name: sum(1 for row in rows if row['phase'] == name) for name in ('free', 'due', 'late', 'paid')}
    return {**counts,
            'collected': sum(row['amount'] for row in rows if row['phase'] == 'paid'),
            'outstanding': sum(row['amount'] for row in rows if row['phase'] in ('due', 'late'))}


def _month_of(request):
    """The first day of the `?month=YYYY-MM` month (default: this month), or None when it is malformed."""
    text = request.query_params.get('month')
    if text is None:
        return business_today().replace(day=1)
    match = MONTH_FORMAT.match(text)
    return date(int(match.group(1)), int(match.group(2)), 1) if match else None


@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def fees(request):
    """
    A month of hotels with their fee state. `?month=YYYY-MM` (default this month), `?status=` one of
    free, due, late, paid, not_billed, `?search=` a part of the hotel name or city. Paginated; the summary counts
    the whole month, not only the filtered rows.
    """
    month = _month_of(request)
    if month is None:
        return Response({'month': [_('Use the format YYYY-MM.')]}, status=status.HTTP_400_BAD_REQUEST)
    wanted = request.query_params.get('status')
    if wanted is not None and wanted not in STATUS_FILTERS:
        return Response({'status': [_('Choose one of: free, due, late, paid, not_billed.')]},
                        status=status.HTTP_400_BAD_REQUEST)
    rows = _rows_of_the_month(month, business_today())
    summary = _summary(rows)
    if wanted:
        rows = [row for row in rows if row['phase'] == wanted]
    search = request.query_params.get('search', '').strip().lower()
    if search:
        rows = [row for row in rows if search in row['name'].lower() or search in row['city'].lower()]
    paginator = PageNumberPagination()
    response = paginator.get_paginated_response(paginator.paginate_queryset(rows, request))
    response.data.update(summary=summary, month=month.strftime('%Y-%m'),
                         monthly_amount=FeeSettings.load().monthly_amount)
    return response


def _fee_action(request, fee_id, action, audit_action, **kwargs):
    fee = MonthlyFee.objects.select_related('property__owner').filter(pk=fee_id).first()
    if fee is None:
        return Response({'detail': _('Not found.')}, status=status.HTTP_404_NOT_FOUND)
    try:
        fee = action(fee, **kwargs)
    except services.FeeStateError as error:
        return Response({'error': str(error)}, status=status.HTTP_409_CONFLICT)
    AdminAccessLog.record(request.user, audit_action, details={'object_id': fee.id, 'property_id': fee.property_id})
    return Response(_row(fee.property, fee, fee.month, business_today(), None))


@extend_schema(request=NoteSerializer, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def fee_mark_paid(request, fee_id):
    serializer = NoteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return _fee_action(request, fee_id, services.confirm_paid, 'fee_mark_paid', actor=request.user,
                       note=serializer.validated_data.get('note', ''))


@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def fee_undo(request, fee_id):
    return _fee_action(request, fee_id, services.undo_paid, 'fee_undo_paid')


@extend_schema(request=AmountSerializer, responses=OpenApiTypes.OBJECT)
@api_view(['GET', 'PUT'])
@permission_classes([IsSuperAdmin])
def fee_settings(request):
    if request.method == 'PUT':
        serializer = AmountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data['monthly_amount']
        services.set_monthly_amount(amount)
        AdminAccessLog.record(request.user, 'fee_amount_update', details={'amount': amount})
    return Response({'monthly_amount': FeeSettings.load().monthly_amount, 'currency': services.CURRENCY})

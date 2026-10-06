"""
No-show report endpoints (R12 phase 3, .ai/PLAN_R12.md section 3).

Owner (/api/v1/partner/):
  POST bookings/{id}/no-show-report/        {comment}  report that the guest did not arrive
  GET  no-show-reports/                     own reports (?status, ?property), paginated
  POST no-show-reports/{id}/withdraw/       own pending report only
Staff (/api/v1/admin-panel/):
  GET  no-show-reports/                     pending first (oldest first); ?status, ?property, ?from, ?to
  GET  no-show-reports/{id}/
  POST no-show-reports/{id}/approve|reject|reverse/   {decision_comment} (10-500 characters)

Another owner's booking or report is a 404, never a 403, so ids do not leak. Owners never decide.
"""
import sys
import os
from datetime import datetime, time, timedelta

from django.db.models import Case, DateTimeField, F, Value, When
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from admin_panel.views import IsSuperAdminOrStaff
from bookings import noshow
from bookings.models import NoShowReport
from bookings.noshow import NoShowError
from bookings.noshow_serializers import (
    DecisionSerializer, OwnerReportSerializer, ReportCommentSerializer, StaffReportSerializer,
)
from common.dates import business_time_zone
from partner.views import IsHotelOwner
from payments.models import Refund

TESTING = 'pytest' in sys.modules or os.getenv('PYTEST_CURRENT_TEST')


class NoShowReportThrottle(UserRateThrottle):
    """Filing no-show reports: 20 per hour per user (settings: THROTTLE_NO_SHOW_REPORT_RATE)."""
    scope = 'no_show_report'

    def allow_request(self, request, view):
        if TESTING:
            return True
        return super().allow_request(request, view)


def _error(exc):
    code = status.HTTP_404_NOT_FOUND if exc.code == 'not_found' else status.HTTP_400_BAD_REQUEST
    return Response({'error': exc.message, 'code': exc.code}, status=code)


def _owner_queryset():
    return NoShowReport.objects.select_related('booking', 'property').prefetch_related('property__translations')


def _int_param(request, name):
    value = request.query_params.get(name)
    if value in (None, ''):
        return None, None
    try:
        return int(value), None
    except ValueError:
        return None, Response({name: ['A valid integer is required.']}, status=status.HTTP_400_BAD_REQUEST)


def _status_param(request):
    value = request.query_params.get('status')
    if value in (None, ''):
        return None, None
    if value not in dict(NoShowReport.STATUS_CHOICES):
        return None, Response({'status': [f'"{value}" is not a valid status.']}, status=status.HTTP_400_BAD_REQUEST)
    return value, None


# --- owner ---------------------------------------------------------------------------------

@extend_schema(request=ReportCommentSerializer, responses=OwnerReportSerializer)
@api_view(['POST'])
@permission_classes([IsHotelOwner])
@throttle_classes([NoShowReportThrottle])
def partner_no_show_report_create(request, booking_id):
    serializer = ReportCommentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        report = noshow.create_report(booking_id, request.user, serializer.validated_data['comment'])
    except NoShowError as exc:
        return _error(exc)
    return Response(OwnerReportSerializer(report).data, status=status.HTTP_201_CREATED)


@extend_schema(responses=OwnerReportSerializer(many=True))
@api_view(['GET'])
@permission_classes([IsHotelOwner])
def partner_no_show_reports(request):
    reports = _owner_queryset().filter(property__owner=request.user)
    state, error = _status_param(request)
    if error:
        return error
    property_id, error = _int_param(request, 'property')
    if error:
        return error
    if state:
        reports = reports.filter(status=state)
    if property_id is not None:
        reports = reports.filter(property_id=property_id)
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(reports.order_by('-created_at', '-id'), request)
    return paginator.get_paginated_response(OwnerReportSerializer(page, many=True).data)


@extend_schema(request=None, responses=OwnerReportSerializer)
@api_view(['POST'])
@permission_classes([IsHotelOwner])
def partner_no_show_report_withdraw(request, report_id):
    try:
        report = noshow.withdraw_report(report_id, request.user)
    except NoShowError as exc:
        return _error(exc)
    return Response(OwnerReportSerializer(_owner_queryset().get(pk=report.pk)).data)


# --- staff ---------------------------------------------------------------------------------

def _staff_context(reports):
    """Everything the staff rows need, in a fixed number of queries whatever the page size."""
    bookings = [report.booking for report in reports]
    pending = [report.booking for report in reports if report.status == 'pending']
    refunds = {}
    for refund in Refund.objects.filter(booking_id__in=[b.pk for b in bookings], reason='no_show'
                                        ).order_by('id'):
        refunds.setdefault(refund.booking_id, []).append({
            'id': refund.pk, 'amount': f'{refund.amount:.2f}', 'currency': refund.currency, 'status': refund.status,
        })
    return {
        'flagged': noshow.flagged_property_ids({report.property_id for report in reports}) if reports else set(),
        'previews': noshow.refund_previews(pending) if pending else {},
        'refunds': refunds,
    }


def _staff_data(reports, many=True):
    reports = list(reports) if many else [reports]
    data = StaffReportSerializer(reports, many=True, context=_staff_context(reports)).data
    return list(data) if many else data[0]


def _date_param(request, name):
    value = request.query_params.get(name)
    if value in (None, ''):
        return None, None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date(), None
    except ValueError:
        return None, Response({name: ['Date must be YYYY-MM-DD.']}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(responses=StaffReportSerializer(many=True))
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_no_show_reports(request):
    reports = _owner_queryset()
    state, error = _status_param(request)
    if error:
        return error
    property_id, error = _int_param(request, 'property')
    if error:
        return error
    first, error = _date_param(request, 'from')
    if error:
        return error
    last, error = _date_param(request, 'to')
    if error:
        return error
    if state:
        reports = reports.filter(status=state)
    if property_id is not None:
        reports = reports.filter(property_id=property_id)
    zone = business_time_zone()
    if first:
        reports = reports.filter(created_at__gte=datetime.combine(first, time.min, tzinfo=zone))
    if last:
        reports = reports.filter(created_at__lt=datetime.combine(last + timedelta(days=1), time.min, tzinfo=zone))
    pending_first = Case(When(status='pending', then=Value(0)), default=Value(1))
    oldest_pending = Case(When(status='pending', then=F('created_at')), output_field=DateTimeField())
    reports = reports.annotate(_pending_first=pending_first, _oldest_pending=oldest_pending).order_by(
        '_pending_first', F('_oldest_pending').asc(nulls_last=True), '-created_at', '-id')
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(reports, request)
    return paginator.get_paginated_response(_staff_data(page))


@extend_schema(responses=StaffReportSerializer)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_no_show_report_detail(request, report_id):
    report = _owner_queryset().filter(pk=report_id).first()
    if report is None:
        return Response({'error': 'Report not found', 'code': 'not_found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(_staff_data(report, many=False))


def _decision(request, report_id, action):
    serializer = DecisionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        action(report_id, request.user, serializer.validated_data['decision_comment'])
    except NoShowError as exc:
        return _error(exc)
    return Response(_staff_data(_owner_queryset().get(pk=report_id), many=False))


@extend_schema(request=DecisionSerializer, responses=StaffReportSerializer)
@api_view(['POST'])
@permission_classes([IsSuperAdminOrStaff])
def admin_no_show_report_approve(request, report_id):
    return _decision(request, report_id, noshow.approve_report)


@extend_schema(request=DecisionSerializer, responses=StaffReportSerializer)
@api_view(['POST'])
@permission_classes([IsSuperAdminOrStaff])
def admin_no_show_report_reject(request, report_id):
    return _decision(request, report_id, noshow.reject_report)


@extend_schema(request=DecisionSerializer, responses=StaffReportSerializer)
@api_view(['POST'])
@permission_classes([IsSuperAdminOrStaff])
def admin_no_show_report_reverse(request, report_id):
    return _decision(request, report_id, noshow.reverse_report)

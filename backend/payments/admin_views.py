"""
Staff follow-up of refunds (R12), under /api/v1/admin-panel/refunds/.

- GET  needs-attention/   staff: refunds that failed, need a manual refund, or are still
                          pending after an hour; oldest first. Ids, booking reference and
                          amounts only (no guest name, phone or email)
- POST {id}/mark-done/    super-admin: a needs_manual refund was paid by hand; requires
                          provider_reference (bank / provider cabinet id). Audit-logged
- POST {id}/retry/        super-admin: send a failed refund to the provider again. Audit-logged
"""
from datetime import timedelta

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from admin_panel.models import AdminAccessLog
from admin_panel.views import IsSuperAdmin, IsSuperAdminOrStaff
from payments.models import Refund
from payments.refunds import RefundError, mark_manual_done, retry_refund

PENDING_TOO_LONG = timedelta(hours=1)


class RefundRowSerializer(serializers.ModelSerializer):
    payment_id = serializers.IntegerField(read_only=True)
    booking_id = serializers.IntegerField(read_only=True)
    booking_reference = serializers.CharField(source='booking.confirmation_code', read_only=True)
    provider = serializers.CharField(source='payment.provider', read_only=True)

    class Meta:
        model = Refund
        fields = ['id', 'payment_id', 'booking_id', 'booking_reference', 'provider', 'amount', 'currency',
                  'reason', 'status', 'error_code', 'provider_reference', 'created_at', 'updated_at']
        read_only_fields = fields


class RefundPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


@extend_schema(responses=RefundRowSerializer(many=True))
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def refunds_needs_attention(request):
    old_pending = Q(status='pending', created_at__lt=timezone.now() - PENDING_TOO_LONG)
    rows = (Refund.objects.filter(Q(status__in=('failed', 'needs_manual')) | old_pending)
            .select_related('booking', 'payment').order_by('created_at', 'id'))
    paginator = RefundPagination()
    page = paginator.paginate_queryset(rows, request)
    return paginator.get_paginated_response(RefundRowSerializer(page, many=True).data)


def _respond(refund):
    return Response(RefundRowSerializer(Refund.objects.select_related('booking', 'payment').get(pk=refund.pk)).data)


@extend_schema(request=OpenApiTypes.OBJECT, responses=RefundRowSerializer)
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def refund_mark_done(request, refund_id):
    refund = get_object_or_404(Refund, pk=refund_id)
    reference = str(request.data.get('provider_reference') or '').strip()[:255]
    if not reference:
        return Response({'provider_reference': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
    try:
        refund = mark_manual_done(refund, reference, request.user)
    except RefundError as e:
        return Response({'error': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)
    AdminAccessLog.record(request.user, 'refund_mark_done', target_booking_id=refund.booking_id,
                          details={'refund_id': refund.id})
    return _respond(refund)


@extend_schema(request=None, responses=RefundRowSerializer)
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def refund_retry(request, refund_id):
    refund = get_object_or_404(Refund, pk=refund_id)
    try:
        refund = retry_refund(refund, request.user)
    except RefundError as e:
        return Response({'error': e.message, 'code': e.code}, status=status.HTTP_400_BAD_REQUEST)
    AdminAccessLog.record(request.user, 'refund_retry', target_booking_id=refund.booking_id,
                          details={'refund_id': refund.id})
    return _respond(refund)

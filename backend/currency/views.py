"""
Staff endpoints for exchange rates (R6), under /api/v1/admin-panel/exchange-rates/.

- GET  /                 staff: rate history, newest first
- GET  /status/          super-admin: per currency the rate in use, its date, stale yes/no,
                         the last fetch and its error, rejected rates waiting for a decision
- POST /{id}/accept/     super-admin: use a rate the fetch rejected (jump over FX_MAX_CHANGE);
                         written to the admin audit log with the old and new rate
"""
from django.db import IntegrityError, transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from admin_panel.models import AdminAccessLog
from admin_panel.views import IsSuperAdmin, IsSuperAdminOrStaff
from currency.cbu import FETCHED_CURRENCIES
from currency.models import ExchangeRate, ExchangeRateFetch
from currency.rates import current_rate


class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = ['id', 'currency', 'rate', 'nominal', 'rate_date', 'source', 'status', 'note', 'fetched_at']
        read_only_fields = fields


class ExchangeRatePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


@extend_schema(responses=ExchangeRateSerializer(many=True))
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def exchange_rate_list(request):
    rows = ExchangeRate.objects.all()
    currency = request.query_params.get('currency')
    if currency:
        rows = rows.filter(currency=currency.upper())
    paginator = ExchangeRatePagination()
    page = paginator.paginate_queryset(rows, request)
    return paginator.get_paginated_response(ExchangeRateSerializer(page, many=True).data)


def _fetch_dict(fetch):
    if fetch is None:
        return None
    return {'attempted_at': fetch.attempted_at, 'success': fetch.success, 'error': fetch.error or None}


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def exchange_rate_status(request):
    currencies = []
    for currency in FETCHED_CURRENCIES:
        rate = current_rate(currency)
        last_fetch = ExchangeRateFetch.objects.filter(currency=currency).first()
        last_failure = ExchangeRateFetch.objects.filter(currency=currency, success=False).first()
        rejected = ExchangeRate.objects.filter(currency=currency, status='rejected')
        if rate is not None and rate.date:
            rejected = rejected.filter(rate_date__gt=rate.date)
        currencies.append({
            'currency': currency,
            'rate': f'{rate.rate:.6f}' if rate else None,
            'date': rate.date.isoformat() if rate and rate.date else None,
            'source': rate.source if rate else None,
            # no rate at all is the worst kind of stale: foreign-currency hotels cannot be booked
            'stale': rate.stale if rate else True,
            'last_fetch': _fetch_dict(last_fetch),
            'last_error': last_failure.error if last_failure else None,
            'rejected': ExchangeRateSerializer(rejected[:10], many=True).data,
        })
    return Response({'currencies': currencies})


@extend_schema(request=None, responses=ExchangeRateSerializer)
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def exchange_rate_accept(request, rate_id):
    """
    Accept a rejected rate: a new accepted row with the same values is appended (history
    is never rewritten) and becomes the rate in use for its date.
    """
    rejected = ExchangeRate.objects.filter(pk=rate_id).first()
    if rejected is None:
        return Response({'error': 'Exchange rate not found'}, status=status.HTTP_404_NOT_FOUND)
    if rejected.status != 'rejected':
        return Response({'error': 'Only a rejected rate can be accepted'}, status=status.HTTP_400_BAD_REQUEST)

    old = current_rate(rejected.currency)
    try:
        with transaction.atomic():
            accepted = ExchangeRate.objects.create(
                currency=rejected.currency, rate=rejected.rate, nominal=rejected.nominal,
                rate_date=rejected.rate_date, source=rejected.source, status='accepted',
                note=f'accepted by super-admin (user {request.user.pk}) from rejected #{rejected.pk}',
            )
            AdminAccessLog.record(request.user, 'exchange_rate_accept', details={
                'currency': rejected.currency, 'rate_date': rejected.rate_date.isoformat(),
                'old_rate': f'{old.rate:.6f}' if old else None, 'new_rate': f'{rejected.rate:.6f}',
                'rejected_id': rejected.pk, 'accepted_id': accepted.pk,
            })
    except IntegrityError:
        return Response({'error': 'A rate for this date is already accepted'}, status=status.HTTP_409_CONFLICT)
    return Response(ExchangeRateSerializer(accepted).data, status=status.HTTP_201_CREATED)

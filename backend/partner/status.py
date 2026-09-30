"""
Partner Status tab: GET /api/v1/partner/status/ (the hotel owner's own properties only).

Totals since the account was created (or for ?period=YYYY / YYYY-MM), a per-property
breakdown and a monthly series for ?year= (default: the current year).
Definitions of counted bookings, guests and revenue: bookings/stats.py.
"""
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from bookings.stats import (
    InvalidPeriod, available_years, counted_bookings, metric_annotations, metric_totals,
    monthly_series, parse_period, parse_year, revenue_by,
)
from partner.views import IsHotelOwner
from properties.models import Property
from properties.regions import hotel_name_expression, region_expression


@api_view(['GET'])
@permission_classes([IsHotelOwner])
def partner_status(request):
    try:
        period, date_range = parse_period(request.query_params.get('period'))
    except InvalidPeriod as error:
        return Response({'period': [str(error)]}, status=status.HTTP_400_BAD_REQUEST)
    try:
        year = parse_year(request.query_params.get('year'), timezone.localdate().year)
    except InvalidPeriod as error:
        return Response({'year': [str(error)]}, status=status.HTTP_400_BAD_REQUEST)

    own = Property.objects.filter(owner=request.user, is_deleted=False)
    all_bookings = counted_bookings().filter(property__in=own)
    in_period = counted_bookings(date_range).filter(property__in=own)

    rows = (
        own.annotate(name=hotel_name_expression(), region=region_expression())
        .values('id', 'name', 'city', 'region', 'country', 'status')
        .annotate(**metric_annotations('bookings__', date_range))
        .order_by('name', 'id')
    )
    revenue = revenue_by(in_period, 'property_id')
    properties = [
        {
            'id': row['id'], 'name': row['name'], 'city': row['city'], 'region': row['region'],
            'country': row['country'], 'status': row['status'],
            'bookings': row['bookings_count'], 'guests': row['guests_count'],
            'revenue': revenue.get(row['id'], []),
        }
        for row in rows
    ]
    return Response({
        'since': request.user.date_joined.date().isoformat(),
        'period': period,
        'totals': metric_totals(in_period),
        'properties': properties,
        'year': year,
        'available_years': available_years(all_bookings),
        'monthly': monthly_series(all_bookings, year),
    })

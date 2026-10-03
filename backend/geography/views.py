"""
Public geography API (Geography plan G3). Read-only, no login.

Only active rows are listed. hotel_count is the number of public properties
(active, approved, not deleted) and comes from one annotated query per list.
"""
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from geography.models import City, Country, Region

PUBLIC_PROPERTY = Q(properties__is_active=True, properties__is_deleted=False, properties__status='active')
NAME_FIELDS = ('name_uz', 'name_ru', 'name_en')


def _rows(queryset, *fields):
    return list(
        queryset.annotate(hotel_count=Count('properties', filter=PUBLIC_PROPERTY))
        .order_by('sort_order', 'name_en')  # Meta.ordering is ignored once the query aggregates
        .values('id', *fields, *NAME_FIELDS, 'hotel_count')
    )


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def country_list(request):
    """Active countries with their currency and hotel counts."""
    return Response(_rows(Country.objects.filter(is_active=True), 'code', 'currency'))


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def region_list(request, code):
    """Active regions of an active country (code is case-insensitive)."""
    country = get_object_or_404(Country, code=code.upper(), is_active=True)
    return Response(_rows(Region.objects.filter(country=country, is_active=True)))


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def city_list(request, region_id):
    """Active cities of an active region in an active country."""
    region = get_object_or_404(Region, pk=region_id, is_active=True, country__is_active=True)
    return Response(_rows(City.objects.filter(region=region, is_active=True)))

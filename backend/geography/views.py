"""
Public geography API (Geography plan G3). Read-only, no login.

Only active rows are listed. hotel_count is the number of public properties
(active, approved, not deleted) and comes from one annotated query per list.
"""
from django.core.files.storage import default_storage
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from common import public_cache
from geography.models import City, Country, Region

PUBLIC_PROPERTY = Q(properties__is_active=True, properties__is_deleted=False, properties__status='active')
NAME_FIELDS = ('name_uz', 'name_ru', 'name_en')


def _rows(queryset, *fields):
    rows = list(
        queryset.annotate(hotel_count=Count('properties', filter=PUBLIC_PROPERTY))
        .order_by('sort_order', 'name_en')  # Meta.ordering is ignored once the query aggregates
        .values('id', *fields, *NAME_FIELDS, 'hotel_count')
    )
    if 'image' in fields:
        for row in rows:
            name = row.pop('image')
            row['image_url'] = default_storage.url(name) if name else None
    return rows


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def country_list(request):
    """Active countries with their currency and hotel counts."""
    return Response(public_cache.remember(
        request, 'countries', lambda: _rows(Country.objects.filter(is_active=True), 'code', 'currency', 'image')))


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def region_list(request, code):
    """Active regions of an active country (code is case-insensitive)."""
    def build():
        country = get_object_or_404(Country, code=code.upper(), is_active=True)
        return _rows(Region.objects.filter(country=country, is_active=True), 'image')

    return Response(public_cache.remember(request, 'regions', build))


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def city_list(request, region_id):
    """Active cities of an active region in an active country."""
    def build():
        region = get_object_or_404(Region, pk=region_id, is_active=True, country__is_active=True)
        return _rows(City.objects.filter(region=region, is_active=True))

    return Response(public_cache.remember(request, 'cities', build))

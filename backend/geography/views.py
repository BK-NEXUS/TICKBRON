"""
Ashıq geografiya API ı (Geography reje G3). Tek oqıw, kirisiw joq.

Tek aktiv qatarlar dizimlenedi. hotel_count ashıq mehmanxanalar sanı
(aktiv, tastıyıqlanǵan, óshirilmegen) hám hár dizim ushın bir annotation lanǵan query den keledi.
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
from geography.models import Country, Region

PUBLIC_PROPERTY = Q(properties__is_active=True, properties__is_deleted=False, properties__status='active')
NAME_FIELDS = ('name_uz', 'name_ru', 'name_en')


def _rows(queryset, *fields):
    rows = list(
        queryset.annotate(hotel_count=Count('properties', filter=PUBLIC_PROPERTY))
        .order_by('sort_order', 'name_en')  # Query jıynaqlaǵannan keyin Meta.ordering itibarǵa alınbaydı
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
    """Valyutası hám mehmanxana sanları menen aktiv mámleketler."""
    return Response(public_cache.remember(
        request, 'countries', lambda: _rows(Country.objects.filter(is_active=True), 'code', 'currency', 'image')))


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
def region_list(request, code):
    """Aktiv mámlekettegi aktiv regionlar (kod register ti esapqa almaydı)."""
    def build():
        country = get_object_or_404(Country, code=code.upper(), is_active=True)
        return _rows(Region.objects.filter(country=country, is_active=True), 'image')

    return Response(public_cache.remember(request, 'regions', build))

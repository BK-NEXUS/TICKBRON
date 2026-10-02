"""
Super-admin geography API (Geography plan G3), mounted at /api/v1/admin-panel/geography/.

Countries, regions and cities: list (search, filters, hidden rows included), create, edit,
hide/show (PATCH is_active) and reorder. A row in use cannot be deleted (PROTECT): 409, hide it instead.
"""
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from admin_panel.views import IsSuperAdmin
from geography.admin_serializers import (
    AdminCitySerializer, AdminCountrySerializer, AdminRegionSerializer, search_filter,
)
from geography.models import City, Country, Region

PUBLIC_PROPERTY = Q(properties__is_active=True, properties__is_deleted=False, properties__status='active')


class GeographyPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 200


class BaseGeographyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsSuperAdmin]
    pagination_class = GeographyPagination
    model = None
    search_extra = ()
    parent_param = None  # query parameter that filters by the parent id

    def filter_queryset(self, queryset):
        params = self.request.query_params
        queryset = search_filter(queryset, params.get('search'), self.search_extra)
        flag = params.get('is_active')
        if flag in ('true', 'false'):
            queryset = queryset.filter(is_active=(flag == 'true'))
        if self.parent_param:
            parent = params.get(self.parent_param, '')
            if parent.isdigit():
                queryset = queryset.filter(**{f'{self.parent_param}_id': int(parent)})
            elif parent:
                queryset = queryset.none()
        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            with transaction.atomic():
                instance.delete()
        except ProtectedError:
            return Response(
                {'error': 'This row is in use (it has regions, cities or properties). Hide it instead.'},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path='reorder')
    def reorder(self, request):
        """POST {"ids": [..]}: sort_order becomes the position of each id in the list."""
        ids = request.data.get('ids') if hasattr(request.data, 'get') else None
        if not isinstance(ids, list) or not ids \
                or not all(isinstance(i, int) and not isinstance(i, bool) for i in ids):
            return Response({'error': 'ids must be a non-empty list of ids'}, status=status.HTTP_400_BAD_REQUEST)
        if len(set(ids)) != len(ids):
            return Response({'error': 'ids must not repeat'}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            rows = {row.pk: row for row in self.model.objects.select_for_update().filter(pk__in=ids)}
            if len(rows) != len(ids):
                return Response({'error': 'unknown id in ids'}, status=status.HTTP_400_BAD_REQUEST)
            for position, pk in enumerate(ids):
                if rows[pk].sort_order != position:
                    rows[pk].sort_order = position
                    rows[pk].save(update_fields=['sort_order', 'updated_at'])
        return Response({'ids': ids})


class AdminCountryViewSet(BaseGeographyViewSet):
    serializer_class = AdminCountrySerializer
    model = Country
    search_extra = ('code',)

    def get_queryset(self):
        return Country.objects.annotate(
            region_count=Count('regions', distinct=True),
            hotel_count=Count('properties', filter=PUBLIC_PROPERTY, distinct=True),
        ).order_by('sort_order', 'name_en')


class AdminRegionViewSet(BaseGeographyViewSet):
    serializer_class = AdminRegionSerializer
    model = Region
    parent_param = 'country'

    def get_queryset(self):
        return Region.objects.annotate(
            city_count=Count('cities', distinct=True),
            hotel_count=Count('properties', filter=PUBLIC_PROPERTY, distinct=True),
        ).order_by('sort_order', 'name_en')


class AdminCityViewSet(BaseGeographyViewSet):
    serializer_class = AdminCitySerializer
    model = City
    parent_param = 'region'

    def get_queryset(self):
        return City.objects.annotate(
            hotel_count=Count('properties', filter=PUBLIC_PROPERTY, distinct=True),
        ).order_by('sort_order', 'name_en')

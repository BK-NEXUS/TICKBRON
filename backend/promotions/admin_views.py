"""Super-admin endpoints for hotel promotions. Reads: staff or super-admin; changes: super-admin only."""
from datetime import datetime

from django.db.models import Exists, OuterRef, Q, Sum
from django.db.models.functions import Coalesce
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.response import Response

from admin_panel.views import IsSuperAdmin, IsSuperAdminOrStaff
from common.dates import business_today
from promotions import service
from promotions.admin_serializers import (
    CancelSerializer, PromotionCreateSerializer, PromotionSerializer, PromotionUpdateSerializer)
from promotions.models import Promotion, PromotionDailyStat
from promotions.service import PromotionError
from properties.models import Property, PropertyTranslation

HOTEL_SEARCH_LIMIT = 20
ORDERING = {
    'start': 'start_date', '-start': '-start_date', 'priority': 'priority', '-priority': '-priority',
    'clicks': 'sum_clicks', '-clicks': '-sum_clicks',
}


class StaffReadsSuperAdminWrites(BasePermission):
    def has_permission(self, request, view):
        checker = IsSuperAdminOrStaff() if request.method in SAFE_METHODS else IsSuperAdmin()
        return checker.has_permission(request, view)


def _error(exc):
    code = status.HTTP_404_NOT_FOUND if exc.code == 'not_found' else status.HTTP_400_BAD_REQUEST
    return Response({'error': exc.message, 'code': exc.code}, status=code)


def _bad(message):
    return Response({'error': message, 'code': 'invalid_query'}, status=status.HTTP_400_BAD_REQUEST)


def _date_param(request, name):
    raw = request.query_params.get(name)
    if not raw:
        return None, None
    try:
        return datetime.strptime(raw, '%Y-%m-%d').date(), None
    except ValueError:
        return None, _bad(f'{name} must be YYYY-MM-DD')


def _queryset():
    return (Promotion.objects.filter(is_deleted=False)
            .select_related('property')
            .prefetch_related('property__translations')
            .annotate(sum_impressions=Coalesce(Sum('daily_stats__impressions'), 0),
                      sum_clicks=Coalesce(Sum('daily_stats__clicks'), 0)))


def _find(promotion_id):
    return _queryset().filter(pk=promotion_id).first()


def _not_found():
    return Response({'error': 'Promotion not found', 'code': 'not_found'}, status=status.HTTP_404_NOT_FOUND)


def _one(promotion_id):
    return PromotionSerializer(_find(promotion_id)).data


def _filtered(request):
    promotions = _queryset()
    state = request.query_params.get('status')
    if state:
        if state not in dict(Promotion.STATUS_CHOICES):
            return None, _bad('Unknown status')
        promotions = promotions.filter(status=state)
    paid = request.query_params.get('paid')
    if paid:
        if paid not in ('true', 'false'):
            return None, _bad('paid must be true or false')
        promotions = promotions.filter(paid_at__isnull=(paid == 'false'))
    first, error = _date_param(request, 'from')
    if error:
        return None, error
    last, error = _date_param(request, 'to')
    if error:
        return None, error
    if first:
        promotions = promotions.filter(end_date__gte=first)
    if last:
        promotions = promotions.filter(start_date__lte=last)
    name = (request.query_params.get('q') or '').strip()
    if name:
        # A subquery, not a join: a join per translation would multiply the Sum() totals
        named = PropertyTranslation.objects.filter(
            property=OuterRef('property_id'), is_deleted=False, name__icontains=name)
        promotions = promotions.filter(Exists(named))
    ordering = request.query_params.get('ordering', '-start')
    if ordering not in ORDERING:
        return None, _bad('Unknown ordering')
    return promotions.order_by(ORDERING[ordering], '-id'), None


@extend_schema(request=PromotionCreateSerializer, responses=PromotionSerializer(many=True))
@api_view(['GET', 'POST'])
@permission_classes([StaffReadsSuperAdminWrites])
def promotions(request):
    if request.method == 'POST':
        return _create(request)
    queryset, error = _filtered(request)
    if error:
        return error
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(queryset, request)
    return paginator.get_paginated_response(PromotionSerializer(page, many=True).data)


def _create(request):
    serializer = PromotionCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        promotion = service.create_promotion(actor=request.user, **serializer.validated_data)
    except PromotionError as exc:
        return _error(exc)
    return Response(_one(promotion.pk), status=status.HTTP_201_CREATED)


@extend_schema(request=PromotionUpdateSerializer, responses=PromotionSerializer)
@api_view(['GET', 'PATCH'])
@permission_classes([StaffReadsSuperAdminWrites])
def promotion_detail(request, promotion_id):
    promotion = _find(promotion_id)
    if promotion is None:
        return _not_found()
    if request.method == 'GET':
        return Response(PromotionSerializer(promotion).data)
    serializer = PromotionUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    if not serializer.validated_data:
        return _error(PromotionError('nothing_to_change', 'No changes were sent'))
    try:
        service.update_promotion(promotion, actor=request.user, **serializer.validated_data)
    except PromotionError as exc:
        return _error(exc)
    return Response(_one(promotion_id))


def _action(request, promotion_id, run):
    promotion = _find(promotion_id)
    if promotion is None:
        return _not_found()
    try:
        run(promotion)
    except PromotionError as exc:
        return _error(exc)
    return Response(_one(promotion_id))


@extend_schema(request=None, responses=PromotionSerializer)
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def promotion_pause(request, promotion_id):
    return _action(request, promotion_id, lambda promotion: service.pause(promotion, actor=request.user))


@extend_schema(request=None, responses=PromotionSerializer)
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def promotion_resume(request, promotion_id):
    return _action(request, promotion_id, lambda promotion: service.resume(promotion, actor=request.user))


@extend_schema(request=None, responses=PromotionSerializer)
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def promotion_mark_paid(request, promotion_id):
    return _action(request, promotion_id, lambda promotion: service.mark_paid(promotion, actor=request.user))


@extend_schema(request=CancelSerializer, responses=PromotionSerializer)
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def promotion_cancel(request, promotion_id):
    serializer = CancelSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    reason = serializer.validated_data['reason']
    return _action(request, promotion_id,
                   lambda promotion: service.cancel(promotion, actor=request.user, reason=reason))


def _ctr(impressions, clicks):
    return round(clicks / impressions * 100, 2) if impressions else None


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def promotion_stats(request, promotion_id):
    if not Promotion.objects.filter(pk=promotion_id, is_deleted=False).exists():
        return _not_found()
    first, error = _date_param(request, 'from')
    if error:
        return error
    last, error = _date_param(request, 'to')
    if error:
        return error
    rows = PromotionDailyStat.objects.filter(promotion_id=promotion_id).order_by('date')
    if first:
        rows = rows.filter(date__gte=first)
    if last:
        rows = rows.filter(date__lte=last)
    days = [{'date': row.date, 'impressions': row.impressions, 'clicks': row.clicks,
             'ctr': _ctr(row.impressions, row.clicks)} for row in rows]
    impressions = sum(day['impressions'] for day in days)
    clicks = sum(day['clicks'] for day in days)
    return Response({'days': days, 'totals': {'impressions': impressions, 'clicks': clicks,
                                              'ctr': _ctr(impressions, clicks)}})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def promotion_hotels(request):
    """Find a hotel by name to promote it. Any status is listed so the admin sees why one cannot be shown."""
    term = (request.query_params.get('q') or '').strip()
    if len(term) < 2:
        return Response({'results': []})
    running = Promotion.objects.filter(
        property=OuterRef('pk'), is_deleted=False, status__in=Promotion.HOLDING_STATUSES,
        end_date__gte=business_today())
    hotels = (Property.objects.filter(is_deleted=False)
              .filter(Q(translations__name__icontains=term, translations__is_deleted=False)
                      | Q(address_line1__icontains=term) | Q(city__icontains=term))
              .distinct().prefetch_related('translations')
              .annotate(has_running=Exists(running)).order_by('id')[:HOTEL_SEARCH_LIMIT])
    return Response({'results': [
        {'id': hotel.pk, 'name': hotel.display_name(), 'city': hotel.city, 'status': hotel.status,
         'has_running_promotion': hotel.has_running} for hotel in hotels]})

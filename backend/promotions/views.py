"""Public promotion endpoints: the home carousel and the click counter."""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from config.settings import TESTING
from promotions import service, stats
from promotions.search import promoted_for_home, serialize_banners


class PromotionPublicThrottle(AnonRateThrottle):
    """60 requests per minute per IP for the public promotion endpoints."""
    rate = '60/min'
    scope = 'promotion_public'

    def allow_request(self, request, view):
        if TESTING:
            return True
        return super().allow_request(request, view)


@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([PromotionPublicThrottle])
def home_promotions(request):
    """Banners for the home page carousel (at most 8). Optional `country` = geography country id."""
    country_id = None
    raw = request.query_params.get('country')
    if raw is not None:
        if not raw.isdigit() or int(raw) < 1:
            return Response({'error': 'Invalid country', 'details': 'country must be a positive integer'},
                            status=status.HTTP_400_BAD_REQUEST)
        country_id = int(raw)
    entries = promoted_for_home(country_id)
    stats.record(stats.IMPRESSION, [promotion.pk for promotion, _ in entries], request)
    return Response({'results': serialize_banners(request, entries)})


@extend_schema(request=None, responses={204: None})
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PromotionPublicThrottle])
def promotion_click(request, promotion_id):
    """The frontend calls this when a banner is opened. Unknown or not-shown ids are 404."""
    if not service.shown_now().filter(pk=promotion_id).exists():
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    stats.record(stats.CLICK, [promotion_id], request)
    return Response(status=status.HTTP_204_NO_CONTENT)

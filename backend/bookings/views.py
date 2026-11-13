"""
TICKBRON bron endpoint leri ushın view ler.
"""
import logging
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.conf import settings
from common.dates import business_today
from currency.rates import ExchangeRateUnavailable
from .models import Booking, BookingItem
from .serializers import BookingSerializer, BookingCreateSerializer, BookingCancelSerializer
from django.utils.translation import gettext as _

logger = logging.getLogger('tickbron')

# Bronlar birden tastıyıqlanadı hám naqd tólenedi, sol sebepli hesh nárse ápiwayı akkaunttıń xonalardı alıwına tosqınlıq
# etpeydi;
# shekleusiz bir akkaunt pútkil mehmanxananı bos emes etip ustap turıwı múmkin (tólenbegen bronlardıń eski shegi de)
# Iyeniń qararı 2026-10-23: bir akkaunt eń kóbi eki keletuǵın bronnı ustaydı, hám olardıń sanaları hesh qashan kesilispeydi
MAX_UPCOMING_BOOKINGS_PER_GUEST = 2


class BookingCreateThrottle(UserRateThrottle):
    """Paydalanıwshı boyınsha bron jaratıw (sazlama: THROTTLE_BOOKING_CREATE_RATE)."""
    scope = 'booking_create'

    def allow_request(self, request, view):
        if settings.TESTING:
            return True
        return super().allow_request(request, view)


class BookingViewSet(mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    """
    Bronlardı basqarıw ushın ViewSet.

    Tek create, list hám retrieve qollap-quwatlanadı. Mehmanlar bronlardı hesh qashan tikkeley
    jańalamaydı yamasa óshirmeydi: status ózgerisleri state machine arqalı ótedi
    (mısalı biykar etiw endpoint i), sol sebepli PUT/PATCH/DELETE 405 qaytaradı.
    """
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Házirgi paydalanıwshınıń bronların qaytaradı."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema jasaw: paydalanıwshı joq
            return self.get_serializer_class().Meta.model.objects.none()
        return Booking.objects.filter(
            guest=self.request.user,
            is_deleted=False
        ).select_related('guest', 'property').prefetch_related(
            # Element serializer i hár xona túrin hám rate plan dı ataydı: olardı elementler menen birge alıń
            Prefetch('booking_items', queryset=BookingItem.objects.select_related('room_type', 'rate_plan')),
            'property__translations',
        )

    @staticmethod
    def _pending_cap_reached(user):
        """Mehmanda ele eń kóp keletuǵın bron bar (biykar etilmegen, kelmegen, pitpegen)."""
        upcoming = Booking.objects.filter(
            guest=user, status__in=('pending', 'confirmed'), arrived_at__isnull=True,
            check_out__gte=business_today(), is_deleted=False,
        ).count()
        return upcoming >= MAX_UPCOMING_BOOKINGS_PER_GUEST

    @staticmethod
    def _pending_cap_response():
        return Response(
            {'error': _('Too many upcoming bookings. Cancel one or wait until you have stayed.'),
             'code': 'too_many_upcoming_bookings'},
            # Bul biznes qaǵıydası, throttling emes: 429 klientlerge hám monitoring ke rate limit sıyaqlı kórinedi
            status=status.HTTP_409_CONFLICT
        )

    @staticmethod
    def _overlaps_another_stay(user, check_in, check_out):
        """Mehmanda usı sanalar menen bir túnin bólisetuǵın aktiv bron bar (shıǵıw kúni bos)."""
        return Booking.objects.filter(
            guest=user, status__in=('pending', 'confirmed'), is_deleted=False,
            check_in__lt=check_out, check_out__gt=check_in,
        ).exists()

    @staticmethod
    def _overlap_response():
        return Response(
            {'error': _('You already have a booking for these dates. Choose dates that start after it ends.'),
             'code': 'overlapping_booking'},
            status=status.HTTP_409_CONFLICT
        )

    def _refused_by_account_rules(self, user, serializer):
        """Bir akkaunt usı sanalardı házir bronlay almasa juwap, bolmasa None."""
        if self._pending_cap_reached(user):
            return self._pending_cap_response()
        if self._overlaps_another_stay(user, serializer.validated_data['check_in'], serializer.validated_data['check_out']):
            return self._overlap_response()
        return None

    def get_throttles(self):
        if self.action == 'create':
            return [BookingCreateThrottle()]
        return super().get_throttles()

    def create(self, request, *args, **kwargs):
        """
        Transaction qáwipsiz inventory qulıplaw menen jańa bron jaratıw.

        Request body:
            property_id: Mehmanxana ID si
            room_type_id: Xona túri ID si
            rate_plan_id: Rate plan ID si
            check_in: Kiriw sanası (YYYY-MM-DD)
            check_out: Shıǵıw sanası (YYYY-MM-DD)
            guest_count: Mehmanlar sanı
            special_requests: Ixtıyarıy arnawlı sorawlar teksti

        Qaytaradı:
            Tastıyıqlaw kodı menen jaratılǵan bron
        """
        serializer = BookingCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response(
                {'error': _('Invalid booking parameters'), 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        refused = self._refused_by_account_rules(request.user, serializer)
        if refused is not None:
            return refused

        try:
            with transaction.atomic():
                # Qaǵıydalardı mehmannıń qatarın qulıplap qayta tekseriw: bunsız birdey
                # sorawlar bir bronlardı oqıp, hámmesi joqarıdaǵı tekseriwden ótedi
                get_user_model().objects.select_for_update().get(pk=request.user.pk)
                refused = self._refused_by_account_rules(request.user, serializer)
                if refused is not None:
                    return refused
                booking = serializer.save()
            response_serializer = BookingSerializer(booking)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        except ExchangeRateUnavailable as e:
            # USD bahalı mehmanxana hám ele kurs joq: hesh nárse rezervlenbedi (R6 sheshimi A)
            return Response(
                {'error': _('Exchange rate unavailable'), 'code': e.default_code, 'details': str(e.detail)},
                status=e.status_code
            )
        except ValidationError as e:
            # Django ValidationError di islew
            return Response(
                {'error': _('Booking validation failed'), 'details': e.message_dict},
                status=status.HTTP_400_BAD_REQUEST
            )
        except DRFValidationError as e:
            # BookingCreateSerializer.create() bunı biznes qaǵıydası buzılǵanda da, kútilmegen
            # ishki qátelikte de kóteredi; eki jaǵdayda da e.detail bul jerge jetkenshe
            # aldınan qáwipsiz, aǵıp ketpeytuǵın xabar boladı.
            body = {'error': 'Booking validation failed', 'details': e.detail}
            if getattr(e, 'reason', None):
                body['reason'] = e.reason
            return Response(body, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            # Haqıyqatında kútilmegen qátelik: str(e) di klientke hesh qashan qaytarmań.
            logger.exception('Unexpected error creating booking')
            return Response(
                {'error': _('Failed to create booking')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        """
        Belgili bir bronnı alıw.

        Path parametrleri:
            id: Bron ID si

        Qaytaradı:
            Bron tolıq maǵlıwmatı
        """
        booking = self.get_object()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        """
        Házirgi paydalanıwshınıń bronların dizimlew, eń jańası birinshi, bir betke 20.

        Query parametrleri:
            status: Status boyınsha filter (ıqtıyarıy)
            payment_status: Tólem statusı boyınsha filter (ıqtıyarıy)
            page: Bet nomeri (ıqtıyarıy)

        Qaytaradı:
            { count, next, previous, results }
        """
        queryset = self.get_queryset().order_by('-created_at', '-id')

        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        payment_status_filter = request.query_params.get('payment_status')
        if payment_status_filter:
            queryset = queryset.filter(payment_status=payment_status_filter)

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def booking_cancel(request, booking_id):
    """
    Bronnan bas tartıw hám inventory di qaytarıw. Biykar etiw hárdayım tegin: mehmann mehmanxanada naqd tóleydi.

    Path parametrleri:
        booking_id: Bron ID si

    Request body:
        cancellation_reason: Ixtıyarıy biykar etiw sebebi

    Qaytaradı:
        Biykar etilgen statusı menen jańalanǵan bron
    """
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        guest=request.user,
        is_deleted=False
    )

    serializer = BookingCancelSerializer(
        booking,
        data=request.data,
        partial=True,
        context={'booking': booking}
    )

    if not serializer.is_valid():
        return Response(
            {'error': _('Invalid cancellation parameters'), 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        updated_booking = serializer.save()
        return Response(BookingSerializer(updated_booking).data, status=status.HTTP_200_OK)
    except DRFValidationError as e:
        # BookingCancelSerializer.update() bunı biznes qaǵıydası buzılǵanda da, kútilmegen
        # ishki qátelikte de kóteredi; e.detail aldınan qáwipsiz.
        return Response(
            {'error': _('Failed to cancel booking'), 'details': e.detail},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception:
        logger.exception('Unexpected error cancelling booking')
        return Response(
            {'error': _('Failed to cancel booking')},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

"""
Partner API endpoint leri ushın view ler.

Bul modul mehmanxana iyesi akkaunt larına shekemlengen mehmanxana, xona, baha hám bos orınlardı
basqarıw view lerin óz ishine aladı.
"""
from common.alphabet import hotels_with_letter, letter_from
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import routers, viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django.db.models import OuterRef, Prefetch, Subquery
from django.db.models.functions import Coalesce
from properties.models import (
    Property, PropertyType, RoomType, RatePlan, DateInventory, RoomInventory, RoomBlock, PropertyPhoto, RoomPhoto,
)
from bookings.arrival import mark_arrived
from bookings.models import Booking
from partner.models import OwnerPlace
from bookings.noshow import report_deadline, reportable_bookings
from common.csv_export import export_response, wants_export
from common.dates import business_time_zone, business_today
from partner.serializers import (
    MAX_PHOTOS_PER_PROPERTY, MAX_PHOTOS_PER_ROOM_TYPE,
    PartnerPropertySerializer, PartnerPropertyCreateSerializer,
    PartnerRoomTypeSerializer, PartnerRatePlanSerializer,
    PartnerDateInventorySerializer, PartnerRoomInventorySerializer,
    PartnerRoomInventoryBulkSerializer, PartnerDateInventoryBulkPriceSerializer,
    PartnerBlockSerializer, PartnerPropertyPhotoSerializer, PartnerRoomPhotoSerializer
)
from django.utils.translation import gettext as _


class IsHotelOwner(IsAuthenticated):
    """
    Paydalanıwshınıń mehmanxana iyesi ekenin támiyinleytuǵın ruxsat.

    Kirgen paydalanıwshıda mehmanxana iyesi roli yamasa staff statusı barlıǵın tekseredi.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        # Staff paydalanıwshılarına ruxsat beriw (super-admin hám admin)
        if request.user.is_staff:
            return True

        # Paydalanıwshıda mehmanxana iyesi roli barlıǵın tekseriw
        if request.user.role and request.user.role.name == 'hotel-owner':
            return True

        return False


class SoftDeleteDestroyMixin:
    """
    DELETE jazbanı óshirmey, jasıradı. Bronlar óz mehmanxanasına, xona túrine hám
    rate plan ına (PROTECT) baylanıp qaladı, sol sebepli haqıyqıy óshiriw 500 bolar edi yamasa mehmanxana maǵlıwmatın
    joǵaltar edi.
    """

    def perform_destroy(self, instance):
        instance.soft_delete()


class PartnerAPIRootView(routers.APIRootView):
    """Router diń endpoint dizimi; ádetdegisi kirgen qálegen paydalanıwshıǵa ashıq."""
    permission_classes = [IsHotelOwner]


class PartnerPropertyViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    """
    Mehmanxana iyeleri mehmanxanalardı basqarıw ushın ViewSet.

    Kirgen mehmanxana iyesine tiyisli mehmanxanalarǵa shekemlengen.
    """
    permission_classes = [IsHotelOwner]

    def get_queryset(self):
        """Queryset ti kirgen paydalanıwshıǵa tiyisli mehmanxanalarǵa shekemlew."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema jasaw: paydalanıwshı joq
            return self.get_serializer_class().Meta.model.objects.none()
        properties = Property.objects.filter(
            owner=self.request.user,
            is_deleted=False
        ).select_related('property_type').prefetch_related('translations')
        return hotels_with_letter(properties, letter_from(self.request))

    def get_serializer_class(self):
        """Háreketke qarap tiyisli serializer di qaytaradı."""
        if self.action == 'create':
            return PartnerPropertyCreateSerializer
        return PartnerPropertySerializer

    def perform_create(self, serializer):
        """Iyeniń kirgen paydalanıwshı etip belgilenwin támiyinlew."""
        serializer.save(owner=self.request.user)


class PartnerRoomTypeViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    """
    Mehmanxana iyeleri xona túrlerin basqarıw ushın ViewSet.

    Kirgen mehmanxana iyesine tiyisli mehmanxanalardaǵı xona túrlerine shekemlengen.
    """
    permission_classes = [IsHotelOwner]
    serializer_class = PartnerRoomTypeSerializer

    def get_queryset(self):
        """Queryset ti kirgen paydalanıwshıǵa tiyisli mehmanxanalardaǵı xona túrlerine shekemlew."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema jasaw: paydalanıwshı joq
            return self.get_serializer_class().Meta.model.objects.none()
        live_photos = Prefetch(
            'photos', queryset=RoomPhoto.objects.filter(is_deleted=False, is_active=True).order_by('display_order', 'id'),
            to_attr='live_photos')
        return RoomType.objects.filter(
            property__owner=self.request.user,
            is_deleted=False
        ).select_related('property').prefetch_related(live_photos)


class PartnerRatePlanViewSet(SoftDeleteDestroyMixin, viewsets.ModelViewSet):
    """
    Mehmanxana iyeleri rate plan larǵı basqarıw ushın ViewSet.

    Kirgen mehmanxana iyesine tiyisli mehmanxanalardaǵı rate plan larǵa shekemlengen.
    """
    permission_classes = [IsHotelOwner]
    serializer_class = PartnerRatePlanSerializer

    def get_queryset(self):
        """Queryset ti kirgen paydalanıwshıǵa tiyisli mehmanxanalardaǵı rate plan larǵa shekemlew."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema jasaw: paydalanıwshı joq
            return self.get_serializer_class().Meta.model.objects.none()
        return RatePlan.objects.filter(
            room_type__property__owner=self.request.user,
            is_deleted=False
        ).select_related('room_type__property').prefetch_related('prices')


class PartnerDateInventoryViewSet(viewsets.ModelViewSet):
    """
    Mehmanxana iyeleri date inventory di basqarıw ushın ViewSet.

    Kirgen mehmanxana iyesine tiyisli mehmanxanalardaǵı date inventory ge shekemlengen.
    """
    permission_classes = [IsHotelOwner]
    serializer_class = PartnerDateInventorySerializer

    def get_queryset(self):
        """Queryset ti kirgen paydalanıwshıǵa tiyisli mehmanxanalardaǵı date inventory ge shekemlew."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema jasaw: paydalanıwshı joq
            return self.get_serializer_class().Meta.model.objects.none()
        queryset = DateInventory.objects.filter(
            rate_plan__room_type__property__owner=self.request.user,
            is_deleted=False
        ).select_related('rate_plan__room_type__property').annotate(room_booked=Coalesce(Subquery(
            RoomInventory.objects.filter(
                room_type=OuterRef('rate_plan__room_type'), date=OuterRef('date'), is_deleted=False,
            ).values('booked_rooms')[:1]), 0))
        if self.action == 'list':
            queryset = self._filter_list(queryset).order_by('date', 'id')
        return queryset

    def _filter_list(self, queryset):
        """
        Ixtıyarıy dizim filter leri: ?rate_plan=<id>&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
        (ekewi de kiredi). Jaramsız mánisler 400, ún-túnsiz itibarǵa alınbaǵan filter emes.
        """
        params = self.request.query_params
        errors = {}

        rate_plan = params.get('rate_plan')
        if rate_plan:
            if rate_plan.isdigit():
                queryset = queryset.filter(rate_plan_id=int(rate_plan))
            else:
                errors['rate_plan'] = ['Must be a rate plan id.']

        dates = {}
        for name in ('date_from', 'date_to'):
            value = params.get(name)
            if not value:
                continue
            try:
                parsed = parse_date(value) if len(value) == 10 else None
            except ValueError:  # durıs jazılǵan, biraq múmkin emes, mısalı 2026-02-30
                parsed = None
            if parsed is None:
                errors[name] = ['Must be a date in YYYY-MM-DD format.']
            else:
                dates[name] = parsed

        if 'date_from' in dates and 'date_to' in dates and dates['date_from'] > dates['date_to']:
            errors['date_to'] = ['Must not be before date_from.']
        if errors:
            raise ValidationError(errors)

        if 'date_from' in dates:
            queryset = queryset.filter(date__gte=dates['date_from'])
        if 'date_to' in dates:
            queryset = queryset.filter(date__lte=dates['date_to'])
        return queryset

    @action(detail=False, methods=['post'], url_path='bulk-price')
    def bulk_price(self, request):
        """
        3.7 kóp bahanı ózgertiw: bir rate plan nıń túngi bahasın sana aralıǵı boyınsha belgilew.

        Body: {rate_plan, date_from, date_to, price}. date_to kirmeydi (exclusive), bronnıń
        check_in/check_out ı sıyaqlı kelisim (bul dizimniń óz date_from/date_to
        filter lerinen ayrıqsha, olar kiredi). Joq qatardı jaratadı (xona túriniń tolıq
        total_rooms ı menen ashılǵan); bar qatardıń basqa maydanlarına tiyilmeydi.
        """
        serializer = PartnerDateInventoryBulkPriceSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            rows = DateInventory.bulk_set_price(data['rate_plan'], data['date_from'], data['date_to'], data['price'])
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict)
        return Response(PartnerDateInventorySerializer(rows, many=True).data, status=status.HTTP_200_OK)


class PartnerRoomInventoryViewSet(viewsets.ModelViewSet):
    """
    Mehmanxana iyeleri xona inventory sın (RoomInventory, audit #31) basqarıw ushın ViewSet.

    Kirgen mehmanxana iyesine tiyisli mehmanxanalardaǵı xona inventory sine shekemlengen. Bul
    xona túriniń haqıyqıy, ortaq fizikalıq xona sanı; DateInventory (qarań
    PartnerDateInventoryViewSet) ele baha hám hár rate plan nıń óz qaǵıydaların saqlaydı.
    """
    permission_classes = [IsHotelOwner]
    serializer_class = PartnerRoomInventorySerializer

    def get_queryset(self):
        """Queryset ti kirgen paydalanıwshıǵa tiyisli mehmanxanalardaǵı xona inventory sine shekemlew."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema jasaw: paydalanıwshı joq
            return self.get_serializer_class().Meta.model.objects.none()
        queryset = RoomInventory.objects.filter(
            room_type__property__owner=self.request.user,
            is_deleted=False
        ).select_related('room_type__property')
        if self.action == 'list':
            queryset = self._filter_list(queryset).order_by('date', 'id')
        return queryset

    def _filter_list(self, queryset):
        """
        Ixtıyarıy dizim filter leri: ?room_type=<id>&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
        (ekewi de kiredi). Jaramsız mánisler 400, ún-túnsiz itibarǵa alınbaǵan filter emes.
        """
        params = self.request.query_params
        errors = {}

        room_type = params.get('room_type')
        if room_type:
            if room_type.isdigit():
                queryset = queryset.filter(room_type_id=int(room_type))
            else:
                errors['room_type'] = ['Must be a room type id.']

        dates = {}
        for name in ('date_from', 'date_to'):
            value = params.get(name)
            if not value:
                continue
            try:
                parsed = parse_date(value) if len(value) == 10 else None
            except ValueError:  # durıs jazılǵan, biraq múmkin emes, mısalı 2026-02-30
                parsed = None
            if parsed is None:
                errors[name] = ['Must be a date in YYYY-MM-DD format.']
            else:
                dates[name] = parsed

        if 'date_from' in dates and 'date_to' in dates and dates['date_from'] > dates['date_to']:
            errors['date_to'] = ['Must not be before date_from.']
        if errors:
            raise ValidationError(errors)

        if 'date_from' in dates:
            queryset = queryset.filter(date__gte=dates['date_from'])
        if 'date_to' in dates:
            queryset = queryset.filter(date__lte=dates['date_to'])
        return queryset

    @action(detail=False, methods=['post'])
    def bulk(self, request):
        """
        3.6 kalendar sana aralıǵın ózgertiw: bir xona túri ushın available_rooms hám/yamasa is_available di
        bir shaqırıwda sana aralıǵı boyınsha belgilew.

        Body: {room_type, date_from, date_to, available_rooms?, is_available?} (ekewiniń
        keminde biri). date_to kirmeydi (exclusive), bronnıń check_in/check_out ı sıyaqlı
        kelisim (bul dizimniń óz date_from/date_to filter lerinen ayrıqsha, olar
        kiredi). Aldın joq, basqarılmaytuǵın qatardı jaratadı (xona túriniń tolıq
        total_rooms ı menen ashılǵan). available_rooms túnni TICKBRON da aldınan bronlanǵannan
        tómenge túsirse, sananı atap 400.
        """
        serializer = PartnerRoomInventoryBulkSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            rows = RoomInventory.bulk_set(
                data['room_type'], data['date_from'], data['date_to'],
                available_rooms=data.get('available_rooms'), is_available=data.get('is_available'),
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict)
        return Response(PartnerRoomInventorySerializer(rows, many=True).data, status=status.HTTP_200_OK)


class PartnerBlockViewSet(viewsets.ModelViewSet):
    """
    Mehmanxana iyeleri sırtqı bron bloklarınıń (RoomBlock, 3.5) ViewSet i.

    Kirgen mehmanxana iyesine tiyisli mehmanxanalardaǵı xona túrleri bloklarına shekemlengen.
    Birin jaratıw tásirlengen RoomInventory qatarların qulıplaydı hám kemeytedi
    (RoomBlock.create_block, serializer arqalı); birin óshiriw olardı qaytaradı (release()).
    PATCH/PUT joq: blok jaratıladı yamasa biykar etiledi (óshiriledi), ornında hesh qashan ózgertilmeydi.
    """
    permission_classes = [IsHotelOwner]
    serializer_class = PartnerBlockSerializer
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        """Queryset ti kirgen paydalanıwshıǵa tiyisli mehmanxanalardaǵı xona túrleri bloklarına shekemlew."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema jasaw: paydalanıwshı joq
            return self.get_serializer_class().Meta.model.objects.none()
        queryset = RoomBlock.objects.filter(
            room_type__property__owner=self.request.user,
            is_deleted=False
        ).select_related('room_type__property')
        if self.action == 'list':
            room_type = self.request.query_params.get('room_type')
            if room_type:
                if room_type.isdigit():
                    queryset = queryset.filter(room_type_id=int(room_type))
                else:
                    raise ValidationError({'room_type': [_('Must be a room type id.')]})
        return queryset

    def perform_destroy(self, instance):
        """Blokti óshiriw onı biykar etedi: bloklanǵan xonalardı qaytaradı, keyin soft-delete etedi."""
        instance.release()


def _owned_property(request, property_id):
    return get_object_or_404(Property, id=property_id, owner=request.user, is_deleted=False)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET', 'POST'])
@permission_classes([IsHotelOwner])
def partner_property_photos(request, property_id):
    """
    GET: iyeniń bir mehmanxanasınıń súwretleri, muqaba hám tártip saqlanǵanday.
    POST: súwret júklew (multipart: photo, photo_type, caption, alt_text).
    Birinshi súwret muqaba boladı; jańa súwretler aqırına baradı; saqlanǵan
    fayl atı tosınarlıq.
    """
    property = _owned_property(request, property_id)

    if request.method == 'GET':
        photos = PropertyPhoto.objects.filter(property=property, is_deleted=False).order_by('display_order', 'id')
        return Response(PartnerPropertyPhotoSerializer(photos, many=True, context={'request': request}).data)

    if PropertyPhoto.objects.filter(property=property, is_deleted=False).count() >= MAX_PHOTOS_PER_PROPERTY:
        return Response(
            {'photo': [_('A property can have at most %(count)s photos.') % {'count': MAX_PHOTOS_PER_PROPERTY}]},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = PartnerPropertyPhotoSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save(property=property)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['PATCH', 'DELETE'])
@permission_classes([IsHotelOwner])
def partner_property_photo_detail(request, property_id, photo_id):
    """
    PATCH: caption, alt_text, photo_type, is_primary=true (onı muqaba etedi).
    DELETE: súwretti alıp taslaw; alıp taslanǵan muqaba qalǵan birinshi súwretke ótedi.
    """
    property = _owned_property(request, property_id)
    photo = get_object_or_404(PropertyPhoto, id=photo_id, property=property, is_deleted=False)

    if request.method == 'DELETE':
        photo.remove()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = PartnerPropertyPhotoSerializer(photo, data=request.data, partial=True, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data)


def _owned_room_type(request, room_type_id):
    return get_object_or_404(RoomType, id=room_type_id, property__owner=request.user, is_deleted=False)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET', 'POST'])
@permission_classes([IsHotelOwner])
def partner_room_photos(request, room_type_id):
    """
    GET: iyeniń bir xona túriniń súwretleri, muqaba hám tártip saqlanǵanday.
    POST: súwret júklew (multipart: photo, photo_type, caption, alt_text). Birinshi súwret muqaba boladı; jańa
    súwretler aqırına baradı; saqlanǵan fayl atı tosınarlıq; hár xona túrine eń kóbi MAX_PHOTOS_PER_ROOM_TYPE.
    """
    room_type = _owned_room_type(request, room_type_id)
    photos = RoomPhoto.objects.filter(room_type=room_type, is_deleted=False)

    if request.method == 'GET':
        return Response(PartnerRoomPhotoSerializer(
            photos.order_by('display_order', 'id'), many=True, context={'request': request}).data)

    if photos.count() >= MAX_PHOTOS_PER_ROOM_TYPE:
        return Response(
            {'photo': [_('A room type can have at most %(count)s photos.') % {'count': MAX_PHOTOS_PER_ROOM_TYPE}]},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = PartnerRoomPhotoSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save(room_type=room_type)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['PATCH', 'DELETE'])
@permission_classes([IsHotelOwner])
def partner_room_photo_detail(request, room_type_id, photo_id):
    """
    PATCH: caption, alt_text, photo_type, is_primary=true (onı muqaba etedi).
    DELETE: súwretti alıp taslaw; alıp taslanǵan muqaba qalǵan birinshi súwretke ótedi.
    """
    room_type = _owned_room_type(request, room_type_id)
    photo = get_object_or_404(RoomPhoto, id=photo_id, room_type=room_type, is_deleted=False)

    if request.method == 'DELETE':
        photo.remove()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = PartnerRoomPhotoSerializer(photo, data=request.data, partial=True, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsHotelOwner])
def partner_booking_arrived(request, booking_id):
    """
    Mehmanxana óz bronlarınıń birindegi mehmannıń kelgenin aytadı (mehmanxanada naqd). Idempotent: birinshi
    ret saqlanadı. Tek tastıyıqlanǵan bron, kiriw kúninen baslap (basqa jaǵdayda 400).
    """
    booking = get_object_or_404(Booking, id=booking_id, property__owner=request.user, is_deleted=False)
    try:
        mark_arrived(booking)
    except ValueError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'id': booking.id, 'arrived_at': booking.arrived_at})


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsHotelOwner])
def partner_assigned_place(request):
    """Super admin usı akkauntqa bergen orın: {country_ref, region_ref}, joq bolsa ekewi de null."""
    place = OwnerPlace.objects.filter(owner=request.user).first()
    return Response({
        'country_ref': place.country_id if place else None,
        'region_ref': place.region_id if place else None,
    })


@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsHotelOwner])
def partner_property_types(request):
    """"Mehmanxana qosıw" formasınıń hár mehmanxana túri: [{id, name, slug}], ele hesh bir mehmanxana paydalanbaǵan túrler de."""
    types = PropertyType.objects.filter(is_deleted=False).order_by('name')
    return Response([{'id': kind.id, 'name': kind.name, 'slug': kind.slug} for kind in types])


# Iyeniń bronlar fayli: bronlar dizimi mehmansız kórsetetuǵını (at, e-mail, telefon yamasa soraw joq)
BOOKINGS_EXPORT_HEADER = ['reference', 'hotel', 'status', 'payment_status', 'check_in', 'check_out', 'nights', 'rooms',
                          'guests', 'total', 'currency', 'booked_on', 'arrival_time', 'arrived']


def _bookings_export_row(booking):
    arrival = booking.expected_arrival_time
    return [
        booking.confirmation_code, booking.property.display_name(), booking.status, booking.payment_status,
        booking.check_in.isoformat(), booking.check_out.isoformat(), booking.number_of_nights,
        booking.number_of_rooms, booking.guest_count, booking.total_price, booking.currency,
        booking.created_at.astimezone(business_time_zone()).date().isoformat(),
        arrival.strftime('%H:%M') if arrival else '', 'yes' if booking.arrived_at else 'no',
    ]


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsHotelOwner])
def partner_bookings(request):
    """
    Mehmanxana iyesine tiyisli mehmanxanalardıń bronların dizimlew.

    Query parametrleri:
        status: Bron statusı boyınsha filter (ıqtıyarıy)
        payment_status: Tólem statusı boyınsha filter (ıqtıyarıy)
        reportable: true tek iye búgin no-show dep xabarlay alatuǵın bronlardı qaldıradı (ıqtıyarıy)
        export: csv yamasa xlsx sol dizimdi fayl retinde júklep aladı (mehmann maǵlıwmatısız), qarań BOOKINGS_EXPORT_HEADER

    Qaytaradı:
        Mehmanxana iyesiniń mehmanxanaları bronları dizimi
    """
    bookings = Booking.objects.filter(
        property__owner=request.user, is_deleted=False,
    ).select_related('property').prefetch_related('property__translations')

    # Filter lerdi qollanıw
    status_filter = request.query_params.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    payment_status_filter = request.query_params.get('payment_status')
    if payment_status_filter:
        bookings = bookings.filter(payment_status=payment_status_filter)

    today = business_today()
    reportable = reportable_bookings(bookings, today)
    if request.query_params.get('reportable') == 'true':
        bookings = reportable
    reportable_ids = set(reportable.values_list('id', flat=True))

    if wants_export(request):
        rows = (_bookings_export_row(booking) for booking in bookings.order_by('-check_in', '-id'))
        return export_response(request, 'partner_bookings', BOOKINGS_EXPORT_HEADER, rows)

    # Bronlardı serializer den ótkiziw
    bookings_data = []
    for booking in bookings:
        property_name = booking.property.display_name()

        booking_data = {
            'id': booking.id,
            'guest_name': booking.guest_full_name,
            'property_name': property_name,
            'status': booking.status,
            'payment_status': booking.payment_status,
            'check_in': booking.check_in,
            'check_out': booking.check_out,
            'number_of_nights': booking.number_of_nights,
            'guest_count': booking.guest_count,
            'total_price': str(booking.total_price),
            'currency': booking.currency,
            'confirmation_code': booking.confirmation_code,
            'created_at': booking.created_at,
            'expected_arrival_time': booking.expected_arrival_time,
            'arrived_at': booking.arrived_at,
            'can_report_no_show': booking.id in reportable_ids,
            'report_deadline': report_deadline(booking) if booking.id in reportable_ids else None,
        }
        bookings_data.append(booking_data)

    return Response(bookings_data, status=status.HTTP_200_OK)

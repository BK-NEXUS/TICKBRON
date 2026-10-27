"""
Views for partner API endpoints.

This module contains views for property, room, rate, and availability
management scoped to hotel-owner accounts.
"""
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
from django.db.models import Prefetch
from properties.models import (
    Property, RoomType, RatePlan, DateInventory, RoomInventory, RoomBlock, PropertyPhoto, RoomPhoto,
)
from bookings.arrival import mark_arrived
from bookings.models import Booking
from partner.models import OwnerPlace
from bookings.noshow import report_deadline, reportable_bookings
from common.dates import business_today
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
    Custom permission to ensure user is a hotel-owner.
    
    Checks if the authenticated user has the hotel-owner role or staff status.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        
        # Allow staff users (super-admin and admin)
        if request.user.is_staff:
            return True
        
        # Check if user has hotel-owner role
        if request.user.role and request.user.role.name == 'hotel-owner':
            return True
        
        return False


class PartnerAPIRootView(routers.APIRootView):
    """The router's endpoint index; the default one is open to any logged-in user."""
    permission_classes = [IsHotelOwner]


class PartnerPropertyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for property management by hotel-owners.
    
    Scoped to properties owned by the authenticated hotel-owner.
    """
    permission_classes = [IsHotelOwner]
    
    def get_queryset(self):
        """Filter queryset to properties owned by the authenticated user."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema generation: no user
            return self.get_serializer_class().Meta.model.objects.none()
        return Property.objects.filter(
            owner=self.request.user,
            is_deleted=False
        ).select_related('property_type').prefetch_related('translations')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return PartnerPropertyCreateSerializer
        return PartnerPropertySerializer
    
    def perform_create(self, serializer):
        """Ensure owner is set to authenticated user."""
        serializer.save(owner=self.request.user)


class PartnerRoomTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for room type management by hotel-owners.
    
    Scoped to room types in properties owned by the authenticated hotel-owner.
    """
    permission_classes = [IsHotelOwner]
    serializer_class = PartnerRoomTypeSerializer
    
    def get_queryset(self):
        """Filter queryset to room types in properties owned by the authenticated user."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema generation: no user
            return self.get_serializer_class().Meta.model.objects.none()
        live_photos = Prefetch(
            'photos', queryset=RoomPhoto.objects.filter(is_deleted=False, is_active=True).order_by('display_order', 'id'),
            to_attr='live_photos')
        return RoomType.objects.filter(
            property__owner=self.request.user,
            is_deleted=False
        ).select_related('property').prefetch_related(live_photos)


class PartnerRatePlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for rate plan management by hotel-owners.
    
    Scoped to rate plans in properties owned by the authenticated hotel-owner.
    """
    permission_classes = [IsHotelOwner]
    serializer_class = PartnerRatePlanSerializer
    
    def get_queryset(self):
        """Filter queryset to rate plans in properties owned by the authenticated user."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema generation: no user
            return self.get_serializer_class().Meta.model.objects.none()
        return RatePlan.objects.filter(
            room_type__property__owner=self.request.user,
            is_deleted=False
        ).select_related('room_type__property')


class PartnerDateInventoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for date inventory management by hotel-owners.
    
    Scoped to date inventory in properties owned by the authenticated hotel-owner.
    """
    permission_classes = [IsHotelOwner]
    serializer_class = PartnerDateInventorySerializer
    
    def get_queryset(self):
        """Filter queryset to date inventory in properties owned by the authenticated user."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema generation: no user
            return self.get_serializer_class().Meta.model.objects.none()
        queryset = DateInventory.objects.filter(
            rate_plan__room_type__property__owner=self.request.user,
            is_deleted=False
        ).select_related('rate_plan__room_type__property')
        if self.action == 'list':
            queryset = self._filter_list(queryset).order_by('date', 'id')
        return queryset

    def _filter_list(self, queryset):
        """
        Optional list filters: ?rate_plan=<id>&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
        (both dates inclusive). Invalid values are a 400, not a silently ignored filter.
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
            except ValueError:  # well formed but impossible, e.g. 2026-02-30
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
        3.7 bulk price edit: set one rate plan's nightly price over a date range.

        Body: {rate_plan, date_from, date_to, price}. date_to is exclusive, same
        convention as a booking's check_in/check_out (unlike this list's own date_from/
        date_to filters, which are inclusive). Creates any missing row (opened at the
        room type's full total_rooms); an existing row's other fields are untouched.
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
    ViewSet for room inventory (RoomInventory, audit #31) management by hotel-owners.

    Scoped to room inventory in properties owned by the authenticated hotel-owner. This
    is the room type's real, shared physical room count; DateInventory (see
    PartnerDateInventoryViewSet) still holds the price and each rate plan's own rules.
    """
    permission_classes = [IsHotelOwner]
    serializer_class = PartnerRoomInventorySerializer

    def get_queryset(self):
        """Filter queryset to room inventory in properties owned by the authenticated user."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema generation: no user
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
        Optional list filters: ?room_type=<id>&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
        (both dates inclusive). Invalid values are a 400, not a silently ignored filter.
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
            except ValueError:  # well formed but impossible, e.g. 2026-02-30
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
        3.6 calendar date-range edit: set available_rooms and/or is_available for one
        room type over a date range in one call.

        Body: {room_type, date_from, date_to, available_rooms?, is_available?} (at least
        one of the two). date_to is exclusive, same convention as a booking's
        check_in/check_out (unlike this list's own date_from/date_to filters, which are
        inclusive). Creates any missing, unmanaged row (opened at the room type's full
        total_rooms) first. 400 naming the date if available_rooms would drop a night
        below what is already booked on TICKBRON.
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
    ViewSet for external-booking blocks (RoomBlock, 3.5) by hotel-owners.

    Scoped to blocks on room types in properties owned by the authenticated hotel-owner.
    Creating one locks and decrements the affected RoomInventory rows
    (RoomBlock.create_block, via the serializer); deleting one restores them (release()).
    No PATCH/PUT: a block is created or undone (deleted), never edited in place.
    """
    permission_classes = [IsHotelOwner]
    serializer_class = PartnerBlockSerializer
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        """Filter queryset to blocks on room types in properties owned by the authenticated user."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema generation: no user
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
        """Deleting a block undoes it: restores the blocked rooms, then soft-deletes it."""
        instance.release()


def _owned_property(request, property_id):
    return get_object_or_404(Property, id=property_id, owner=request.user, is_deleted=False)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET', 'POST'])
@permission_classes([IsHotelOwner])
def partner_property_photos(request, property_id):
    """
    GET: the owner's photos of one property, cover and order as stored.
    POST: upload a photo (multipart: photo, photo_type, caption, alt_text).
    The first photo becomes the cover; new photos go to the end; the stored
    file name is random.
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
    PATCH: caption, alt_text, photo_type, is_primary=true (makes it the cover).
    DELETE: remove the photo; a removed cover passes to the first remaining photo.
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
    GET: the photos of one of the owner's room types, cover and order as stored.
    POST: upload a photo (multipart: photo, photo_type, caption, alt_text). The first photo becomes the cover; new
    photos go to the end; the stored file name is random; at most MAX_PHOTOS_PER_ROOM_TYPE per room type.
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
    PATCH: caption, alt_text, photo_type, is_primary=true (makes it the cover).
    DELETE: remove the photo; a removed cover passes to the first remaining photo.
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
    The hotel says the guest of one of its own bookings has arrived (cash at the hotel). Idempotent: the first
    time stays. Only a confirmed booking, from the check-in day on (400 otherwise).
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
    """The place the super admin gave this account: {country_ref, region_ref, city_ref}, all null when none."""
    place = OwnerPlace.objects.filter(owner=request.user).first()
    return Response({
        'country_ref': place.country_id if place else None,
        'region_ref': place.region_id if place else None,
        'city_ref': place.city_id if place else None,
    })


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsHotelOwner])
def partner_bookings(request):
    """
    List bookings for properties owned by the hotel-owner.
    
    Query Parameters:
        status: Filter by booking status (optional)
        payment_status: Filter by payment status (optional)
        reportable: true keeps only bookings the owner can report as no-show today (optional)
    
    Returns:
        List of bookings for the hotel-owner's properties
    """
    bookings = Booking.objects.filter(
        property__owner=request.user, is_deleted=False,
    ).select_related('property').prefetch_related('property__translations')

    # Apply filters
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

    # Serialize bookings
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

"""
Views for admin API endpoints.

This module contains views for property moderation, user management,
amenity management, and payment monitoring.
"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import routers, serializers, viewsets, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import (
    Count, Max, Q, F, OuterRef, Subquery, Value, Case, When, CharField
)
from django.db.models.functions import TruncMonth, ExtractYear, Coalesce, Concat, Lower, NullIf, Trim
from datetime import timedelta
from properties.listing import missing_for_listing
from properties.models import Property, Amenity, AmenityCategory
from users import two_factor
from users.models import User
from users.throttles import TwoFactorResetThrottle
from bookings.models import Booking
from admin_panel.audit import AuditedModelViewSetMixin
from accounts.notifications import notify
from admin_panel.models import AdminAccessLog, InternalNote
from common.request import object_body
from common.security_log import log_security_event
from admin_panel.serializers import (
    AdminPropertySerializer, AdminPropertyApproveSerializer, AdminPropertyRegionSerializer,
    AdminUserSerializer, AdminUserCreateSerializer, AdminStaffCreateSerializer, AdminContactSerializer,
    AdminAmenityCategorySerializer, AdminAmenitySerializer,
    AdminAmenityReadSerializer,
    AdminCustomerSerializer,
    AdminCustomerDetailSerializer,
    AdminBookingSummarySerializer,
    AdminInternalNoteSerializer,
    AdminInternalNoteCreateSerializer
)
from django.utils.translation import gettext as _


class IsSuperAdminOrStaff(IsAuthenticated):
    """
    Custom permission to ensure user is super-admin or staff.
    
    Super-admins have full access, staff have limited access.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        # Check if user is staff
        if request.user.is_staff:
            return True

        return False


class IsSuperAdmin(IsAuthenticated):
    """
    Custom permission to ensure user is super-admin.
    
    Only super-admins (is_superuser=True) can access these endpoints.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        # Check if user is superuser
        if request.user.is_superuser:
            return True

        return False


HOTEL_OWNER_ROLE = 'hotel-owner'


class AdminAPIRootView(routers.APIRootView):
    """The router's endpoint index; the default one is open to any logged-in user."""
    permission_classes = [IsSuperAdminOrStaff]


class AdminPropertyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for property moderation by admins.
    
    Read-only access to all properties for moderation purposes.
    """
    permission_classes = [IsSuperAdminOrStaff]
    serializer_class = AdminPropertySerializer

    def get_queryset(self):
        """Return all properties for moderation."""
        return Property.objects.filter(
            is_deleted=False
        ).select_related('owner', 'property_type', 'approved_by')


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdminOrStaff])
def admin_property_approve(request, property_id):
    """
    Approve a property for listing.
    
    Path Parameters:
        property_id: Property ID
    
    Request Body:
        rejection_reason: Reason for rejection (optional, only when rejecting)
    
    Returns:
        Updated property with approval status
    """
    property = get_object_or_404(Property, id=property_id, is_deleted=False)

    serializer = AdminPropertyApproveSerializer(data=request.data)

    if serializer.is_valid():
        rejection_reason = serializer.validated_data.get('rejection_reason', '')

        if rejection_reason:
            # Reject property
            property.status = 'rejected'
            property.rejection_reason = rejection_reason
            property.approved_by = None
            property.approved_at = None
        else:
            missing = missing_for_listing(property)
            if missing:
                return Response(
                    {'error': _('Property is not ready to be listed'), 'missing': missing},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            property.status = 'active'
            property.rejection_reason = ''
            property.approved_by = request.user
            property.approved_at = timezone.now()

        property.save()
        AdminAccessLog.record(
            request.user, 'property_reject' if rejection_reason else 'property_approve',
            details={'property_id': property.id},
        )

        return Response(
            AdminPropertySerializer(property).data,
            status=status.HTTP_200_OK
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['PATCH'])
@permission_classes([IsSuperAdminOrStaff])
def admin_property_region(request, property_id):
    """
    Set the location of a property (Status section: country > region > hotel).

    Request Body (either form):
        country_ref, region_ref, city_ref: Geography ids (all three null clears them)
        state: region name; blank or null clears it ("Unspecified"); older clients only

    Only the location changes; every other field in the body is ignored.
    """
    property = get_object_or_404(Property, id=property_id, is_deleted=False)
    serializer = AdminPropertyRegionSerializer(data=request.data, context={'property': property})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    refs = [name for name in ('country_ref', 'region_ref', 'city_ref') if name in data]
    if refs:
        for name in refs:
            setattr(property, name, data[name])
        if all(data.get(name) is None for name in refs) and len(refs) == 3:
            property.state = None
        # Property.save() copies the English names of the refs into country / state / city
        property.save()
    else:
        property.state = data['state']
        property.save(update_fields=['state', 'updated_at'])
    AdminAccessLog.record(request.user, 'property_region_update', details={'property_id': property.id})
    return Response(AdminPropertySerializer(property).data, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdminOrStaff])
def admin_property_suspend(request, property_id):
    """
    Suspend a property.
    
    Path Parameters:
        property_id: Property ID
    
    Returns:
        Updated property with suspended status
    """
    property = get_object_or_404(Property, id=property_id, is_deleted=False)

    property.status = 'suspended'
    property.save()
    AdminAccessLog.record(request.user, 'property_suspend', details={'property_id': property.id})

    return Response(
        AdminPropertySerializer(property).data,
        status=status.HTTP_200_OK
    )


class AdminUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user management by admins.
    
    Read-only access to all users for management purposes.
    """
    permission_classes = [IsSuperAdminOrStaff]
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        """Return all users for management."""
        return User.objects.filter(is_deleted=False).select_related('role')

    def list(self, request, *args, **kwargs):
        """Custom list method to handle both router and custom URL."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        AdminAccessLog.record(request.user, 'user_list')
        return Response(serializer.data)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def admin_create_hotel_owner(request):
    """
    Create a hotel-owner account (super-admin only).
    
    This endpoint allows super-admins to directly create hotel-owner accounts
    without self-registration. The account is created with the hotel-owner role
    and is immediately usable with the provided credentials.
    
    Request Body:
        email: Hotel owner email (required)
        first_name: First name (required)
        last_name: Last name (required)
        phone_number: Phone number (required)
        country_ref, region_ref, city_ref: the place of the owner's hotels (required, must fit together)
        password: Initial password (required, min 8 characters)
        password_confirm: Password confirmation (required)
    
    Returns:
        Created user object with hotel-owner role
    """
    serializer = AdminUserCreateSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
        AdminAccessLog.record(request.user, 'hotel_owner_create', target_user_id=user.id)
        return Response(
            AdminUserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def admin_create_admin(request):
    """
    Add another administrator (super-admin only). The new account is staff and never a super-admin;
    the request cannot change that. Body: email, first_name, last_name, phone_number, password,
    password_confirm. Written to the admin access log.
    """
    serializer = AdminStaffCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.save()
    AdminAccessLog.record(request.user, 'admin_create', target_user_id=user.id,
                          details={'role': serializer.validated_data['role']})
    return Response(AdminUserSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['PATCH'])
@permission_classes([IsSuperAdminOrStaff])
def admin_change_contact(request, user_id):
    """
    Change the phone number and/or e-mail of an account (super admin or staff). Body: phone_number, email.
    A staff admin may change guests and hotel owners; a super admin may also change staff admins. A super
    admin's contact data cannot be changed here. A new e-mail marks the account unverified and signs it out
    everywhere. Written to the admin access log (which fields, never the values).
    """
    target = get_object_or_404(User.objects.filter(is_deleted=False), pk=user_id)
    allowed_over_staff = request.user.is_superuser
    if target.is_superuser or (target.is_staff and not allowed_over_staff):
        return Response({'detail': _('You cannot change the contact details of this account.')},
                        status=status.HTTP_403_FORBIDDEN)
    serializer = AdminContactSerializer(data=object_body(request), account=target)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    changed = serializer.validated_data
    for field, value in changed.items():
        setattr(target, field, value)
    if 'email' in changed:
        target.email_verified = False
    target.save(update_fields=list(changed) + (['email_verified'] if 'email' in changed else []))
    if 'email' in changed:
        two_factor.end_sessions(target)
    AdminAccessLog.record(request.user, 'user_contact_update', target_user_id=target.id,
                          details={'fields': ','.join(sorted(changed))})
    return Response(AdminUserSerializer(target).data)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
@throttle_classes([TwoFactorResetThrottle])
def admin_reset_two_factor(request, user_id):
    """
    Reset another account's two-step sign-in after a lost phone (super-admin only). Body: code, the
    super admin's OWN current app code, so a stolen session alone cannot do it. The account is signed out
    everywhere and sets it up again at its next sign-in. A super admin's own two-step sign-in cannot be
    reset here: that is done on the server (`manage.py reset_2fa`). Written to the admin access log.
    """
    code = object_body(request).get('code')
    if not (request.user.two_factor_enabled and isinstance(code, str) and two_factor.accept_code(request.user, code)):
        return Response({'detail': _('Enter your own current two-step code.')}, status=status.HTTP_400_BAD_REQUEST)
    target = get_object_or_404(User.objects.filter(is_deleted=False), pk=user_id)
    if target.is_superuser:
        return Response(
            {'detail': _("A super admin's two-step sign-in can only be reset on the server.")},
            status=status.HTTP_403_FORBIDDEN)
    if not target.two_factor_enabled:
        return Response({'detail': _('Two-step sign-in is not on for this account.')}, status=status.HTTP_400_BAD_REQUEST)
    two_factor.reset(target)
    AdminAccessLog.record(request.user, 'two_factor_reset', target_user_id=target.id)
    notify(target, 'two_factor_reset', {})
    log_security_event('two_factor_reset', request, target=target.pk)
    return Response(AdminUserSerializer(target).data)


class AdminAmenityCategoryViewSet(AuditedModelViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for amenity category management by admins.
    
    Full CRUD access for amenity categories.
    """
    permission_classes = [IsSuperAdminOrStaff]
    serializer_class = AdminAmenityCategorySerializer
    audit_name = 'amenity_category'

    def get_queryset(self):
        """Return all amenity categories."""
        return AmenityCategory.objects.filter(is_deleted=False)


class AdminAmenityViewSet(AuditedModelViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for amenity management by admins.
    
    Full CRUD access for amenities.
    """
    permission_classes = [IsSuperAdminOrStaff]
    serializer_class = AdminAmenitySerializer
    audit_name = 'amenity'

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['list', 'retrieve']:
            # Use a serializer with nested category for read operations
            return AdminAmenityReadSerializer
        return AdminAmenitySerializer

    def get_queryset(self):
        """Return all amenities."""
        return Amenity.objects.filter(is_deleted=False).select_related('category')


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_booking_lookup_by_reference(request):
    """
    Look up a customer's full details and booking by reference code.
    
    This endpoint is for staff/support use when a guest reports a problem at the property
    and calls support with their booking reference code.
    
    Query Parameters:
        reference_code: 6-character booking reference code (required)
    
    Returns:
        Full booking details including:
        - Customer information (name, contact info)
        - Property and room details
        - Booking dates and status
        - Payment status
    """
    reference_code = request.query_params.get('reference_code')

    if not reference_code:
        return Response(
            {'error': 'reference_code parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Look up booking by reference code
    try:
        booking = Booking.objects.select_related(
            'guest', 'property', 'property__property_type', 'property__owner'
        ).prefetch_related(
            'booking_items__room_type', 'booking_items__rate_plan'
        ).get(
            confirmation_code=reference_code.upper(),
            is_deleted=False
        )
    except Booking.DoesNotExist:
        return Response(
            {'error': _('Booking not found with this reference code')},
            status=status.HTTP_404_NOT_FOUND
        )

    # Build comprehensive response
    booking_items_data = []
    for item in booking.booking_items.all():
        booking_items_data.append({
            'room_type': {
                'id': item.room_type.id,
                'name': item.room_type.name,
                'description': item.room_type.description,
                'base_occupancy': item.room_type.base_occupancy,
                'max_occupancy': item.room_type.max_occupancy,
            },
            'rate_plan': {
                'id': item.rate_plan.id,
                'name': item.rate_plan.name,
                'rate_type': item.rate_plan.rate_type,
                'description': item.rate_plan.description,
            },
            'number_of_rooms': item.number_of_rooms,
            'price_per_night': str(item.price_per_night),
            'currency': item.currency,
        })

    response_data = {
        'booking': {
            'id': booking.id,
            'reference_code': booking.confirmation_code,
            'status': booking.status,
            'payment_status': booking.payment_status,
            'check_in': booking.check_in,
            'check_out': booking.check_out,
            'number_of_nights': booking.number_of_nights,
            'guest_count': booking.guest_count,
            'total_price': str(booking.total_price),
            'currency': booking.currency,
            'special_requests': booking.special_requests,
            'cancelled_at': booking.cancelled_at,
            'cancellation_reason': booking.cancellation_reason,
            'expires_at': booking.expires_at,
            'created_at': booking.created_at,
            'updated_at': booking.updated_at,
            'guest_full_name': booking.guest_full_name,
            'guest_phone': booking.guest_phone,
            'guest_email': booking.guest_email,
            'number_of_rooms': booking.number_of_rooms,
            'children': booking.children,
            'booking_items': booking_items_data,
        },
        'customer': {
            'id': booking.guest.id,
            'full_name': booking.guest.get_full_name(),
            'email': booking.guest.email,
            'phone_number': booking.guest.phone_number,
            'whatsapp': booking.guest.whatsapp,
            'telegram': booking.guest.telegram,
            'preferred_contact_method': booking.guest.preferred_contact_method,
        },
        'property': {
            'id': booking.property.id,
            'name': booking.property.display_name(),
            'property_type': booking.property.property_type.name if booking.property.property_type else None,
            'status': booking.property.status,
            'address_line1': booking.property.address_line1,
            'city': booking.property.city,
            'state': booking.property.state,
            'country': booking.property.country,
            'base_price': str(booking.property.base_price),
            'currency': booking.property.currency,
            'owner': {
                'id': booking.property.owner.id,
                'full_name': booking.property.owner.get_full_name(),
                'email': booking.property.owner.email,
            } if booking.property.owner else None,
        },
    }

    AdminAccessLog.record(
        request.user, 'booking_lookup', target_user_id=booking.guest_id, target_booking_id=booking.id,
    )
    return Response(response_data, status=status.HTTP_200_OK)


class AdminCustomerPagination(PageNumberPagination):
    """
    Custom pagination for admin customers directory.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT, operation_id='v1_admin_panel_customers_list')
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_customers_directory(request):
    """
    Admin API for customers directory with booking aggregates.
    
    Returns for each customer:
    - customer ID, registration date, full name, phone, email, whatsapp, telegram, preferred contact method
    - total booking count, last booking date, total amount paid, customer status
    
    Query Parameters:
        search: Search by name, phone, email, or customer ID (optional)
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)
        sort_by: Sort field (default: registration_date)
        sort_order: Sort order (asc or desc, default: desc)
    
    Returns:
        Paginated list of customers with booking aggregates
    """
    # Get query parameters
    search = request.query_params.get('search', '').strip()
    page = request.query_params.get('page', 1)
    sort_by = request.query_params.get('sort_by', 'registration_date')
    sort_order = request.query_params.get('sort_order', 'desc')

    # Validate sort_order
    if sort_order not in ['asc', 'desc']:
        sort_order = 'desc'

    # Validate sort_by field
    valid_sort_fields = [
        'registration_date', 'full_name', 'email', 'total_booking_count',
        'last_booking_date', 'customer_status'
    ]
    if sort_by not in valid_sort_fields:
        sort_by = 'registration_date'

    # Aggregates come from correlated subqueries, so one customer is never counted twice
    customer_bookings = Booking.objects.filter(
        guest=OuterRef('pk'), is_deleted=False
    ).order_by().values('guest')

    # Active: is_active=True and (has booking in last 90 days OR no bookings yet)
    # Inactive: is_active=False OR (is_active=True and last booking > 90 days ago)
    threshold_date = timezone.now() - timedelta(days=90)

    # Staff, super-admins and hotel owners are not customers
    users = User.objects.filter(
        is_deleted=False, is_staff=False, is_superuser=False
    ).exclude(role__name=HOTEL_OWNER_ROLE).annotate(
        total_booking_count=Coalesce(
            Subquery(customer_bookings.annotate(c=Count('id')).values('c')), 0
        ),
        last_booking_date=Subquery(customer_bookings.annotate(m=Max('created_at')).values('m')),
        # Same fallback as User.get_full_name(): full_name, else first + last, else email
        display_name=Coalesce(
            NullIf('full_name', Value('')),
            NullIf(Trim(Concat('first_name', Value(' '), 'last_name')), Value('')),
            'email',
            output_field=CharField(),
        ),
    ).annotate(
        customer_status=Case(
            When(is_active=False, then=Value('inactive')),
            When(last_booking_date__lt=threshold_date, then=Value('inactive')),
            default=Value('active'),
            output_field=CharField(),
        ),
    )

    # Apply search filter
    if search:
        users = users.filter(
            Q(full_name__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone_number__icontains=search) |
            Q(email__icontains=search) |
            Q(id__icontains=search)
        )

    # Sort in the database; id breaks ties so pages are stable
    sort_expressions = {
        'registration_date': F('date_joined'),
        'full_name': Lower('display_name'),
        'email': F('email'),
        'total_booking_count': F('total_booking_count'),
        'last_booking_date': F('last_booking_date'),
        'customer_status': F('customer_status'),
    }
    sort_expression = sort_expressions[sort_by]
    if sort_order == 'asc':
        users = users.order_by(sort_expression.asc(nulls_last=True), 'id')
    else:
        users = users.order_by(sort_expression.desc(nulls_last=True), '-id')

    # Paginate the queryset, so only one page of users is loaded
    paginator = AdminCustomerPagination()
    page = paginator.paginate_queryset(users, request)

    paginated_data = [
        {
            'id': user.id,
            'registration_date': user.date_joined,
            'full_name': user.get_full_name(),
            'phone': user.phone_number,
            'email': user.email,
            'whatsapp': user.whatsapp,
            'telegram': user.telegram,
            'preferred_contact_method': user.preferred_contact_method,
            'total_booking_count': user.total_booking_count,
            'last_booking_date': user.last_booking_date,
            'customer_status': user.customer_status,
        }
        for user in page
    ]

    # Serialize paginated data
    serializer = AdminCustomerSerializer(paginated_data, many=True)

    AdminAccessLog.record(request.user, 'customer_list')
    return paginator.get_paginated_response(serializer.data)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_customer_detail(request, customer_id):
    """
    Admin API for a single customer's full profile.
    
    Returns:
    - Contact information (full profile)
    - All bookings filterable by all/upcoming/completed/cancelled
    - Last activity timestamp
    - Internal notes (staff-only)
    
    Query Parameters:
        booking_filter: Filter bookings by status (all, upcoming, completed, cancelled)
    
    Path Parameters:
        customer_id: Customer ID
    """
    # Get customer
    customer = get_object_or_404(User, id=customer_id, is_deleted=False)

    # Get booking filter
    booking_filter = request.query_params.get('booking_filter', 'all')

    # Build bookings query
    bookings = Booking.objects.filter(
        guest=customer,
        is_deleted=False
    ).select_related('property').order_by('-created_at')

    # Apply booking filter
    if booking_filter == 'upcoming':
        bookings = bookings.filter(
            status='confirmed',
            check_in__gte=timezone.now().date()
        )
    elif booking_filter == 'completed':
        bookings = bookings.filter(status='completed')
    elif booking_filter == 'cancelled':
        bookings = bookings.filter(status='cancelled')
    # 'all' returns all bookings

    # Serialize bookings
    bookings_data = []
    for booking in bookings:
        bookings_data.append({
            'id': booking.id,
            'reference_code': booking.confirmation_code,
            'status': booking.status,
            'payment_status': booking.payment_status,
            'check_in': booking.check_in,
            'check_out': booking.check_out,
            'number_of_nights': booking.number_of_nights,
            'total_price': str(booking.total_price),
            'currency': booking.currency,
            'property_name': booking.property.display_name(),
            'property_city': booking.property.city,
            'created_at': booking.created_at
        })

    bookings_serializer = AdminBookingSummarySerializer(bookings_data, many=True)

    # Get internal notes
    internal_notes = InternalNote.objects.filter(
        customer=customer,
        is_deleted=False
    ).select_related('author').order_by('-created_at')

    internal_notes_serializer = AdminInternalNoteSerializer(internal_notes, many=True)

    # Calculate last activity timestamp
    # Last activity is the most recent of: last_login, last booking created_at
    last_activities = []
    if customer.last_login:
        last_activities.append(customer.last_login)
    if bookings.exists():
        last_activities.append(bookings.first().created_at)

    last_activity = max(last_activities) if last_activities else None

    # Build response
    response_data = {
        'customer': AdminCustomerDetailSerializer(customer).data,
        'bookings': bookings_serializer.data,
        'internal_notes': internal_notes_serializer.data,
        'last_activity': last_activity
    }

    AdminAccessLog.record(request.user, 'customer_view', target_user_id=customer.id)
    return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdminOrStaff])
def admin_internal_note_create(request, customer_id):
    """
    Create an internal note for a customer.
    
    Path Parameters:
        customer_id: Customer ID
    
    Request Body:
        note: Note content (required)
    
    Returns:
        Created internal note
    """
    customer = get_object_or_404(User, id=customer_id, is_deleted=False)

    serializer = AdminInternalNoteCreateSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        note = serializer.save(customer=customer)
        AdminAccessLog.record(request.user, 'internal_note_create', target_user_id=customer.id,
                              details={'object_id': note.id})
        return Response(
            AdminInternalNoteSerializer(note).data,
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['PUT', 'DELETE'])
@permission_classes([IsSuperAdminOrStaff])
def admin_internal_note_detail(request, customer_id, note_id):
    """
    Update or delete an internal note.
    
    Path Parameters:
        customer_id: Customer ID
        note_id: Note ID
    
    Request Body (for PUT):
        note: Updated note content (required)
    
    Returns:
        Updated note (for PUT) or 204 No Content (for DELETE)
    """
    customer = get_object_or_404(User, id=customer_id, is_deleted=False)
    note = get_object_or_404(
        InternalNote,
        id=note_id,
        customer=customer,
        is_deleted=False
    )

    if request.method == 'PUT':
        serializer = AdminInternalNoteSerializer(note, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            AdminAccessLog.record(request.user, 'internal_note_update', target_user_id=customer.id,
                                  details={'object_id': note.id})
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        note.soft_delete()
        AdminAccessLog.record(request.user, 'internal_note_delete', target_user_id=customer.id,
                              details={'object_id': note.id})
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_registration_statistics(request):
    """
    Admin API for registration statistics.
    
    Returns new-registration counts broken down by:
    - Rolling 12-month window (month-by-month)
    - Calendar year (year-by-year)
    
    Query Parameters:
        type: Type of breakdown (rolling_12_months or calendar_year, default: rolling_12_months)
    
    Returns:
        Registration statistics with counts and period labels
    """
    stats_type = request.query_params.get('type', 'rolling_12_months')

    if stats_type == 'calendar_year':
        # Get registration counts by calendar year
        yearly_stats = User.objects.filter(
            is_deleted=False
        ).annotate(
            year=ExtractYear('date_joined')
        ).values('year').annotate(
            count=Count('id')
        ).order_by('year')

        # Format response
        stats_data = [
            {
                'period': str(item['year']),
                'count': item['count']
            }
            for item in yearly_stats
        ]

        return Response({
            'type': 'calendar_year',
            'statistics': stats_data
        }, status=status.HTTP_200_OK)

    else:  # rolling_12_months (default)
        # Get rolling 12-month window
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)

        # Get registration counts by month for the rolling window
        monthly_stats = User.objects.filter(
            is_deleted=False,
            date_joined__gte=start_date,
            date_joined__lte=end_date
        ).annotate(
            month=TruncMonth('date_joined')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')

        # Format response with month labels
        stats_data = []
        for item in monthly_stats:
            month_date = item['month']
            stats_data.append({
                'period': month_date.strftime('%Y-%m'),
                'count': item['count']
            })

        return Response({
            'type': 'rolling_12_months',
            'start_date': start_date,
            'end_date': end_date,
            'statistics': stats_data
        }, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_top_bookers_leaderboard(request):
    """
    Admin API for top-bookers leaderboard.
    
    Returns customers ranked by number of completed bookings within a selectable period.
    Intended to support customer-reward/loyalty programs.
    
    Query Parameters:
        period: Time period for the leaderboard (this_month, this_year, all_time, default: all_time)
        limit: Maximum number of top bookers to return (default: 10, max: 100)
    
    Returns:
        Leaderboard with customer name, booking count, and rank
    """
    period = request.query_params.get('period', 'all_time')
    limit = request.query_params.get('limit', 10)

    # Validate and sanitize limit
    try:
        limit = int(limit)
        if limit < 1:
            limit = 10
        elif limit > 100:
            limit = 100
    except (ValueError, TypeError):
        limit = 10

    # Build date filter based on period
    now = timezone.now()

    if period == 'this_month':
        # First day of current month
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        booking_filter = Q(
            bookings__is_deleted=False,
            bookings__status='completed',
            bookings__created_at__gte=start_date
        )
    elif period == 'this_year':
        # First day of current year
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        booking_filter = Q(
            bookings__is_deleted=False,
            bookings__status='completed',
            bookings__created_at__gte=start_date
        )
    else:  # 'all_time' has no date filter
        booking_filter = Q(
            bookings__is_deleted=False,
            bookings__status='completed'
        )

    # Get top bookers with completed booking counts
    top_bookers = User.objects.filter(
        is_deleted=False
    ).annotate(
        completed_booking_count=Count('bookings', filter=booking_filter)
    ).filter(
        completed_booking_count__gt=0
    ).order_by('-completed_booking_count')[:limit]

    # Build leaderboard response
    leaderboard_data = []
    for rank, user in enumerate(top_bookers, start=1):
        leaderboard_data.append({
            'rank': rank,
            'customer_id': user.id,
            'customer_name': user.get_full_name(),
            'completed_booking_count': user.completed_booking_count
        })

    return Response({
        'period': period,
        'limit': limit,
        'leaderboard': leaderboard_data
    }, status=status.HTTP_200_OK)


class AdminAccessLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminAccessLog
        fields = ['id', 'actor_id', 'action', 'target_user_id', 'target_booking_id', 'details', 'created_at']
        read_only_fields = fields


class AdminAccessLogPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_access_log(request):
    """
    Staff-only, read-only view of AdminAccessLog, newest first.

    Filters: actor_id, target_user_id, target_booking_id (integers), action.
    Reading this log is not itself recorded (it holds ids only, no customer data).
    """
    entries = AdminAccessLog.objects.all()
    for name in ('actor_id', 'target_user_id', 'target_booking_id'):
        value = request.query_params.get(name)
        if value:
            if not value.isdigit():
                return Response({'error': f'{name} must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
            entries = entries.filter(**{name: int(value)})
    action = request.query_params.get('action')
    if action:
        entries = entries.filter(action=action)

    paginator = AdminAccessLogPagination()
    page = paginator.paginate_queryset(entries, request)
    return paginator.get_paginated_response(AdminAccessLogSerializer(page, many=True).data)

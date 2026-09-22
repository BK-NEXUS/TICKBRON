"""
Views for admin API endpoints.

This module contains views for property moderation, user management,
amenity management, and payment monitoring.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Sum, Max, Q
from datetime import timedelta
from properties.models import Property, Amenity, AmenityCategory
from users.models import User
from payments.models import PaymentTransaction
from bookings.models import Booking, BookingItem
from admin_panel.serializers import (
    AdminPropertySerializer, AdminPropertyApproveSerializer,
    AdminUserSerializer, AdminUserCreateSerializer,
    AdminAmenityCategorySerializer, AdminAmenitySerializer,
    AdminAmenityReadSerializer,
    AdminPaymentTransactionSerializer,
    AdminCustomerSerializer
)


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
            # Approve property
            property.status = 'active'
            property.rejection_reason = ''
            property.approved_by = request.user
            property.approved_at = timezone.now()
        
        property.save()
        
        return Response(
            AdminPropertySerializer(property).data,
            status=status.HTTP_200_OK
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        return Response(serializer.data)


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
        phone_number: Phone number (optional)
        password: Initial password (required, min 12 characters)
        password_confirm: Password confirmation (required)
    
    Returns:
        Created user object with hotel-owner role
    """
    serializer = AdminUserCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            AdminUserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminAmenityCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for amenity category management by admins.
    
    Full CRUD access for amenity categories.
    """
    permission_classes = [IsSuperAdminOrStaff]
    serializer_class = AdminAmenityCategorySerializer
    
    def get_queryset(self):
        """Return all amenity categories."""
        return AmenityCategory.objects.filter(is_deleted=False)


class AdminAmenityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for amenity management by admins.
    
    Full CRUD access for amenities.
    """
    permission_classes = [IsSuperAdminOrStaff]
    serializer_class = AdminAmenitySerializer
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['list', 'retrieve']:
            # Use a serializer with nested category for read operations
            return AdminAmenityReadSerializer
        return AdminAmenitySerializer
    
    def get_queryset(self):
        """Return all amenities."""
        return Amenity.objects.filter(is_deleted=False).select_related('category')


@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_payment_transactions(request):
    """
    List payment transactions for admin monitoring.
    
    Query Parameters:
        status: Filter by transaction status (optional)
        provider: Filter by payment provider (optional)
    
    Returns:
        List of payment transactions for monitoring
    """
    transactions = PaymentTransaction.objects.filter(
        is_deleted=False
    ).select_related('booking')
    
    # Apply filters
    status_filter = request.query_params.get('status')
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    provider_filter = request.query_params.get('provider')
    if provider_filter:
        transactions = transactions.filter(provider=provider_filter)
    
    # Serialize transactions
    transactions_data = []
    for transaction in transactions:
        transaction_data = {
            'id': transaction.id,
            'booking_id': transaction.booking.id if transaction.booking else None,
            'provider': transaction.provider,
            'amount': str(transaction.amount),
            'currency': transaction.currency,
            'status': transaction.status,
            'created_at': transaction.created_at,
            'updated_at': transaction.updated_at
        }
        transactions_data.append(transaction_data)
    
    return Response(transactions_data, status=status.HTTP_200_OK)


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
            {'error': 'Booking not found with this reference code'},
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
            'name': booking.property.name,
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
    
    return Response(response_data, status=status.HTTP_200_OK)


class AdminCustomerPagination(PageNumberPagination):
    """
    Custom pagination for admin customers directory.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


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
    page_size = request.query_params.get('page_size', 20)
    sort_by = request.query_params.get('sort_by', 'registration_date')
    sort_order = request.query_params.get('sort_order', 'desc')
    
    # Validate sort_order
    if sort_order not in ['asc', 'desc']:
        sort_order = 'desc'
    
    # Validate sort_by field
    valid_sort_fields = [
        'registration_date', 'full_name', 'email', 'total_booking_count',
        'last_booking_date', 'total_amount_paid', 'customer_status'
    ]
    if sort_by not in valid_sort_fields:
        sort_by = 'registration_date'
    
    # Build sort string
    sort_prefix = '' if sort_order == 'asc' else '-'
    sort_string = f'{sort_prefix}{sort_by}'
    
    # Annotate users with booking aggregates
    users = User.objects.filter(is_deleted=False).annotate(
        total_booking_count=Count('bookings', filter=Q(bookings__is_deleted=False)),
        last_booking_date=Max('bookings__created_at', filter=Q(bookings__is_deleted=False)),
        total_amount_paid=Sum(
            'bookings__payment_transactions__amount',
            filter=Q(
                bookings__is_deleted=False,
                bookings__payment_transactions__status='completed'
            )
        )
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
    
    # Calculate customer status
    # Active: is_active=True and (has booking in last 90 days OR no bookings yet)
    # Inactive: is_active=False OR (is_active=True and last booking > 90 days ago)
    threshold_date = timezone.now() - timedelta(days=90)
    
    customers_data = []
    for user in users:
        # Determine customer status
        if not user.is_active:
            customer_status = 'inactive'
        elif user.last_booking_date and user.last_booking_date < threshold_date:
            customer_status = 'inactive'
        else:
            customer_status = 'active'
        
        customer_data = {
            'id': user.id,
            'registration_date': user.date_joined,
            'full_name': user.get_full_name(),
            'phone': user.phone_number,
            'email': user.email,
            'whatsapp': user.whatsapp,
            'telegram': user.telegram,
            'preferred_contact_method': user.preferred_contact_method,
            'total_booking_count': user.total_booking_count or 0,
            'last_booking_date': user.last_booking_date,
            'total_amount_paid': user.total_amount_paid or 0,
            'customer_status': customer_status
        }
        customers_data.append(customer_data)
    
    # Sort the results
    if sort_by == 'registration_date':
        customers_data.sort(key=lambda x: x['registration_date'], reverse=(sort_order == 'desc'))
    elif sort_by == 'full_name':
        customers_data.sort(key=lambda x: x['full_name'] or '', reverse=(sort_order == 'desc'))
    elif sort_by == 'email':
        customers_data.sort(key=lambda x: x['email'], reverse=(sort_order == 'desc'))
    elif sort_by == 'total_booking_count':
        customers_data.sort(key=lambda x: x['total_booking_count'], reverse=(sort_order == 'desc'))
    elif sort_by == 'last_booking_date':
        # Handle None values - put them last
        customers_data.sort(
            key=lambda x: (x['last_booking_date'] is None, x['last_booking_date'] or timezone.now()),
            reverse=(sort_order == 'desc')
        )
    elif sort_by == 'total_amount_paid':
        customers_data.sort(key=lambda x: x['total_amount_paid'], reverse=(sort_order == 'desc'))
    elif sort_by == 'customer_status':
        customers_data.sort(key=lambda x: x['customer_status'], reverse=(sort_order == 'desc'))
    
    # Apply pagination
    paginator = AdminCustomerPagination()
    paginated_data = paginator.paginate_queryset(customers_data, request)
    
    # Serialize paginated data
    serializer = AdminCustomerSerializer(paginated_data, many=True)
    
    return paginator.get_paginated_response(serializer.data)

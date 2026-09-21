"""
Views for admin API endpoints.

This module contains views for property moderation, user management,
amenity management, and payment monitoring.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from properties.models import Property, Amenity, AmenityCategory
from users.models import User
from payments.models import PaymentTransaction
from admin_panel.serializers import (
    AdminPropertySerializer, AdminPropertyApproveSerializer,
    AdminUserSerializer, AdminUserCreateSerializer,
    AdminAmenityCategorySerializer, AdminAmenitySerializer,
    AdminAmenityReadSerializer,
    AdminPaymentTransactionSerializer
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

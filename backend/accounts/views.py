"""
Views for the accounts app.

This module contains views for favorites, reviews, notifications, and account history.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, Count, Avg, Prefetch
from .models import Favorite, Review, Notification, AccountHistory
from .serializers import (
    FavoriteSerializer, FavoriteCreateSerializer,
    ReviewSerializer, ReviewCreateSerializer,
    NotificationSerializer, NotificationUpdateSerializer,
    AccountHistorySerializer, AccountHistoryCreateSerializer
)
from properties.models import Property, PropertyPhoto
from bookings.models import Booking


class FavoriteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user favorites.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return favorites for the current user."""
        return Favorite.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).select_related('property')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return FavoriteCreateSerializer
        return FavoriteSerializer
    
    def perform_create(self, serializer):
        """Create favorite for the current user."""
        serializer.save(user=self.request.user)
        
        # Log account history
        property_obj = serializer.validated_data.get('property')
        AccountHistory.objects.create(
            user=self.request.user,
            action='favorite_added',
            description=f"Added property in {property_obj.city if property_obj else 'unknown'} to favorites",
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            property=property_obj
        )
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete favorite."""
        instance = self.get_object()
        instance.soft_delete()
        
        # Log account history
        AccountHistory.objects.create(
            user=request.user,
            action='favorite_removed',
            description=f"Removed property in {instance.property.city} from favorites",
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            property=instance.property
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def count(self, request):
        """Get total count of user favorites."""
        count = self.get_queryset().count()
        return Response({'count': count})


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing property reviews.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return reviews based on user role."""
        user = self.request.user
        
        # Regular users can only see their own reviews
        if not user.is_staff:
            return Review.objects.filter(
                user=user,
                is_deleted=False
            ).select_related('user', 'property', 'booking')
        
        # Staff can see all reviews
        return Review.objects.filter(
            is_deleted=False
        ).select_related('user', 'property', 'booking')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ReviewCreateSerializer
        return ReviewSerializer
    
    def perform_create(self, serializer):
        """Create review for the current user."""
        serializer.save(user=self.request.user, status='pending')
        
        # Log account history
        property_obj = serializer.validated_data.get('property')
        AccountHistory.objects.create(
            user=self.request.user,
            action='review_submitted',
            description=f"Submitted review for property in {property_obj.city if property_obj else 'unknown'}",
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            property=property_obj,
            booking=serializer.validated_data.get('booking')
        )
    
    @action(detail=False, methods=['get'])
    def eligible_properties(self, request):
        """
        Get properties the user is eligible to review.
        
        Users can review properties they have completed bookings for and haven't reviewed yet.
        """
        user = request.user
        
        # Get completed bookings without reviews
        completed_bookings = Booking.objects.filter(
            guest=user,
            status='completed',
            is_deleted=False
        ).select_related('property')
        
        # Get properties already reviewed
        reviewed_properties = Review.objects.filter(
            user=user,
            is_deleted=False
        ).values_list('property_id', flat=True)
        
        # Get eligible properties
        eligible_properties = []
        for booking in completed_bookings:
            if booking.property_id not in reviewed_properties:
                eligible_properties.append({
                    'property_id': booking.property_id,
                    'property_city': booking.property.city,
                    'property_country': booking.property.country,
                    'booking_id': booking.id,
                    'confirmation_code': booking.confirmation_code,
                    'check_in': booking.check_in,
                    'check_out': booking.check_out
                })
        
        return Response({'eligible_properties': eligible_properties})
    
    @action(detail=False, methods=['get'])
    def property_scores(self, request):
        """
        Get review scores for a specific property.
        
        Returns average ratings across different categories for a property.
        """
        property_id = request.query_params.get('property_id')
        
        if not property_id:
            return Response(
                {'detail': 'property_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get approved reviews for the property
        reviews = Review.objects.filter(
            property_id=property_id,
            status='approved',
            is_deleted=False
        )
        
        if not reviews.exists():
            return Response({
                'property_id': property_id,
                'total_reviews': 0,
                'average_rating': None,
                'category_scores': {}
            })
        
        # Calculate average ratings
        avg_overall = reviews.aggregate(avg_rating=Avg('overall_rating'))['avg_rating']
        
        category_scores = {}
        rating_fields = ['cleanliness_rating', 'location_rating', 'value_rating', 
                        'amenities_rating', 'service_rating']
        
        for field in rating_fields:
            avg = reviews.aggregate(avg=Avg(field))['avg']
            if avg is not None:
                category_scores[field] = round(avg, 1)
        
        return Response({
            'property_id': property_id,
            'total_reviews': reviews.count(),
            'average_rating': round(avg_overall, 1) if avg_overall else None,
            'category_scores': category_scores
        })


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notifications.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications for the current user."""
        return Notification.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).select_related('booking', 'property')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['update', 'partial_update']:
            return NotificationUpdateSerializer
        return NotificationSerializer
    
    def create(self, request, *args, **kwargs):
        """Prevent direct creation of notifications through API."""
        return Response(
            {'detail': 'Notifications cannot be created directly through API.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    def perform_update(self, serializer):
        """Update notification."""
        if 'is_read' in serializer.validated_data:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications for the current user."""
        unread = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(unread, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read for the current user."""
        count = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'marked_as_read': count})
    
    @action(detail=False, methods=['get'])
    def count(self, request):
        """Get notification counts for the current user."""
        total = self.get_queryset().count()
        unread = self.get_queryset().filter(is_read=False).count()
        
        return Response({
            'total': total,
            'unread': unread,
            'read': total - unread
        })


class AccountHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing user account history.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return account history for the current user."""
        return AccountHistory.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).select_related('booking', 'property')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        return AccountHistorySerializer
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent account history entries."""
        limit = min(int(request.query_params.get('limit', 10)), 50)
        recent = self.get_queryset()[:limit]
        serializer = self.get_serializer(recent, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get account activity statistics."""
        queryset = self.get_queryset()
        
        # Count by action type
        action_counts = queryset.values('action').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'total_entries': queryset.count(),
            'action_counts': list(action_counts)
        })


def get_client_ip(request):
    """
    Get the client's IP address from the request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

"""
accounts app ınıń view leri.

Bul modul favorit ler, sharhlar, bildiriwler hám akkaunt tariyxı view lerin óz ishine aladı.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.db.models import Count, Avg, Prefetch
from .models import Favorite, Review, Notification, AccountHistory
from .serializers import (
    FavoriteSerializer, FavoriteCreateSerializer,
    ReviewSerializer, ReviewCreateSerializer, ReviewUpdateSerializer, PublicReviewSerializer,
    NotificationSerializer, NotificationUpdateSerializer,
    AccountHistorySerializer
)
from properties.models import Property, PropertyPhoto, PropertyTranslation
from properties.search import card_prices_prefetch
from bookings.models import Booking
from common.request import get_client_ip
from django.utils.translation import gettext as _


class FavoriteViewSet(viewsets.ModelViewSet):
    """
    Paydalanıwshı favorit lerin basqarıw ushın ViewSet.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Házirgi paydalanıwshınıń favorit lerin qaytaradı."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema jasaw: paydalanıwshı joq
            return self.get_serializer_class().Meta.model.objects.none()
        return Favorite.objects.filter(
            user=self.request.user,
            is_deleted=False,
            property__status='active',
        ).select_related('property').prefetch_related(
            Prefetch(
                'property__translations',
                queryset=PropertyTranslation.objects.filter(is_deleted=False),
            ),
            Prefetch(
                'property__photos', to_attr='primary_photos',
                queryset=PropertyPhoto.objects.filter(is_primary=True, is_deleted=False),
            ),
            card_prices_prefetch('property__'),
        )

    def get_serializer_class(self):
        """Háreketke qarap tiyisli serializer di qaytaradı."""
        if self.action == 'create':
            return FavoriteCreateSerializer
        return FavoriteSerializer

    def perform_create(self, serializer):
        """
        Házirgi paydalanıwshı ushın favorit jaratadı.

        (user, property) boyınsha unique_together is_deleted di bilmeydi, sol sebepli
        sol mehmanxana ushın burın óshirilgen (soft-deleted) favorit bar bolsa, ápiwayı create()
        IntegrityError sebepli 500 beredi. Onıń ornına sonı qayta tiklaymız.
        """
        property_obj = serializer.validated_data.get('property')
        existing = Favorite.objects.filter(user=self.request.user, property=property_obj).first()

        if existing is not None:
            if not existing.is_deleted:
                raise ValidationError({'non_field_errors': _('This property is already in your favorites.')})
            existing.is_deleted = False
            existing.deleted_at = None
            existing.notes = serializer.validated_data.get('notes', existing.notes)
            existing.save()
            serializer.instance = existing
        else:
            serializer.save(user=self.request.user)

        # Akkaunt tariyxına jazıw
        AccountHistory.objects.create(
            user=self.request.user,
            action='favorite_added',
            description=f"Added property in {property_obj.city if property_obj else 'unknown'} to favorites",
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            property=property_obj
        )

    def destroy(self, request, *args, **kwargs):
        """Favorittı soft delete etedi."""
        instance = self.get_object()
        instance.soft_delete()

        # Akkaunt tariyxına jazıw
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
        """Paydalanıwshı favorit leriniń ulıwma sanın qaytaradı."""
        count = self.get_queryset().count()
        return Response({'count': count})


class ReviewViewSet(viewsets.ModelViewSet):
    """
    Mehmanxana sharhların basqarıw ushın ViewSet.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Paydalanıwshı roline qarap sharhlardı qaytaradı."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema jasaw: paydalanıwshı joq
            return self.get_serializer_class().Meta.model.objects.none()
        user = self.request.user

        # Ápiwayı paydalanıwshılar tek óz sharhların kóre aladı
        if not user.is_staff:
            return Review.objects.filter(
                user=user,
                is_deleted=False
            ).select_related('user', 'property', 'booking')

        # Staff barlıq sharhlardı kóre aladı
        return Review.objects.filter(
            is_deleted=False
        ).select_related('user', 'property', 'booking')

    def get_serializer_class(self):
        """Háreketke qarap tiyisli serializer di qaytaradı."""
        if self.action == 'create':
            return ReviewCreateSerializer
        if self.action in ['update', 'partial_update']:
            return ReviewUpdateSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        """Házirgi paydalanıwshı ushın sharh jaratadı."""
        try:
            with transaction.atomic():
                serializer.save(user=self.request.user, status='pending')
        except IntegrityError:
            # Tekseriwden keyin basqa bir sorawdıń bir bronǵa sharh jazıp úlgergeni
            raise ValidationError({'booking': [_("This booking has already been reviewed.")]})

        # Akkaunt tariyxına jazıw
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

    def perform_update(self, serializer):
        """Ózgertilgen sharhtı qaytadan moderation ǵa jiberedi, sonda tekserilmegen tekst tastıyıqlanǵan dep kórsetilmeydi."""
        serializer.save(status='pending', reviewed_at=None)

    @action(detail=False, methods=['get'])
    def eligible_properties(self, request):
        """
        Paydalanıwshı sharh jaza alatuǵın bronlardı qaytaradı.

        Sharhı joq hár juwmaqlanǵan bron bólek jazıladı, sol sebepli bir mehmanxanada eki
        turıw eki jazba boladı.
        """
        user = request.user

        # Óshirilgen (soft-deleted) sharhlar da esapqa alınadı: bronǵa qayta sharh jazıp bolmaydı
        completed_bookings = Booking.objects.filter(
            guest=user,
            status='completed',
            is_deleted=False
        ).exclude(
            reviews__isnull=False
        ).select_related('property').order_by('-check_out', '-id')

        eligible_properties = []
        for booking in completed_bookings:
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

    # Ashıq hám tek oqıw ushın: dizimdegi mehmanxananıń tastıyıqlanǵan sharhları, eń jańası birinshi (sharh jazıwshı "Aziz K."
    # sıyaqlı)
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def public(self, request):
        """Bir mehmanxananıń tastıyıqlanǵan sharhları, betlerge bólingen (paginated)."""
        raw = request.query_params.get('property_id')
        if not raw or not raw.isdigit():
            return Response({'detail': _('property_id must be a whole number.')}, status=status.HTTP_400_BAD_REQUEST)
        if not Property.objects.filter(pk=int(raw), status='active', is_deleted=False).exists():
            return Response({'detail': _('Not found.')}, status=status.HTTP_404_NOT_FOUND)
        reviews = Review.objects.filter(property_id=int(raw), status='approved', is_deleted=False) \
            .select_related('user', 'booking').order_by('-created_at', '-id')
        page = self.paginate_queryset(reviews)
        return self.get_paginated_response(PublicReviewSerializer(page, many=True).data)

    # Ashıq hám tek oqıw ushın: tastıyıqlanǵan sharhlardıń jámi bahaları hár mehmanxana betinde kórsetiledi
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def property_scores(self, request):
        """
        Belgili bir mehmanxana ushın sharh bahaların qaytaradı.

        Mehmanxana ushın hár túrli kategoriyalar boyınsha ortasha bahalardı qaytaradı.
        """
        property_id = request.query_params.get('property_id')

        if not property_id:
            return Response(
                {'detail': 'property_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            property_id = int(property_id)
        except (TypeError, ValueError):
            return Response(
                {'detail': 'property_id must be an integer'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mehmanxananıń tastıyıqlanǵan sharhların alıw
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

        # Ortasha bahalardı esaplaw
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
    Paydalanıwshı bildiriwlerin basqarıw ushın ViewSet.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Házirgi paydalanıwshınıń bildiriwlerin qaytaradı."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema jasaw: paydalanıwshı joq
            return self.get_serializer_class().Meta.model.objects.none()
        return Notification.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).select_related('booking', 'property')

    def get_serializer_class(self):
        """Háreketke qarap tiyisli serializer di qaytaradı."""
        if self.action in ['update', 'partial_update']:
            return NotificationUpdateSerializer
        return NotificationSerializer

    def create(self, request, *args, **kwargs):
        """Bildiriwlerdi API arqalı tikkeley jaratıwdıń aldın aladı."""
        return Response(
            {'detail': _('Notifications cannot be created directly through API.')},
            status=status.HTTP_403_FORBIDDEN
        )

    def perform_update(self, serializer):
        """Bildiriwdi jańalaw."""
        if 'is_read' in serializer.validated_data:
            serializer.save()

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Házirgi paydalanıwshınıń oqılmaǵan bildiriwlerin qaytaradı."""
        unread = self.get_queryset().filter(is_read=False)
        page = self.paginate_queryset(unread)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Házirgi paydalanıwshınıń barlıq bildiriwlerin oqılǵan dep belgileydi."""
        count = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'marked_as_read': count})

    @action(detail=False, methods=['get'])
    def count(self, request):
        """Házirgi paydalanıwshınıń bildiriw sanların qaytaradı."""
        total = self.get_queryset().count()
        unread = self.get_queryset().filter(is_read=False).count()

        return Response({
            'total': total,
            'unread': unread,
            'read': total - unread
        })


class AccountHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Paydalanıwshı akkaunt tariyxın kóriw ushın ViewSet.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Házirgi paydalanıwshınıń akkaunt tariyxın qaytaradı."""
        if getattr(self, 'swagger_fake_view', False):  # OpenAPI schema jasaw: paydalanıwshı joq
            return self.get_serializer_class().Meta.model.objects.none()
        return AccountHistory.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).select_related('booking', 'property')

    def get_serializer_class(self):
        """Háreketke qarap tiyisli serializer di qaytaradı."""
        return AccountHistorySerializer

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Eń sońǵı akkaunt tariyxı jazbaların qaytaradı."""
        try:
            limit = int(request.query_params.get('limit', 10))
        except (TypeError, ValueError):
            return Response(
                {'detail': 'limit must be a positive integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if limit < 1:
            return Response(
                {'detail': 'limit must be a positive integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        limit = min(limit, 50)
        recent = self.get_queryset()[:limit]
        serializer = self.get_serializer(recent, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Akkaunt háreketleri statistikasın qaytaradı."""
        queryset = self.get_queryset()

        # Háreket túri boyınsha sanaw
        action_counts = queryset.values('action').annotate(
            count=Count('id')
        ).order_by('-count')

        return Response({
            'total_entries': queryset.count(),
            'action_counts': list(action_counts)
        })

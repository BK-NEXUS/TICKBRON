"""
Tests for accounts views.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from properties.models import Property, PropertyType
from bookings.models import Booking
from accounts.models import Favorite, Review, Notification, AccountHistory

User = get_user_model()


class FavoriteViewSetTest(TestCase):
    """Test cases for FavoriteViewSet."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)
        
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            status='active',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Test Street',
            city='Test City',
            country='Test Country',
            base_price=100.00,
            currency='USD'
        )
    
    def test_create_favorite(self):
        """Test creating a favorite."""
        data = {
            'property': self.property.id,
            'notes': 'Great property!'
        }
        response = self.client.post('/api/v1/me/favorites/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Favorite.objects.count(), 1)
        self.assertEqual(Favorite.objects.first().user, self.user)
    
    def test_list_favorites(self):
        """Test listing user favorites."""
        Favorite.objects.create(user=self.user, property=self.property)
        response = self.client.get('/api/v1/me/favorites/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_delete_favorite(self):
        """Test deleting a favorite."""
        favorite = Favorite.objects.create(user=self.user, property=self.property)
        response = self.client.delete(f'/api/v1/me/favorites/{favorite.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        favorite.refresh_from_db()
        self.assertTrue(favorite.is_deleted)
    
    def test_favorite_count(self):
        """Test getting favorite count."""
        Favorite.objects.create(user=self.user, property=self.property)
        response = self.client.get('/api/v1/me/favorites/count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_cannot_favorite_inactive_property(self):
        """Test that inactive properties cannot be favorited."""
        self.property.is_active = False
        self.property.save()
        
        data = {'property': self.property.id}
        response = self.client.post('/api/v1/me/favorites/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReviewViewSetTest(TestCase):
    """Test cases for ReviewViewSet."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)
        
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            status='active',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Test Street',
            city='Test City',
            country='Test Country',
            base_price=100.00,
            currency='USD'
        )
        self.booking = Booking.objects.create(
            guest=self.user,
            property=self.property,
            check_in='2024-01-01',
            check_out='2024-01-05',
            number_of_nights=4,
            guest_count=2,
            total_price=400.00,
            currency='USD',
            status='completed'
        )
    
    def test_create_review_without_booking(self):
        """Test creating a review without booking."""
        data = {
            'property': self.property.id,
            'overall_rating': 5,
            'title': 'Great stay!',
            'comment': 'Excellent property'
        }
        response = self.client.post('/api/v1/me/reviews/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_eligible_properties(self):
        """Test getting eligible properties for review."""
        response = self.client.get('/api/v1/me/reviews/eligible_properties/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['eligible_properties']), 1)
        self.assertEqual(response.data['eligible_properties'][0]['property_id'], self.property.id)
        self.assertEqual(response.data['eligible_properties'][0]['property_city'], 'Test City')
    
    def test_eligible_properties_excludes_reviewed(self):
        """Test that reviewed properties are excluded from eligible list."""
        Review.objects.create(
            user=self.user,
            property=self.property,
            booking=self.booking,
            overall_rating=5
        )
        
        response = self.client.get('/api/v1/me/reviews/eligible_properties/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['eligible_properties']), 0)
    
    def test_property_scores(self):
        """Test getting property review scores."""
        # Create approved reviews
        Review.objects.create(
            user=self.user,
            property=self.property,
            overall_rating=5,
            cleanliness_rating=5,
            status='approved'
        )
        
        response = self.client.get(f'/api/v1/me/reviews/property_scores/?property_id={self.property.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_reviews'], 1)
        self.assertEqual(response.data['average_rating'], 5.0)
    
    def test_property_scores_no_reviews(self):
        """Test property scores when no reviews exist."""
        response = self.client.get(f'/api/v1/me/reviews/property_scores/?property_id={self.property.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_reviews'], 0)
        self.assertIsNone(response.data['average_rating'])


class NotificationViewSetTest(TestCase):
    """Test cases for NotificationViewSet."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)
        
        self.notification = Notification.objects.create(
            user=self.user,
            notification_type='booking',
            priority='normal',
            title='Test Notification',
            message='Test message'
        )
    
    def test_list_notifications(self):
        """Test listing user notifications."""
        response = self.client.get('/api/v1/me/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_unread_notifications(self):
        """Test getting unread notifications."""
        response = self.client.get('/api/v1/me/notifications/unread/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_mark_notification_as_read(self):
        """Test marking notification as read."""
        response = self.client.patch(f'/api/v1/me/notifications/{self.notification.id}/', {'is_read': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
    
    def test_mark_all_read(self):
        """Test marking all notifications as read."""
        Notification.objects.create(
            user=self.user,
            notification_type='payment',
            priority='normal',
            title='Another Notification',
            message='Another message'
        )
        
        response = self.client.post('/api/v1/me/notifications/mark_all_read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['marked_as_read'], 2)
    
    def test_notification_count(self):
        """Test getting notification counts."""
        response = self.client.get('/api/v1/me/notifications/count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['unread'], 1)
    
    def test_cannot_create_notification_via_api(self):
        """Test that notifications cannot be created via API."""
        data = {
            'notification_type': 'booking',
            'priority': 'normal',
            'title': 'Test',
            'message': 'Test message'
        }
        response = self.client.post('/api/v1/me/notifications/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AccountHistoryViewSetTest(TestCase):
    """Test cases for AccountHistoryViewSet."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)
        
        self.history = AccountHistory.objects.create(
            user=self.user,
            action='login',
            description='User logged in'
        )
    
    def test_list_account_history(self):
        """Test listing account history."""
        response = self.client.get('/api/v1/me/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_recent_history(self):
        """Test getting recent history."""
        response = self.client.get('/api/v1/me/history/recent/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_history_stats(self):
        """Test getting history statistics."""
        response = self.client.get('/api/v1/me/history/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_entries'], 1)
        self.assertEqual(len(response.data['action_counts']), 1)
    
    def test_cannot_create_history_via_api(self):
        """Test that history cannot be created via API (read-only)."""
        data = {
            'action': 'login',
            'description': 'Test'
        }
        response = self.client.post('/api/v1/me/history/', data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

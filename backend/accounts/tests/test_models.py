"""
accounts model leri ushın testler.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from users.models import User
from properties.models import Property, PropertyType
from bookings.models import Booking
from accounts.models import Favorite, Review, Notification, AccountHistory


class FavoriteModelTest(TestCase):
    """Favorite modeli ushın test jaǵdayları."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
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

    def test_favorite_creation(self):
        """Favorit jaratıwdı testlew."""
        favorite = Favorite.objects.create(
            user=self.user,
            property=self.property,
            notes='Great property!'
        )
        self.assertEqual(favorite.user, self.user)
        self.assertEqual(favorite.property, self.property)
        self.assertEqual(favorite.notes, 'Great property!')
        self.assertTrue(favorite.is_active)
        self.assertFalse(favorite.is_deleted)

    def test_favorite_unique_constraint(self):
        """Paydalanıwshı mehmanxananı tek bir márte favorit etiwi múmkinligin testlew."""
        Favorite.objects.create(user=self.user, property=self.property)

        with self.assertRaises(Exception):
            Favorite.objects.create(user=self.user, property=self.property)

    def test_favorite_str(self):
        """Favorit tiń qatar kórinisin testlew."""
        favorite = Favorite.objects.create(user=self.user, property=self.property)
        expected = f"{self.user.email} - {self.property.city}"
        self.assertEqual(str(favorite), expected)


class ReviewModelTest(TestCase):
    """Review modeli ushın test jaǵdayları."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
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

    def test_review_creation(self):
        """Sharh jaratıwdı testlew."""
        review = Review.objects.create(
            user=self.user,
            property=self.property,
            booking=self.booking,
            overall_rating=5,
            cleanliness_rating=5,
            location_rating=4,
            title='Great stay!',
            comment='Excellent property'
        )
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.property, self.property)
        self.assertEqual(review.overall_rating, 5)
        self.assertEqual(review.status, 'pending')
        self.assertIsNone(review.reviewed_at)

    def test_review_approval_sets_reviewed_at(self):
        """Sharhtı tastıyıqlaw reviewed_at waqıt belgisin belgilewin testlew."""
        review = Review.objects.create(
            user=self.user,
            property=self.property,
            booking=self.booking,
            overall_rating=5,
            status='pending'
        )

        self.assertIsNone(review.reviewed_at)

        review.status = 'approved'
        review.save()

        self.assertIsNotNone(review.reviewed_at)

    def test_review_rating_validation(self):
        """Bahalar 1 hám 5 aralıǵında bolıwı kerekligin testlew."""
        with self.assertRaises(ValidationError):
            review = Review(
                user=self.user,
                property=self.property,
                overall_rating=6  # Jaramsız baha
            )
            review.full_clean()

    def test_review_unique_booking_constraint(self):
        """Paydalanıwshı bir bronǵa tek bir márte sharh jaza alatuǵının testlew."""
        Review.objects.create(
            user=self.user,
            property=self.property,
            booking=self.booking,
            overall_rating=5
        )

        with self.assertRaises(Exception):
            Review.objects.create(
                user=self.user,
                property=self.property,
                booking=self.booking,
                overall_rating=4
            )

    def test_review_str(self):
        """Sharhtıń qatar kórinisin testlew."""
        review = Review.objects.create(
            user=self.user,
            property=self.property,
            overall_rating=5
        )
        expected = f"{self.user.email} - {self.property.city} (5/5)"
        self.assertEqual(str(review), expected)


class NotificationModelTest(TestCase):
    """Notification modeli ushın test jaǵdayları."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
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

    def test_notification_creation(self):
        """Bildiriw jaratıwdı testlew."""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='booking',
            priority='normal',
            title='Booking Confirmed',
            message='Your booking has been confirmed'
        )
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.notification_type, 'booking')
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)

    def test_mark_as_read(self):
        """Bildiriwdi oqılǵan dep belgilewdi testlew."""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='booking',
            priority='normal',
            title='Test',
            message='Test message'
        )

        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)

        notification.mark_as_read()

        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

    def test_notification_str(self):
        """Bildiriwdiń qatar kórinisin testlew."""
        notification = Notification.objects.create(
            user=self.user,
            notification_type='booking',
            priority='normal',
            title='Test',
            message='Test message'
        )
        expected = f"{self.user.email} - Test"
        self.assertEqual(str(notification), expected)


class AccountHistoryModelTest(TestCase):
    """AccountHistory modeli ushın test jaǵdayları."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
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

    def test_account_history_creation(self):
        """Akkaunt tariyxı jazbasın jaratıwdı testlew."""
        history = AccountHistory.objects.create(
            user=self.user,
            action='login',
            description='User logged in',
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.action, 'login')
        self.assertEqual(history.description, 'User logged in')
        self.assertEqual(history.ip_address, '127.0.0.1')

    def test_account_history_with_metadata(self):
        """JSON metadata menen akkaunt tariyxın testlew."""
        metadata = {'key': 'value', 'number': 123}
        history = AccountHistory.objects.create(
            user=self.user,
            action='profile_update',
            description='User updated profile',
            metadata=metadata
        )
        self.assertEqual(history.metadata, metadata)

    def test_account_history_str(self):
        """Akkaunt tariyxınıń qatar kórinisin testlew."""
        history = AccountHistory.objects.create(
            user=self.user,
            action='login',
            description='User logged in'
        )
        expected = f"{self.user.email} - login - {history.created_at}"
        self.assertEqual(str(history), expected)

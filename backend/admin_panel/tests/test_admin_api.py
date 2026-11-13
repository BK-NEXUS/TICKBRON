"""
Admin API endpoint leri ushın testler.

Bul modul mehmanxana moderation ı, paydalanıwshılardı basqarıw
hám amenity di basqarıw ushın testlerdi óz ishine aladı.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from partner.tests.geography_helpers import uzbek_location
from admin_panel.tests.listing_helpers import make_listable
from properties.models import Property, PropertyType, Amenity, AmenityCategory, RoomType, RatePlan
from bookings.models import Booking, BookingItem
from admin_panel.models import InternalNote
from decimal import Decimal
from datetime import date, datetime, timedelta, timezone as dt_timezone
from unittest import mock
from django.utils import timezone

User = get_user_model()


class AdminPropertyTests(TestCase):
    """Admin mehmanxana moderation endpoint leri ushın testler."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.client = APIClient()

        # Super-admin paydalanıwshı jaratıw
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )

        # Staff paydalanıwshı jaratıw
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )

        # Ápiwayı paydalanıwshı jaratıw
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='testpassword123',
            first_name='Regular',
            last_name='User'
        )

        # Mehmanxana túrin hám mehmanxananı jaratıw
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment',
            description='Apartment property type'
        )

        self.property = Property.objects.create(
            owner=self.regular_user,
            property_type=self.property_type,
            status='pending_approval',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Main St',
            city='Tashkent',
            country='Uzbekistan',
            base_price=100.00,
            currency='USD'
        )
        make_listable(self.property)

    def test_super_admin_can_list_all_properties(self):
        """Super-admin barlıq mehmanxanalardı dizimley alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/properties/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Keminde bizdiń test mehmanxanamız dizimde ekenin tekseriw (betlengen juwap)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        property_ids = [prop['id'] for prop in results]
        self.assertIn(self.property.id, property_ids)

    def test_staff_can_list_all_properties(self):
        """Staff barlıq mehmanxanalardı dizimley alatuǵının testlew."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin-panel/properties/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Keminde bizdiń test mehmanxanamız dizimde ekenin tekseriw (betlengen juwap)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        property_ids = [prop['id'] for prop in results]
        self.assertIn(self.property.id, property_ids)

    def test_regular_user_cannot_list_admin_properties(self):
        """Ápiwayı paydalanıwshı admin mehmanxana endpoint lerine kire almaytuǵının testlew."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/admin-panel/properties/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_super_admin_can_approve_property(self):
        """Super-admin mehmanxananı tastıyıqlay alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.post(f'/api/v1/admin-panel/properties/{self.property.id}/approve/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, 'active')
        self.assertEqual(self.property.approved_by, self.super_admin)
        self.assertIsNotNone(self.property.approved_at)

    def test_staff_can_approve_property(self):
        """Staff mehmanxananı tastıyıqlay alatuǵının testlew."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(f'/api/v1/admin-panel/properties/{self.property.id}/approve/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, 'active')

    def test_admin_can_reject_property_with_reason(self):
        """Admin mehmanxananı sebep penen biykar ete alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        data = {'rejection_reason': 'Property does not meet standards'}
        response = self.client.post(f'/api/v1/admin-panel/properties/{self.property.id}/approve/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, 'rejected')
        self.assertEqual(self.property.rejection_reason, 'Property does not meet standards')

    def test_admin_can_suspend_property(self):
        """Admin mehmanxananı toqtata alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.post(f'/api/v1/admin-panel/properties/{self.property.id}/suspend/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, 'suspended')


class AdminUserTests(TestCase):
    """Admin paydalanıwshılardı basqarıw endpoint leri ushın testler."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.client = APIClient()

        # Super-admin paydalanıwshı jaratıw
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )

        # Staff paydalanıwshı jaratıw
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )

        # Ápiwayı paydalanıwshı jaratıw
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='testpassword123',
            first_name='Regular',
            last_name='User'
        )

    def test_super_admin_can_list_all_users(self):
        """Super-admin barlıq paydalanıwshılardı dizimley alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/users/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)  # alfavit filterinen (2026-11-01) beri bir waqıtta bir bet

    def test_staff_can_list_all_users(self):
        """Staff barlıq paydalanıwshılardı dizimley alatuǵının testlew."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin-panel/users/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_regular_user_cannot_list_admin_users(self):
        """Ápiwayı paydalanıwshı admin paydalanıwshı endpoint lerine kire almaytuǵının testlew."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/admin-panel/users/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_super_admin_can_create_hotel_owner_account(self):
        """Super-admin mehmanxana iyesi akkaunt ın jarata alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        data = {
            'email': 'hotelowner@example.com',
            'first_name': 'Hotel',
            'last_name': 'Owner',
            'phone_number': '+998901234567',
            'password': 'Owner#Secret2026',
            'password_confirm': 'Owner#Secret2026',
            **uzbek_location('Tashkent'),  # jańa akkauntqa orın kerek
        }
        response = self.client.post('/api/v1/admin-panel/users/create-hotel-owner/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 4)

        # Paydalanıwshıda mehmanxana iyesi roli barlıǵın tekseriw
        new_user = User.objects.get(email='hotelowner@example.com')
        self.assertEqual(new_user.role.name, 'hotel-owner')

    def test_staff_cannot_create_hotel_owner_account(self):
        """Staff mehmanxana iyesi akkaunt ın jarata almaytuǵının testlew."""
        self.client.force_authenticate(user=self.staff_user)
        data = {
            'email': 'hotelowner2@example.com',
            'first_name': 'Hotel',
            'last_name': 'Owner',
            'password': 'testpassword123',
            'password_confirm': 'testpassword123'
        }
        response = self.client.post('/api/v1/admin-panel/users/create-hotel-owner/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(User.objects.count(), 3)

    def test_hotel_owner_names_take_no_digits(self):
        self.client.force_authenticate(user=self.super_admin)
        data = {
            'email': 'digitowner@example.com', 'first_name': 'Hotel7', 'last_name': 'Owner',
            'password': 'Owner#Secret2026', 'password_confirm': 'Owner#Secret2026',
        }
        response = self.client.post('/api/v1/admin-panel/users/create-hotel-owner/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)
        self.assertFalse(User.objects.filter(email='digitowner@example.com').exists())

    def test_password_mismatch_validation(self):
        """Parol sáykes kelmewi tekserilgenin testlew."""
        self.client.force_authenticate(user=self.super_admin)
        data = {
            'email': 'hotelowner3@example.com',
            'first_name': 'Hotel',
            'last_name': 'Owner',
            'password': 'testpassword123',
            'password_confirm': 'differentpassword',
            **uzbek_location('Tashkent'),  # jańa akkauntqa orın kerek
            'phone_number': '+998901234567',  # jańa akkauntqa telefon nomeri kerek
        }
        response = self.client.post('/api/v1/admin-panel/users/create-hotel-owner/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)

    def test_password_not_returned_in_response(self):
        """Parol juwapta qaytarılmaytuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        data = {
            'email': 'hotelowner4@example.com',
            'first_name': 'Hotel',
            'last_name': 'Owner',
            'password': 'Owner#Secret2026',
            'password_confirm': 'Owner#Secret2026',
            **uzbek_location('Tashkent'),  # jańa akkauntqa orın kerek
            'phone_number': '+998901234567',  # jańa akkauntqa telefon nomeri kerek
        }
        response = self.client.post('/api/v1/admin-panel/users/create-hotel-owner/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', response.data)
        self.assertNotIn('password_confirm', response.data)


class AdminAmenityTests(TestCase):
    """Admin amenity di basqarıw endpoint leri ushın testler."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.client = APIClient()

        # Super-admin paydalanıwshı jaratıw
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )

        # Staff paydalanıwshı jaratıw
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )

        # Ápiwayı paydalanıwshı jaratıw
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='testpassword123',
            first_name='Regular',
            last_name='User'
        )

        # Amenity kategoriyasın jaratıw
        self.amenity_category = AmenityCategory.objects.create(
            name='Kitchen',
            slug='kitchen',
            description='Kitchen amenities',
            sort_order=1
        )

        # Amenity jaratıw
        self.amenity = Amenity.objects.create(
            category=self.amenity_category,
            name='WiFi',
            slug='wifi',
            description='Wireless internet',
            is_searchable=True,
            sort_order=1
        )

    def test_super_admin_can_list_all_amenities(self):
        """Super-admin barlıq amenity lerdi dizimley alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/amenities/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Keminde bizdiń test amenity miz dizimde ekenin tekseriw (betlengen juwap)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        amenity_ids = [amenity['id'] for amenity in results]
        self.assertIn(self.amenity.id, amenity_ids)

    def test_staff_can_list_all_amenities(self):
        """Staff barlıq amenity lerdi dizimley alatuǵının testlew."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin-panel/amenities/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Keminde bizdiń test amenity miz dizimde ekenin tekseriw (betlengen juwap)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        amenity_ids = [amenity['id'] for amenity in results]
        self.assertIn(self.amenity.id, amenity_ids)

    def test_regular_user_cannot_list_admin_amenities(self):
        """Ápiwayı paydalanıwshı admin amenity endpoint lerine kire almaytuǵının testlew."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/admin-panel/amenities/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_super_admin_can_create_amenity(self):
        """Super-admin amenity jarata alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        data = {
            'category': self.amenity_category.id,
            'name': 'Air Conditioning',
            'slug': 'air-conditioning',
            'description': 'Climate control',
            'is_searchable': True,
            'sort_order': 2
        }
        response = self.client.post('/api/v1/admin-panel/amenities/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Amenity.objects.count(), 2)

    def test_super_admin_can_update_amenity(self):
        """Super-admin amenity di jańalay alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        data = {
            'name': 'Wireless Internet',
            'description': 'High-speed wireless internet'
        }
        response = self.client.patch(f'/api/v1/admin-panel/amenities/{self.amenity.id}/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.amenity.refresh_from_db()
        self.assertEqual(self.amenity.name, 'Wireless Internet')

    def test_super_admin_can_delete_amenity(self):
        """Super-admin amenity di óshire alatuǵının testlew (soft delete)."""
        self.client.force_authenticate(user=self.super_admin)
        amenity_id = self.amenity.id
        response = self.client.delete(f'/api/v1/admin-panel/amenities/{amenity_id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Amenity endi aktiv queryset te joq ekenin tekseriw
        self.assertFalse(Amenity.objects.filter(id=amenity_id).exists())

    def test_super_admin_can_manage_amenity_categories(self):
        """Super-admin amenity kategoriyaların basqara alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)

        # Kategoriya jaratıw
        data = {
            'name': 'Bathroom',
            'slug': 'bathroom',
            'description': 'Bathroom amenities',
            'sort_order': 2
        }
        response = self.client.post('/api/v1/admin-panel/amenities/categories/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AmenityCategory.objects.count(), 2)


class AdminPermissionTests(TestCase):
    """Admin ruxsatların shekemlew ushın testler."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.client = APIClient()

        # Super-admin paydalanıwshı jaratıw
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )

        # Staff paydalanıwshı jaratıw
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )

        # Ápiwayı paydalanıwshı jaratıw
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='testpassword123',
            first_name='Regular',
            last_name='User'
        )

    def test_unauthenticated_user_cannot_access_admin_endpoints(self):
        """Kirmegen paydalanıwshılar admin endpoint lerge kire almaytuǵının testlew."""
        endpoints = [
            '/api/v1/admin-panel/properties/',
            '/api/v1/admin-panel/users/',
            '/api/v1/admin-panel/amenities/',
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            # Autentifikaciya kerek bolǵanda DRF kirmegen paydalanıwshılarǵa 403 qaytaradı
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_staff_user_cannot_access_admin_endpoints(self):
        """Staff emes paydalanıwshılar admin endpoint lerge kire almaytuǵının testlew."""
        self.client.force_authenticate(user=self.regular_user)
        endpoints = [
            '/api/v1/admin-panel/properties/',
            '/api/v1/admin-panel/users/',
            '/api/v1/admin-panel/amenities/',
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_superuser_cannot_create_hotel_owner(self):
        """Super-admin emes paydalanıwshı mehmanxana iyesi akkaunt ın jarata almaytuǵının testlew."""
        self.client.force_authenticate(user=self.staff_user)
        data = {
            'email': 'hotelowner@example.com',
            'first_name': 'Hotel',
            'last_name': 'Owner',
            'password': 'testpassword123',
            'password_confirm': 'testpassword123'
        }
        response = self.client.post('/api/v1/admin-panel/users/create-hotel-owner/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminBookingLookupTests(TestCase):
    """Admin bronlardı reference code boyınsha izlew endpoint i ushın testler."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.client = APIClient()

        # Super-admin paydalanıwshı jaratıw
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )

        # Staff paydalanıwshı jaratıw
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )

        # Ápiwayı paydalanıwshı jaratıw
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='testpassword123',
            first_name='Regular',
            last_name='User'
        )

        # Mehmanxana túrin hám mehmanxananı jaratıw
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment',
            description='Apartment property type'
        )

        self.property = Property.objects.create(
            owner=self.regular_user,
            property_type=self.property_type,
            status='active',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Main St',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00'),
            currency='USD'
        )

        # Xona túrin hám rate plan dı jaratıw
        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('100.00'),
            currency='USD',
            total_rooms=5
        )

        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type,
            name='Standard Rate',
            slug='standard-rate',
            rate_type='standard',
            base_price=Decimal('100.00'),
            currency='USD',
            min_nights=1,
            max_nights=30,
            is_active=True
        )

        # Bron jaratıw
        self.booking = Booking.objects.create(
            guest=self.regular_user,
            property=self.property,
            status='confirmed',
            payment_status='paid',
            check_in=date.today() + timedelta(days=10),
            check_out=date.today() + timedelta(days=12),
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD',
            guest_full_name='Regular User',
            guest_phone='+998901234567',
            guest_email='regular@example.com',
            number_of_rooms=1,
            children=[]
        )

        # Bron elementin jaratıw
        BookingItem.objects.create(
            booking=self.booking,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            number_of_rooms=1,
            price_per_night=Decimal('100.00'),
            currency='USD'
        )

    def test_super_admin_can_lookup_booking_by_reference_code(self):
        """Super-admin bronnı reference code boyınsha izley alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/bookings/lookup/?reference_code={self.booking.confirmation_code}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('booking', response.data)
        self.assertIn('customer', response.data)
        self.assertIn('property', response.data)

        # Bron maǵlıwmatın tekseriw
        booking_data = response.data['booking']
        self.assertEqual(booking_data['reference_code'], self.booking.confirmation_code)
        self.assertEqual(booking_data['status'], 'confirmed')
        self.assertEqual(booking_data['payment_status'], 'paid')

        # Mijoz maǵlıwmatın tekseriw
        customer_data = response.data['customer']
        self.assertEqual(customer_data['email'], 'regular@example.com')
        self.assertEqual(customer_data['full_name'], 'Regular User')

        # Mehmanxana maǵlıwmatın tekseriw
        property_data = response.data['property']
        self.assertEqual(property_data['id'], self.property.id)
        # Kórsetiletuǵın at mehmanxana atı (awdarma); bul mehmanxanada ol joq,
        # sol sebepli oylap tabılǵan "Property N - city" belgisi emes, mánzilge qaytadı
        self.assertEqual(
            property_data['name'],
            '123 Main St, Tashkent, Uzbekistan'
        )

    def test_staff_can_lookup_booking_by_reference_code(self):
        """Staff bronnı reference code boyınsha izley alatuǵının testlew."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(f'/api/v1/admin-panel/bookings/lookup/?reference_code={self.booking.confirmation_code}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('booking', response.data)

    def test_regular_user_cannot_lookup_booking_by_reference_code(self):
        """Ápiwayı paydalanıwshı bron izlew endpoint ine kire almaytuǵının testlew."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f'/api/v1/admin-panel/bookings/lookup/?reference_code={self.booking.confirmation_code}')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_lookup_booking(self):
        """Kirmegen paydalanıwshı bron izlew endpoint ine kire almaytuǵının testlew."""
        response = self.client.get(f'/api/v1/admin-panel/bookings/lookup/?reference_code={self.booking.confirmation_code}')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lookup_with_missing_reference_code_parameter(self):
        """reference_code parametri joq bolsa 400 qátelik qaytarılatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/bookings/lookup/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_lookup_with_invalid_reference_code(self):
        """Jaramsız reference code 404 qátelik qaytaratuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/bookings/lookup/?reference_code=INVALID')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_lookup_case_insensitive(self):
        """Reference code izlewi register ti esapqa almaytuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)

        # Kishi háripler menen testlew
        response = self.client.get(f'/api/v1/admin-panel/bookings/lookup/?reference_code={self.booking.confirmation_code.lower()}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['booking']['reference_code'], self.booking.confirmation_code)

    def test_lookup_returns_all_required_fields(self):
        """Izlew kerek mijoz hám bron maǵlıwmatınıń hámmesin qaytaratuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/bookings/lookup/?reference_code={self.booking.confirmation_code}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Bron maydanların tekseriw
        booking_data = response.data['booking']
        required_booking_fields = [
            'id', 'reference_code', 'status', 'payment_status', 'check_in', 'check_out',
            'number_of_nights', 'guest_count', 'total_price', 'currency', 'special_requests',
            'guest_full_name', 'guest_phone', 'guest_email', 'number_of_rooms', 'children', 'booking_items'
        ]
        for field in required_booking_fields:
            self.assertIn(field, booking_data)

        # Mijoz maydanların tekseriw
        customer_data = response.data['customer']
        required_customer_fields = ['id', 'full_name', 'email', 'phone_number', 'whatsapp', 'telegram', 'preferred_contact_method']
        for field in required_customer_fields:
            self.assertIn(field, customer_data)

        # Mehmanxana maydanların tekseriw
        property_data = response.data['property']
        required_property_fields = ['id', 'name', 'property_type', 'status', 'address_line1', 'city', 'state', 'country', 'base_price', 'currency', 'owner']
        for field in required_property_fields:
            self.assertIn(field, property_data)


class AdminCustomersDirectoryTests(TestCase):
    """Admin mijozlar dizimi API endpoint i ushın testler."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.client = APIClient()

        # Super-admin paydalanıwshı jaratıw
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )

        # Staff paydalanıwshı jaratıw
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )

        # Ápiwayı paydalanıwshı jaratıw
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='testpassword123',
            first_name='Regular',
            last_name='User',
            phone_number='+998901234567',
            whatsapp='+998901234567',
            telegram='@regularuser',
            preferred_contact_method='whatsapp'
        )

        # Basqa mijoz paydalanıwshı jaratıw
        self.customer2 = User.objects.create_user(
            email='customer2@example.com',
            password='testpassword123',
            first_name='Customer',
            last_name='Two',
            phone_number='+998901234568'
        )

        # Mehmanxana túrin hám mehmanxananı jaratıw
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment',
            description='Apartment property type'
        )

        self.property = Property.objects.create(
            owner=self.super_admin,
            property_type=self.property_type,
            status='active',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Main St',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00'),
            currency='USD'
        )

        # Xona túrin hám rate plan dı jaratıw
        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('100.00'),
            currency='USD',
            total_rooms=5
        )

        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type,
            name='Standard Rate',
            slug='standard-rate',
            rate_type='standard',
            base_price=Decimal('100.00'),
            currency='USD',
            min_nights=1,
            max_nights=30,
            is_active=True
        )

        # regular_user ushın bron jaratıw
        self.booking1 = Booking.objects.create(
            guest=self.regular_user,
            property=self.property,
            status='confirmed',
            payment_status='paid',
            check_in=date.today() + timedelta(days=10),
            check_out=date.today() + timedelta(days=12),
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD',
            guest_full_name='Regular User',
            guest_phone='+998901234567',
            guest_email='regular@example.com',
            number_of_rooms=1,
            children=[]
        )

        BookingItem.objects.create(
            booking=self.booking1,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            number_of_rooms=1,
            price_per_night=Decimal('100.00'),
            currency='USD'
        )


    def test_super_admin_can_access_customers_directory(self):
        """Super-admin mijozlar dizimine kire alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIsInstance(response.data['results'], list)

    def test_staff_can_access_customers_directory(self):
        """Staff mijozlar dizimine kire alatuǵının testlew."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin-panel/customers/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_regular_user_cannot_access_customers_directory(self):
        """Ápiwayı paydalanıwshı mijozlar dizimine kire almaytuǵının testlew."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/admin-panel/customers/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_access_customers_directory(self):
        """Kirmegen paydalanıwshı mijozlar dizimine kire almaytuǵının testlew."""
        response = self.client.get('/api/v1/admin-panel/customers/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customers_directory_returns_required_fields(self):
        """Mijozlar dizimi kerek maydanlardıń hámmesin qaytaratuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Birinshi mijozda kerek maydanlardıń hámmesi barlıǵın tekseriw
        if response.data['results']:
            customer_data = response.data['results'][0]
            required_fields = [
                'id', 'registration_date', 'full_name', 'phone', 'email',
                'whatsapp', 'telegram', 'preferred_contact_method',
                'total_booking_count', 'last_booking_date', 'customer_status'
            ]
            for field in required_fields:
                self.assertIn(field, customer_data)

    def test_customers_directory_includes_booking_aggregates(self):
        """Mijozlar dizimi bron jıynaqların óz ishine alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Nátiyjelerde regular_user dı tabıw
        regular_user_data = None
        for customer in response.data['results']:
            if customer['email'] == 'regular@example.com':
                regular_user_data = customer
                break

        self.assertIsNotNone(regular_user_data)
        self.assertEqual(regular_user_data['total_booking_count'], 1)
        self.assertNotIn('total_amount_paid', regular_user_data)
        self.assertIsNotNone(regular_user_data['last_booking_date'])

    def test_search_by_name(self):
        """Mijozlardı at boyınsha izlewdi testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/?search=Regular')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # regular_user tabılıwı kerek
        found = False
        for customer in response.data['results']:
            if customer['email'] == 'regular@example.com':
                found = True
                break
        self.assertTrue(found)

    def test_search_by_email(self):
        """Mijozlardı e-mail boyınsha izlewdi testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/?search=regular@example.com')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # regular_user tabılıwı kerek
        found = False
        for customer in response.data['results']:
            if customer['email'] == 'regular@example.com':
                found = True
                break
        self.assertTrue(found)

    def test_search_by_phone(self):
        """Mijozlardı telefon boyınsha izlewdi testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/?search=+998901234567')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # regular_user tabılıwı kerek
        found = False
        for customer in response.data['results']:
            if customer['email'] == 'regular@example.com':
                found = True
                break
        self.assertTrue(found)

    def test_search_by_customer_id(self):
        """Mijozlardı mijoz ID si boyınsha izlewdi testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/?search={self.regular_user.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # regular_user tabılıwı kerek
        found = False
        for customer in response.data['results']:
            if customer['id'] == self.regular_user.id:
                found = True
                break
        self.assertTrue(found)

    def test_pagination_works(self):
        """Betlew durıs islewin testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/?page_size=1')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        self.assertLessEqual(len(response.data['results']), 1)

    def test_sorting_by_registration_date(self):
        """Dizimnen ótiw sanası boyınsha tártiplewdi testlew."""
        self.client.force_authenticate(user=self.super_admin)

        # Ósiw tártibinde tártiplew
        response = self.client.get('/api/v1/admin-panel/customers/?sort_by=registration_date&sort_order=asc')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Kemeyiw tártibinde tártiplew
        response = self.client.get('/api/v1/admin-panel/customers/?sort_by=registration_date&sort_order=desc')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sorting_by_total_booking_count(self):
        """Jámi bron sanı boyınsha tártiplewdi testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/?sort_by=total_booking_count&sort_order=desc')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_status_active_for_recent_booking(self):
        """Jaqında broni bar mijoz aktiv dep belgilenetuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Nátiyjelerde regular_user dı tabıw
        regular_user_data = None
        for customer in response.data['results']:
            if customer['email'] == 'regular@example.com':
                regular_user_data = customer
                break

        self.assertIsNotNone(regular_user_data)
        self.assertEqual(regular_user_data['customer_status'], 'active')

    def test_customer_status_inactive_for_no_booking(self):
        """Broni joq mijoz aktiv dep belgilenetuǵının testlew (jańa mijoz)."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Nátiyjelerde customer2 ni tabıw (broni joq)
        customer2_data = None
        for customer in response.data['results']:
            if customer['email'] == 'customer2@example.com':
                customer2_data = customer
                break

        self.assertIsNotNone(customer2_data)
        # Broni joq mijoz aktiv bolıwı kerek (jańa mijoz)
        self.assertEqual(customer2_data['customer_status'], 'active')

    def test_contact_method_fields_returned(self):
        """Baylanıs usılı maydanları durıs qaytarılatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Nátiyjelerde regular_user dı tabıw
        regular_user_data = None
        for customer in response.data['results']:
            if customer['email'] == 'regular@example.com':
                regular_user_data = customer
                break

        self.assertIsNotNone(regular_user_data)
        self.assertEqual(regular_user_data['whatsapp'], '+998901234567')
        self.assertEqual(regular_user_data['telegram'], '@regularuser')
        self.assertEqual(regular_user_data['preferred_contact_method'], 'whatsapp')

    def test_invalid_sort_field_defaults_to_registration_date(self):
        """Jaramsız tártiplew maydanı registration_date ǵa qaytatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/?sort_by=invalid_field')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ádetdegi tártiplew menen ele nátiyjeler qaytıwı kerek

    def test_invalid_sort_order_defaults_to_desc(self):
        """Jaramsız tártiplew baǵıtı desc ke qaytatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/?sort_order=invalid')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def _directory_emails(self, query=''):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{query}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return [customer['email'] for customer in response.data['results']]

    def test_staff_and_superusers_are_not_listed(self):
        """Tek mijozlar dizimlenedi; staff hám super-admin ler emes."""
        superuser_only = User.objects.create_user(
            email='root@example.com', password='testpassword123', is_superuser=True
        )

        emails = self._directory_emails('?page_size=100')

        self.assertIn('regular@example.com', emails)
        self.assertIn('customer2@example.com', emails)
        self.assertNotIn('admin@example.com', emails)
        self.assertNotIn('staff@example.com', emails)
        self.assertNotIn(superuser_only.email, emails)
        self.assertEqual(len(emails), 2)

    def test_aggregates_are_not_multiplied_by_joins(self):
        """Bir mijozdıń bir neshe broni hárbiri bir márte esaplanadı."""
        Booking.objects.create(
            guest=self.regular_user,
            property=self.property,
            status='confirmed',
            payment_status='paid',
            check_in=date.today() + timedelta(days=20),
            check_out=date.today() + timedelta(days=22),
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('150.00'),
            currency='USD',
        )

        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/?search=regular@example.com')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        customer = response.data['results'][0]
        self.assertEqual(customer['total_booking_count'], 2)

    def test_sorting_and_pagination_happen_in_the_database(self):
        """Bet barlıq paydalanıwshını jaddıǵa júklewdiń ornına LIMIT penen alınadı."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        self.client.force_authenticate(user=self.super_admin)

        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(
                '/api/v1/admin-panel/customers/?page_size=1&sort_by=total_booking_count'
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual([c['email'] for c in response.data['results']], ['regular@example.com'])
        user_queries = [q['sql'] for q in ctx.captured_queries if 'FROM "users"' in q['sql']]
        self.assertTrue(any('LIMIT' in sql for sql in user_queries), user_queries)

    def test_sorting_by_full_name_uses_display_name(self):
        """full_name boyınsha tártiplew kórsetilgen atqa ılayıq (full_name, bolmasa first + last, bolmasa email), register ti
        esapqa almay."""
        User.objects.create_user(email='zed@example.com', password='testpassword123', full_name='Aaron Zed')
        User.objects.create_user(email='anon@example.com', password='testpassword123')

        emails = self._directory_emails('?sort_by=full_name&sort_order=asc')

        # Kórsetiletuǵın atlar: 'Aaron Zed', 'anon@example.com', 'Customer Two', 'Regular User'
        self.assertEqual(
            emails,
            ['zed@example.com', 'anon@example.com', 'customer2@example.com', 'regular@example.com'],
        )

    def test_sorting_by_customer_status(self):
        """Aktiv emes mijozlar ósiw tártibinde aktivlerden keyin turadı."""
        self.customer2.is_active = False
        self.customer2.save()

        self.assertEqual(
            self._directory_emails('?sort_by=customer_status&sort_order=asc'),
            ['regular@example.com', 'customer2@example.com'],
        )
        self.assertEqual(
            self._directory_emails('?sort_by=customer_status&sort_order=desc'),
            ['customer2@example.com', 'regular@example.com'],
        )
        # Ádetdegi tártiplew menen ele nátiyjeler qaytıwı kerek


class AdminCustomerDetailTests(TestCase):
    """Admin mijoz tolıq maǵlıwmatı API endpoint i ushın testler."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.client = APIClient()

        # Super-admin paydalanıwshı jaratıw
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )

        # Staff paydalanıwshı jaratıw
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )

        # Ápiwayı paydalanıwshı (mijoz) jaratıw
        self.customer = User.objects.create_user(
            email='customer@example.com',
            password='testpassword123',
            first_name='Customer',
            last_name='Test',
            phone_number='+998901234567',
            whatsapp='+998901234567',
            telegram='@customer',
            preferred_contact_method='whatsapp'
        )

        # Mehmanxana túrin hám mehmanxananı jaratıw
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment',
            description='Apartment property type'
        )

        self.property = Property.objects.create(
            owner=self.super_admin,
            property_type=self.property_type,
            status='active',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Main St',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00'),
            currency='USD'
        )

        # Xona túrin hám rate plan dı jaratıw
        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('100.00'),
            currency='USD',
            total_rooms=5
        )

        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type,
            name='Standard Rate',
            slug='standard-rate',
            rate_type='standard',
            base_price=Decimal('100.00'),
            currency='USD',
            min_nights=1,
            max_nights=30,
            is_active=True
        )

        # Túrli statuslı bronlardı jaratıw
        self.booking_confirmed = Booking.objects.create(
            guest=self.customer,
            property=self.property,
            status='confirmed',
            payment_status='paid',
            check_in=date.today() + timedelta(days=10),
            check_out=date.today() + timedelta(days=12),
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD',
            guest_full_name='Customer Test',
            guest_phone='+998901234567',
            guest_email='customer@example.com',
            number_of_rooms=1,
            children=[]
        )

        BookingItem.objects.create(
            booking=self.booking_confirmed,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            number_of_rooms=1,
            price_per_night=Decimal('100.00'),
            currency='USD'
        )

        self.booking_completed = Booking.objects.create(
            guest=self.customer,
            property=self.property,
            status='completed',
            payment_status='paid',
            check_in=date.today() - timedelta(days=20),
            check_out=date.today() - timedelta(days=18),
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD',
            guest_full_name='Customer Test',
            guest_phone='+998901234567',
            guest_email='customer@example.com',
            number_of_rooms=1,
            children=[]
        )

        BookingItem.objects.create(
            booking=self.booking_completed,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            number_of_rooms=1,
            price_per_night=Decimal('100.00'),
            currency='USD'
        )

        self.booking_cancelled = Booking.objects.create(
            guest=self.customer,
            property=self.property,
            status='cancelled',
            payment_status='refunded',
            check_in=date.today() - timedelta(days=30),
            check_out=date.today() - timedelta(days=28),
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD',
            guest_full_name='Customer Test',
            guest_phone='+998901234567',
            guest_email='customer@example.com',
            number_of_rooms=1,
            children=[]
        )

        BookingItem.objects.create(
            booking=self.booking_cancelled,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            number_of_rooms=1,
            price_per_night=Decimal('100.00'),
            currency='USD'
        )

        # Ishki jazbalardı jaratıw
        self.note1 = InternalNote.objects.create(
            customer=self.customer,
            author=self.super_admin,
            note='VIP customer - treat with special care'
        )

        self.note2 = InternalNote.objects.create(
            customer=self.customer,
            author=self.staff_user,
            note='Prefers WhatsApp communication'
        )

    def test_super_admin_can_access_customer_detail(self):
        """Super-admin mijoz tolıq maǵlıwmatına kire alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('customer', response.data)
        self.assertIn('bookings', response.data)
        self.assertNotIn('payments', response.data)
        self.assertIn('internal_notes', response.data)
        self.assertIn('last_activity', response.data)

    def test_staff_can_access_customer_detail(self):
        """Staff mijoz tolıq maǵlıwmatına kire alatuǵının testlew."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('customer', response.data)

    def test_regular_user_cannot_access_customer_detail(self):
        """Ápiwayı paydalanıwshı mijoz tolıq maǵlıwmatına kire almaytuǵının testlew."""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_detail_returns_contact_info(self):
        """Mijoz tolıq maǵlıwmatı tolıq baylanıs maǵlıwmatın qaytaratuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        customer_data = response.data['customer']
        self.assertEqual(customer_data['id'], self.customer.id)
        self.assertEqual(customer_data['email'], 'customer@example.com')
        self.assertEqual(customer_data['phone_number'], '+998901234567')
        self.assertEqual(customer_data['whatsapp'], '+998901234567')
        self.assertEqual(customer_data['telegram'], '@customer')
        self.assertEqual(customer_data['preferred_contact_method'], 'whatsapp')

    def test_customer_detail_returns_all_bookings(self):
        """Mijoz tolıq maǵlıwmatı ádetde barlıq bronlardı qaytaratuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bookings = response.data['bookings']
        self.assertEqual(len(bookings), 3)

    def test_customer_detail_filters_upcoming_bookings(self):
        """Mijoz tolıq maǵlıwmatı keletuǵın bronlardı filterley alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/?booking_filter=upcoming')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bookings = response.data['bookings']
        self.assertEqual(len(bookings), 1)
        self.assertEqual(bookings[0]['status'], 'confirmed')

    def test_upcoming_follows_the_business_day_not_the_utc_day(self):
        """21:00 UTC te Tashkent te ol aldınan keyingi kúnniń 02:00 i: sol kúni baslanǵan turıw endi keletuǵın emes."""
        Booking.objects.filter(pk=self.booking_confirmed.pk).update(check_in=date(2026, 11, 10), check_out=date(2026, 11, 12))
        self.client.force_authenticate(user=self.super_admin)
        at = datetime(2026, 11, 10, 21, 0, tzinfo=dt_timezone.utc)
        with mock.patch('django.utils.timezone.now', return_value=at):
            response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/?booking_filter=upcoming')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bookings'], [])

    def test_customer_detail_filters_completed_bookings(self):
        """Mijoz tolıq maǵlıwmatı juwmaqlanǵan bronlardı filterley alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/?booking_filter=completed')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bookings = response.data['bookings']
        self.assertEqual(len(bookings), 1)
        self.assertEqual(bookings[0]['status'], 'completed')

    def test_customer_detail_filters_cancelled_bookings(self):
        """Mijoz tolıq maǵlıwmatı biykar etilgen bronlardı filterley alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/?booking_filter=cancelled')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bookings = response.data['bookings']
        self.assertEqual(len(bookings), 1)
        self.assertEqual(bookings[0]['status'], 'cancelled')

    def test_customer_detail_returns_internal_notes(self):
        """Mijoz tolıq maǵlıwmatı ishki jazbalardı qaytaratuǵının testlew."""
        # Jaratıw tártibin anıq etiw (eki jazba da setUp te jaratıladı)
        InternalNote.objects.filter(pk=self.note1.pk).update(created_at=timezone.now() - timedelta(hours=1))
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notes = response.data['internal_notes']
        self.assertEqual(len(notes), 2)
        # Eń jańası birinshi: WhatsApp jazbası (note2) VIP jazbasınan keyin qosılǵan
        self.assertIn('Prefers WhatsApp', notes[0]['note'])
        self.assertIn('VIP customer', notes[1]['note'])

    def test_customer_detail_returns_last_activity(self):
        """Mijoz tolıq maǵlıwmatı sońǵı aktivlik waqıt belgisin qaytaratuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('last_activity', response.data)
        self.assertIsNotNone(response.data['last_activity'])

    def test_customer_detail_not_found(self):
        """Joq mijoz ushın tolıq maǵlıwmat 404 qaytaratuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/99999/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminInternalNotesTests(TestCase):
    """Admin ishki jazbalar CRUD ámelleri ushın testler."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.client = APIClient()

        # Super-admin paydalanıwshı jaratıw
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )

        # Staff paydalanıwshı jaratıw
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )

        # Ápiwayı paydalanıwshı (mijoz) jaratıw
        self.customer = User.objects.create_user(
            email='customer@example.com',
            password='testpassword123',
            first_name='Customer',
            last_name='Test'
        )

        # Dáslepki ishki jazbanı jaratıw
        self.note = InternalNote.objects.create(
            customer=self.customer,
            author=self.super_admin,
            note='Initial note'
        )

    def test_staff_can_create_internal_note(self):
        """Staff ishki jazba jarata alatuǵının testlew."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/',
            {'note': 'New note from staff'}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['note'], 'New note from staff')
        self.assertEqual(response.data['author_email'], 'staff@example.com')

    def test_super_admin_can_create_internal_note(self):
        """Super-admin ishki jazba jarata alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.post(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/',
            {'note': 'New note from admin'}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['note'], 'New note from admin')

    def test_note_is_created_for_customer_in_url_not_body(self):
        """Mijoz URL den keledi; denedegi mijoz id si itibarǵa alınbaydı."""
        other_customer = User.objects.create_user(email='other-customer@example.com', password='testpassword123')
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/',
            {'note': 'Body names another customer', 'customer': other_customer.id}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['customer'], self.customer.id)
        self.assertFalse(InternalNote.objects.filter(customer=other_customer).exists())

    def test_note_cannot_be_moved_to_another_customer(self):
        """Jazbanı ózgertiw onı basqa mijozǵa ótkize almaydı."""
        other_customer = User.objects.create_user(email='other-customer@example.com', password='testpassword123')
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.put(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/{self.note.id}/',
            {'note': 'Edited', 'customer': other_customer.id}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.note.refresh_from_db()
        self.assertEqual(self.note.customer_id, self.customer.id)
        self.assertEqual(self.note.note, 'Edited')

    def test_note_author_cannot_be_changed(self):
        """Jazbanı ózgertiw kim jazǵanın qayta jaza almaydı."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.put(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/{self.note.id}/',
            {'note': 'Edited', 'author': self.staff_user.id}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.note.refresh_from_db()
        self.assertEqual(self.note.author_id, self.super_admin.id)
        self.assertEqual(self.note.note, 'Edited')

    def test_note_author_only_update_leaves_note_untouched(self):
        """Jazba PUT i bólekleyin; tek author bar dene avtordı ózgertpewi kerek."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.put(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/{self.note.id}/',
            {'author': self.staff_user.id}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.note.refresh_from_db()
        self.assertEqual(self.note.author_id, self.super_admin.id)
        self.assertEqual(response.data['author_email'], 'admin@example.com')

    def test_regular_user_cannot_create_internal_note(self):
        """Ápiwayı paydalanıwshı ishki jazba jarata almaytuǵının testlew."""
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/',
            {'note': 'Should not work'}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_note_requires_note_content(self):
        """Jazba jaratıw jazba mazmunın talap etetuǵının testlew."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/',
            {}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_can_update_internal_note(self):
        """Staff ishki jazbanı jańalay alatuǵının testlew."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.put(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/{self.note.id}/',
            {'note': 'Updated note content'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['note'], 'Updated note content')

    def test_staff_can_delete_internal_note(self):
        """Staff ishki jazbanı óshire alatuǵının testlew."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.delete(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/{self.note.id}/'
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Jazba soft-delete etilgenin tekseriw
        self.note.refresh_from_db()
        self.assertTrue(self.note.is_deleted)

    def test_regular_user_cannot_update_internal_note(self):
        """Ápiwayı paydalanıwshı ishki jazbanı jańalay almaytuǵının testlew."""
        self.client.force_authenticate(user=self.customer)
        response = self.client.put(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/{self.note.id}/',
            {'note': 'Should not work'}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_delete_internal_note(self):
        """Ápiwayı paydalanıwshı ishki jazbanı óshire almaytuǵının testlew."""
        self.client.force_authenticate(user=self.customer)
        response = self.client.delete(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/{self.note.id}/'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_access_note_for_different_customer(self):
        """Paydalanıwshı basqa mijozdıń jazbasına kire almaytuǵının testlew."""
        other_customer = User.objects.create_user(
            email='other@example.com',
            password='testpassword123',
            first_name='Other',
            last_name='Customer'
        )

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.put(
            f'/api/v1/admin-panel/customers/{other_customer.id}/notes/{self.note.id}/',
            {'note': 'Should not work'}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_author_name_in_note_response(self):
        """Jazba juwabı avtor atın óz ishine alatuǵının testlew."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notes = response.data['internal_notes']
        self.assertEqual(notes[0]['author_name'], 'Admin User')
        self.assertEqual(notes[0]['author_email'], 'admin@example.com')


class AdminStatisticsTests(TestCase):
    """Admin statistika endpoint leri ushın testler."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.client = APIClient()

        # Super-admin paydalanıwshı jaratıw
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )

        # Staff paydalanıwshı jaratıw
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )

        # Ápiwayı paydalanıwshı jaratıw
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='testpassword123',
            first_name='Regular',
            last_name='User'
        )

        # Mehmanxana túrin hám mehmanxananı jaratıw
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment',
            description='Apartment property type'
        )

        self.property = Property.objects.create(
            owner=self.super_admin,
            property_type=self.property_type,
            status='active',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Main St',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00'),
            currency='USD'
        )

        # Xona túrin hám rate plan dı jaratıw
        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('100.00'),
            currency='USD',
            total_rooms=5
        )

        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type,
            name='Standard Rate',
            slug='standard-rate',
            rate_type='standard',
            base_price=Decimal('100.00'),
            currency='USD',
            min_nights=1,
            max_nights=30,
            is_active=True
        )

        # Statistika ushın túrli dizimnen ótiw sanalı paydalanıwshılardı jaratıw
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpassword123',
            first_name='User',
            last_name='One'
        )
        self.user1.date_joined = timezone.now() - timedelta(days=30)
        self.user1.save()

        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpassword123',
            first_name='User',
            last_name='Two'
        )
        self.user2.date_joined = timezone.now() - timedelta(days=60)
        self.user2.save()

        self.user3 = User.objects.create_user(
            email='user3@example.com',
            password='testpassword123',
            first_name='User',
            last_name='Three'
        )
        self.user3.date_joined = timezone.now() - timedelta(days=400)  # Bir jıldan aldın
        self.user3.save()

        # Reyting testleri ushın bronlar jaratıw
        self.booking1 = Booking.objects.create(
            guest=self.user1,
            property=self.property,
            status='completed',
            payment_status='paid',
            check_in=date.today() - timedelta(days=5),
            check_out=date.today() - timedelta(days=3),
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD',
            guest_full_name='User One',
            guest_phone='+998901234567',
            guest_email='user1@example.com',
            number_of_rooms=1,
            children=[]
        )

        BookingItem.objects.create(
            booking=self.booking1,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            number_of_rooms=1,
            price_per_night=Decimal('100.00'),
            currency='USD'
        )

        self.booking2 = Booking.objects.create(
            guest=self.user1,
            property=self.property,
            status='completed',
            payment_status='paid',
            check_in=date.today() - timedelta(days=10),
            check_out=date.today() - timedelta(days=8),
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD',
            guest_full_name='User One',
            guest_phone='+998901234567',
            guest_email='user1@example.com',
            number_of_rooms=1,
            children=[]
        )

        BookingItem.objects.create(
            booking=self.booking2,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            number_of_rooms=1,
            price_per_night=Decimal('100.00'),
            currency='USD'
        )

        self.booking3 = Booking.objects.create(
            guest=self.user2,
            property=self.property,
            status='completed',
            payment_status='paid',
            check_in=date.today() - timedelta(days=15),
            check_out=date.today() - timedelta(days=13),
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD',
            guest_full_name='User Two',
            guest_phone='+998901234568',
            guest_email='user2@example.com',
            number_of_rooms=1,
            children=[]
        )

        BookingItem.objects.create(
            booking=self.booking3,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            number_of_rooms=1,
            price_per_night=Decimal('100.00'),
            currency='USD'
        )

        # Biykar etilgen bron jaratıw (reytingte esaplanbawı kerek)
        self.booking_cancelled = Booking.objects.create(
            guest=self.user2,
            property=self.property,
            status='cancelled',
            payment_status='refunded',
            check_in=date.today() - timedelta(days=20),
            check_out=date.today() - timedelta(days=18),
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD',
            guest_full_name='User Two',
            guest_phone='+998901234568',
            guest_email='user2@example.com',
            number_of_rooms=1,
            children=[]
        )

        BookingItem.objects.create(
            booking=self.booking_cancelled,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            number_of_rooms=1,
            price_per_night=Decimal('100.00'),
            currency='USD'
        )

    def test_super_admin_can_access_registration_statistics(self):
        """Super-admin dizimnen ótiw statistikasına kire alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/registrations/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('type', response.data)
        self.assertIn('statistics', response.data)

    def test_staff_can_access_registration_statistics(self):
        """Staff dizimnen ótiw statistikasına kire alatuǵının testlew."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin-panel/statistics/registrations/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_access_registration_statistics(self):
        """Ápiwayı paydalanıwshı dizimnen ótiw statistikasına kire almaytuǵının testlew."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/admin-panel/statistics/registrations/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_access_registration_statistics(self):
        """Kirmegen paydalanıwshı dizimnen ótiw statistikasına kire almaytuǵının testlew."""
        response = self.client.get('/api/v1/admin-panel/statistics/registrations/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_registration_statistics_rolling_12_months(self):
        """Júrip turatuǵın 12 ay aynası ushın dizimnen ótiw statistikasın testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/registrations/?type=rolling_12_months')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'rolling_12_months')
        self.assertIn('start_date', response.data)
        self.assertIn('end_date', response.data)
        self.assertIn('statistics', response.data)
        self.assertIsInstance(response.data['statistics'], list)

    def test_registration_statistics_calendar_year(self):
        """Kalendar jıl ushın dizimnen ótiw statistikasın testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/registrations/?type=calendar_year')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'calendar_year')
        self.assertIn('statistics', response.data)
        self.assertIsInstance(response.data['statistics'], list)

    def test_registration_statistics_defaults_to_rolling_12_months(self):
        """Dizimnen ótiw statistikası ádetde júrip turatuǵın 12 ay aynasın paydalanatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/registrations/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'rolling_12_months')

    def test_registration_statistics_no_registrations_in_period(self):
        """Dáwirde dizimnen ótiw joq bolǵanda dizimnen ótiw statistikasın testlew."""
        self.client.force_authenticate(user=self.super_admin)

        # Óshirilgen paydalanıwshı jaratıw
        deleted_user = User.objects.create_user(
            email='deleted@example.com',
            password='testpassword123',
            first_name='Deleted',
            last_name='User'
        )
        deleted_user.soft_delete()

        # Aktiv dizimnen ótiw joq dáwir ushın statistikanı alıw
        # Bul bos statistika shegaralıq jaǵdayın testleydi
        response = self.client.get('/api/v1/admin-panel/statistics/registrations/?type=calendar_year')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['statistics'], list)

    def test_super_admin_can_access_top_bookers_leaderboard(self):
        """Super-admin eń kóp bronlaǵan mijozlar reytingine kire alatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('period', response.data)
        self.assertIn('limit', response.data)
        self.assertIn('leaderboard', response.data)

    def test_staff_can_access_top_bookers_leaderboard(self):
        """Staff eń kóp bronlaǵan mijozlar reytingine kire alatuǵının testlew."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_access_top_bookers_leaderboard(self):
        """Ápiwayı paydalanıwshı eń kóp bronlaǵan mijozlar reytingine kire almaytuǵının testlew."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_access_top_bookers_leaderboard(self):
        """Kirmegen paydalanıwshı eń kóp bronlaǵan mijozlar reytingine kire almaytuǵının testlew."""
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_top_bookers_leaderboard_all_time(self):
        """Pútkil waqıt dáwiri ushın eń kóp bronlaǵan mijozlar reytingin testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?period=all_time')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['period'], 'all_time')
        self.assertIn('leaderboard', response.data)
        self.assertIsInstance(response.data['leaderboard'], list)

        # user1 joqarıda ekenin tekseriw (2 juwmaqlanǵan bron)
        if response.data['leaderboard']:
            self.assertEqual(response.data['leaderboard'][0]['customer_name'], 'User One')
            self.assertEqual(response.data['leaderboard'][0]['completed_booking_count'], 2)

    def test_top_bookers_leaderboard_this_month(self):
        """Usı ay dáwiri ushın eń kóp bronlaǵan mijozlar reytingin testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?period=this_month')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['period'], 'this_month')
        self.assertIn('leaderboard', response.data)

    def test_top_bookers_leaderboard_this_year(self):
        """Usı jıl dáwiri ushın eń kóp bronlaǵan mijozlar reytingin testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?period=this_year')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['period'], 'this_year')
        self.assertIn('leaderboard', response.data)

    def test_top_bookers_leaderboard_defaults_to_all_time(self):
        """Eń kóp bronlaǵan mijozlar reytingi ádetde pútkil waqıt ekenin testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['period'], 'all_time')

    def test_top_bookers_leaderboard_limit_parameter(self):
        """limit parametri durıs islewin testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?limit=2')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['limit'], 2)
        self.assertLessEqual(len(response.data['leaderboard']), 2)

    def test_top_bookers_leaderboard_limit_max_constraint(self):
        """limit parametri 100 lik eń kóp shekke boysınatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?limit=200')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['limit'], 100)

    def test_top_bookers_leaderboard_invalid_limit_defaults(self):
        """Jaramsız limit parametri 10 ǵa qaytatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?limit=invalid')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['limit'], 10)

    def test_top_bookers_leaderboard_only_completed_bookings(self):
        """Reytingte tek juwmaqlanǵan bronlar esaplanatuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?period=all_time')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # user2 de 1 juwmaqlanǵan hám 1 biykar etilgen bron bar
        # Tek juwmaqlanǵanı esaplanıwı kerek
        user2_entry = None
        for entry in response.data['leaderboard']:
            if entry['customer_name'] == 'User Two':
                user2_entry = entry
                break

        self.assertIsNotNone(user2_entry)
        self.assertEqual(user2_entry['completed_booking_count'], 1)

    def test_top_bookers_leaderboard_no_bookings_in_period(self):
        """Dáwirde bron joq bolǵanda reytingti testlew."""
        self.client.force_authenticate(user=self.super_admin)

        # Usı ay ushın reytingti sorawlaw, usı ayda bronlarımız joq bolǵanda
        # (test bronlarımız aldınǵı kúnlerden/aylardan)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?period=this_month')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['leaderboard'], list)
        # Usı ayda bron joq bolsa bos bolıwı múmkin

    def test_top_bookers_leaderboard_ranking_order(self):
        """Reytingtiń bron sanı boyınsha durıs reytingleniwin testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?period=all_time')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Jazbalar bron sanı boyınsha kemeyiw tártibinde ekenin tekseriw
        leaderboard = response.data['leaderboard']
        for i in range(len(leaderboard) - 1):
            self.assertGreaterEqual(
                leaderboard[i]['completed_booking_count'],
                leaderboard[i + 1]['completed_booking_count']
            )

    def test_top_bookers_leaderboard_rank_field(self):
        """Reyting jazbalarında rank maydanı barlıǵın testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?period=all_time')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Jazbalarda rank maydanı 1 den baslanatuǵının tekseriw
        if response.data['leaderboard']:
            self.assertEqual(response.data['leaderboard'][0]['rank'], 1)
            if len(response.data['leaderboard']) > 1:
                self.assertEqual(response.data['leaderboard'][1]['rank'], 2)

    def test_top_bookers_leaderboard_sensitive_data_not_leaked(self):
        """Reyting mijozdıń jasırın maǵlıwmatın sızdırmaytuǵının testlew."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?period=all_time')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Tek kerekli maydanlar qaytarılǵanın tekseriw
        if response.data['leaderboard']:
            entry = response.data['leaderboard'][0]
            self.assertIn('rank', entry)
            self.assertIn('customer_id', entry)
            self.assertIn('customer_name', entry)
            self.assertIn('completed_booking_count', entry)

            # Jasırın maǵlıwmat BOLMAWI kerek
            self.assertNotIn('email', entry)
            self.assertNotIn('phone_number', entry)
            self.assertNotIn('address', entry)

"""
Tests for admin API endpoints.

This module contains tests for property moderation, user management,
amenity management, and payment monitoring.
"""
import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from properties.models import Property, PropertyType, Amenity, AmenityCategory, RoomType, RatePlan
from permissions.models import Role
from bookings.models import Booking, BookingItem
from admin_panel.models import InternalNote
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

User = get_user_model()


class AdminPropertyTests(TestCase):
    """Tests for admin property moderation endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create super-admin user
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='testpassword123',
            first_name='Regular',
            last_name='User'
        )
        
        # Create property type and property
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
    
    def test_super_admin_can_list_all_properties(self):
        """Test that super-admin can list all properties."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/properties/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that at least our test property is in the list (paginated response)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        property_ids = [prop['id'] for prop in results]
        self.assertIn(self.property.id, property_ids)
    
    def test_staff_can_list_all_properties(self):
        """Test that staff can list all properties."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin-panel/properties/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that at least our test property is in the list (paginated response)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        property_ids = [prop['id'] for prop in results]
        self.assertIn(self.property.id, property_ids)
    
    def test_regular_user_cannot_list_admin_properties(self):
        """Test that regular user cannot access admin property endpoints."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/admin-panel/properties/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_super_admin_can_approve_property(self):
        """Test that super-admin can approve property."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.post(f'/api/v1/admin-panel/properties/{self.property.id}/approve/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, 'active')
        self.assertEqual(self.property.approved_by, self.super_admin)
        self.assertIsNotNone(self.property.approved_at)
    
    def test_staff_can_approve_property(self):
        """Test that staff can approve property."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(f'/api/v1/admin-panel/properties/{self.property.id}/approve/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, 'active')
    
    def test_admin_can_reject_property_with_reason(self):
        """Test that admin can reject property with reason."""
        self.client.force_authenticate(user=self.super_admin)
        data = {'rejection_reason': 'Property does not meet standards'}
        response = self.client.post(f'/api/v1/admin-panel/properties/{self.property.id}/approve/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, 'rejected')
        self.assertEqual(self.property.rejection_reason, 'Property does not meet standards')
    
    def test_admin_can_suspend_property(self):
        """Test that admin can suspend property."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.post(f'/api/v1/admin-panel/properties/{self.property.id}/suspend/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, 'suspended')


class AdminUserTests(TestCase):
    """Tests for admin user management endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create super-admin user
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='testpassword123',
            first_name='Regular',
            last_name='User'
        )
    
    def test_super_admin_can_list_all_users(self):
        """Test that super-admin can list all users."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
    
    def test_staff_can_list_all_users(self):
        """Test that staff can list all users."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin-panel/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
    
    def test_regular_user_cannot_list_admin_users(self):
        """Test that regular user cannot access admin user endpoints."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/admin-panel/users/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_super_admin_can_create_hotel_owner_account(self):
        """Test that super-admin can create hotel-owner account."""
        self.client.force_authenticate(user=self.super_admin)
        data = {
            'email': 'hotelowner@example.com',
            'first_name': 'Hotel',
            'last_name': 'Owner',
            'phone_number': '+998901234567',
            'password': 'Owner#Secret2026',
            'password_confirm': 'Owner#Secret2026'
        }
        response = self.client.post('/api/v1/admin-panel/users/create-hotel-owner/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 4)
        
        # Verify user has hotel-owner role
        new_user = User.objects.get(email='hotelowner@example.com')
        self.assertEqual(new_user.role.name, 'hotel-owner')
    
    def test_staff_cannot_create_hotel_owner_account(self):
        """Test that staff cannot create hotel-owner account."""
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
    
    def test_password_mismatch_validation(self):
        """Test that password mismatch is validated."""
        self.client.force_authenticate(user=self.super_admin)
        data = {
            'email': 'hotelowner3@example.com',
            'first_name': 'Hotel',
            'last_name': 'Owner',
            'password': 'testpassword123',
            'password_confirm': 'differentpassword'
        }
        response = self.client.post('/api/v1/admin-panel/users/create-hotel-owner/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)
    
    def test_password_not_returned_in_response(self):
        """Test that password is not returned in response."""
        self.client.force_authenticate(user=self.super_admin)
        data = {
            'email': 'hotelowner4@example.com',
            'first_name': 'Hotel',
            'last_name': 'Owner',
            'password': 'Owner#Secret2026',
            'password_confirm': 'Owner#Secret2026'
        }
        response = self.client.post('/api/v1/admin-panel/users/create-hotel-owner/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', response.data)
        self.assertNotIn('password_confirm', response.data)


class AdminAmenityTests(TestCase):
    """Tests for admin amenity management endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create super-admin user
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='testpassword123',
            first_name='Regular',
            last_name='User'
        )
        
        # Create amenity category
        self.amenity_category = AmenityCategory.objects.create(
            name='Kitchen',
            slug='kitchen',
            description='Kitchen amenities',
            sort_order=1
        )
        
        # Create amenity
        self.amenity = Amenity.objects.create(
            category=self.amenity_category,
            name='WiFi',
            slug='wifi',
            description='Wireless internet',
            is_searchable=True,
            sort_order=1
        )
    
    def test_super_admin_can_list_all_amenities(self):
        """Test that super-admin can list all amenities."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/amenities/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that at least our test amenity is in the list (paginated response)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        amenity_ids = [amenity['id'] for amenity in results]
        self.assertIn(self.amenity.id, amenity_ids)
    
    def test_staff_can_list_all_amenities(self):
        """Test that staff can list all amenities."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin-panel/amenities/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that at least our test amenity is in the list (paginated response)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        amenity_ids = [amenity['id'] for amenity in results]
        self.assertIn(self.amenity.id, amenity_ids)
    
    def test_regular_user_cannot_list_admin_amenities(self):
        """Test that regular user cannot access admin amenity endpoints."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/admin-panel/amenities/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_super_admin_can_create_amenity(self):
        """Test that super-admin can create amenity."""
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
        """Test that super-admin can update amenity."""
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
        """Test that super-admin can delete amenity (soft delete)."""
        self.client.force_authenticate(user=self.super_admin)
        amenity_id = self.amenity.id
        response = self.client.delete(f'/api/v1/admin-panel/amenities/{amenity_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Check that amenity is no longer in the active queryset
        self.assertFalse(Amenity.objects.filter(id=amenity_id).exists())
    
    def test_super_admin_can_manage_amenity_categories(self):
        """Test that super-admin can manage amenity categories."""
        self.client.force_authenticate(user=self.super_admin)
        
        # Create category
        data = {
            'name': 'Bathroom',
            'slug': 'bathroom',
            'description': 'Bathroom amenities',
            'sort_order': 2
        }
        response = self.client.post('/api/v1/admin-panel/amenities/categories/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AmenityCategory.objects.count(), 2)


class AdminPaymentTests(TestCase):
    """Tests for admin payment monitoring endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create super-admin user
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='testpassword123',
            first_name='Regular',
            last_name='User'
        )
    
    def test_super_admin_can_list_payment_transactions(self):
        """Test that super-admin can list payment transactions."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/payments/transactions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return empty list if no transactions exist
        self.assertEqual(response.data, [])
    
    def test_staff_can_list_payment_transactions(self):
        """Test that staff can list payment transactions."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin-panel/payments/transactions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_regular_user_cannot_list_payment_transactions(self):
        """Test that regular user cannot access admin payment endpoints."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/admin-panel/payments/transactions/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_can_filter_transactions_by_status(self):
        """Test that admin can filter transactions by status."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/payments/transactions/?status=completed')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_admin_can_filter_transactions_by_provider(self):
        """Test that admin can filter transactions by provider."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/payments/transactions/?provider=payme')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminPermissionTests(TestCase):
    """Tests for admin permission scoping."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create super-admin user
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='testpassword123',
            first_name='Regular',
            last_name='User'
        )
    
    def test_unauthenticated_user_cannot_access_admin_endpoints(self):
        """Test that unauthenticated users cannot access admin endpoints."""
        endpoints = [
            '/api/v1/admin-panel/properties/',
            '/api/v1/admin-panel/users/',
            '/api/v1/admin-panel/amenities/',
            '/api/v1/admin-panel/payments/transactions/'
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            # DRF returns 403 for unauthenticated users when authentication is required
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_non_staff_user_cannot_access_admin_endpoints(self):
        """Test that non-staff users cannot access admin endpoints."""
        self.client.force_authenticate(user=self.regular_user)
        endpoints = [
            '/api/v1/admin-panel/properties/',
            '/api/v1/admin-panel/users/',
            '/api/v1/admin-panel/amenities/',
            '/api/v1/admin-panel/payments/transactions/'
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_non_superuser_cannot_create_hotel_owner(self):
        """Test that non-superuser cannot create hotel-owner account."""
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
    """Tests for admin booking lookup by reference code endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create super-admin user
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='testpassword123',
            first_name='Regular',
            last_name='User'
        )
        
        # Create property type and property
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
        
        # Create room type and rate plan
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
        
        # Create booking
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
        
        # Create booking item
        BookingItem.objects.create(
            booking=self.booking,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            number_of_rooms=1,
            price_per_night=Decimal('100.00'),
            currency='USD'
        )
    
    def test_super_admin_can_lookup_booking_by_reference_code(self):
        """Test that super-admin can lookup booking by reference code."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/bookings/lookup/?reference_code={self.booking.confirmation_code}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('booking', response.data)
        self.assertIn('customer', response.data)
        self.assertIn('property', response.data)
        
        # Verify booking details
        booking_data = response.data['booking']
        self.assertEqual(booking_data['reference_code'], self.booking.confirmation_code)
        self.assertEqual(booking_data['status'], 'confirmed')
        self.assertEqual(booking_data['payment_status'], 'paid')
        
        # Verify customer details
        customer_data = response.data['customer']
        self.assertEqual(customer_data['email'], 'regular@example.com')
        self.assertEqual(customer_data['full_name'], 'Regular User')
        
        # Verify property details
        property_data = response.data['property']
        self.assertEqual(property_data['id'], self.property.id)
        # The display name is the hotel name (translation); this property has none,
        # so it falls back to the address instead of a made-up "Property N - city" label
        self.assertEqual(
            property_data['name'],
            '123 Main St, Tashkent, Uzbekistan'
        )
    
    def test_staff_can_lookup_booking_by_reference_code(self):
        """Test that staff can lookup booking by reference code."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(f'/api/v1/admin-panel/bookings/lookup/?reference_code={self.booking.confirmation_code}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('booking', response.data)
    
    def test_regular_user_cannot_lookup_booking_by_reference_code(self):
        """Test that regular user cannot access booking lookup endpoint."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f'/api/v1/admin-panel/bookings/lookup/?reference_code={self.booking.confirmation_code}')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthenticated_user_cannot_lookup_booking(self):
        """Test that unauthenticated user cannot access booking lookup endpoint."""
        response = self.client.get(f'/api/v1/admin-panel/bookings/lookup/?reference_code={self.booking.confirmation_code}')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_lookup_with_missing_reference_code_parameter(self):
        """Test that missing reference_code parameter returns 400 error."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/bookings/lookup/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_lookup_with_invalid_reference_code(self):
        """Test that invalid reference code returns 404 error."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/bookings/lookup/?reference_code=INVALID')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_lookup_case_insensitive(self):
        """Test that reference code lookup is case-insensitive."""
        self.client.force_authenticate(user=self.super_admin)
        
        # Test with lowercase
        response = self.client.get(f'/api/v1/admin-panel/bookings/lookup/?reference_code={self.booking.confirmation_code.lower()}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['booking']['reference_code'], self.booking.confirmation_code)
    
    def test_lookup_returns_all_required_fields(self):
        """Test that lookup returns all required customer and booking details."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/bookings/lookup/?reference_code={self.booking.confirmation_code}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check booking fields
        booking_data = response.data['booking']
        required_booking_fields = [
            'id', 'reference_code', 'status', 'payment_status', 'check_in', 'check_out',
            'number_of_nights', 'guest_count', 'total_price', 'currency', 'special_requests',
            'guest_full_name', 'guest_phone', 'guest_email', 'number_of_rooms', 'children', 'booking_items'
        ]
        for field in required_booking_fields:
            self.assertIn(field, booking_data)
        
        # Check customer fields
        customer_data = response.data['customer']
        required_customer_fields = ['id', 'full_name', 'email', 'phone_number', 'whatsapp', 'telegram', 'preferred_contact_method']
        for field in required_customer_fields:
            self.assertIn(field, customer_data)
        
        # Check property fields
        property_data = response.data['property']
        required_property_fields = ['id', 'name', 'property_type', 'status', 'address_line1', 'city', 'state', 'country', 'base_price', 'currency', 'owner']
        for field in required_property_fields:
            self.assertIn(field, property_data)


class AdminCustomersDirectoryTests(TestCase):
    """Tests for admin customers directory API endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create super-admin user
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )
        
        # Create regular user
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
        
        # Create another customer user
        self.customer2 = User.objects.create_user(
            email='customer2@example.com',
            password='testpassword123',
            first_name='Customer',
            last_name='Two',
            phone_number='+998901234568'
        )
        
        # Create property type and property
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
        
        # Create room type and rate plan
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
        
        # Create booking for regular_user
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
        
        # Create payment transaction for booking1
        from payments.models import PaymentTransaction
        self.payment1 = PaymentTransaction.objects.create(
            idempotency_key='test-payment-1',
            booking=self.booking1,
            provider='payme',
            amount=Decimal('200.00'),
            currency='USD',
            status='completed'
        )
    
    def test_super_admin_can_access_customers_directory(self):
        """Test that super-admin can access customers directory."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIsInstance(response.data['results'], list)
    
    def test_staff_can_access_customers_directory(self):
        """Test that staff can access customers directory."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin-panel/customers/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_regular_user_cannot_access_customers_directory(self):
        """Test that regular user cannot access customers directory."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/admin-panel/customers/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthenticated_user_cannot_access_customers_directory(self):
        """Test that unauthenticated user cannot access customers directory."""
        response = self.client.get('/api/v1/admin-panel/customers/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_customers_directory_returns_required_fields(self):
        """Test that customers directory returns all required fields."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check first customer has all required fields
        if response.data['results']:
            customer_data = response.data['results'][0]
            required_fields = [
                'id', 'registration_date', 'full_name', 'phone', 'email',
                'whatsapp', 'telegram', 'preferred_contact_method',
                'total_booking_count', 'last_booking_date', 'total_amount_paid', 'customer_status'
            ]
            for field in required_fields:
                self.assertIn(field, customer_data)
    
    def test_customers_directory_includes_booking_aggregates(self):
        """Test that customers directory includes booking aggregates."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Find regular_user in results
        regular_user_data = None
        for customer in response.data['results']:
            if customer['email'] == 'regular@example.com':
                regular_user_data = customer
                break
        
        self.assertIsNotNone(regular_user_data)
        self.assertEqual(regular_user_data['total_booking_count'], 1)
        self.assertEqual(regular_user_data['total_amount_paid'], '200.00')  # DRF renders decimals as strings
        self.assertIsNotNone(regular_user_data['last_booking_date'])
    
    def test_search_by_name(self):
        """Test searching customers by name."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/?search=Regular')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should find regular_user
        found = False
        for customer in response.data['results']:
            if customer['email'] == 'regular@example.com':
                found = True
                break
        self.assertTrue(found)
    
    def test_search_by_email(self):
        """Test searching customers by email."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/?search=regular@example.com')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should find regular_user
        found = False
        for customer in response.data['results']:
            if customer['email'] == 'regular@example.com':
                found = True
                break
        self.assertTrue(found)
    
    def test_search_by_phone(self):
        """Test searching customers by phone."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/?search=+998901234567')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should find regular_user
        found = False
        for customer in response.data['results']:
            if customer['email'] == 'regular@example.com':
                found = True
                break
        self.assertTrue(found)
    
    def test_search_by_customer_id(self):
        """Test searching customers by customer ID."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/?search={self.regular_user.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should find regular_user
        found = False
        for customer in response.data['results']:
            if customer['id'] == self.regular_user.id:
                found = True
                break
        self.assertTrue(found)
    
    def test_pagination_works(self):
        """Test that pagination works correctly."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/?page_size=1')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        self.assertLessEqual(len(response.data['results']), 1)
    
    def test_sorting_by_registration_date(self):
        """Test sorting by registration date."""
        self.client.force_authenticate(user=self.super_admin)
        
        # Sort ascending
        response = self.client.get('/api/v1/admin-panel/customers/?sort_by=registration_date&sort_order=asc')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Sort descending
        response = self.client.get('/api/v1/admin-panel/customers/?sort_by=registration_date&sort_order=desc')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_sorting_by_total_booking_count(self):
        """Test sorting by total booking count."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/?sort_by=total_booking_count&sort_order=desc')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_sorting_by_total_amount_paid(self):
        """Test sorting by total amount paid."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/?sort_by=total_amount_paid&sort_order=desc')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_customer_status_active_for_recent_booking(self):
        """Test that customer with recent booking is marked as active."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Find regular_user in results
        regular_user_data = None
        for customer in response.data['results']:
            if customer['email'] == 'regular@example.com':
                regular_user_data = customer
                break
        
        self.assertIsNotNone(regular_user_data)
        self.assertEqual(regular_user_data['customer_status'], 'active')
    
    def test_customer_status_inactive_for_no_booking(self):
        """Test that customer with no bookings is marked as active (new customer)."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Find customer2 in results (has no bookings)
        customer2_data = None
        for customer in response.data['results']:
            if customer['email'] == 'customer2@example.com':
                customer2_data = customer
                break
        
        self.assertIsNotNone(customer2_data)
        # Customer with no bookings should be active (new customer)
        self.assertEqual(customer2_data['customer_status'], 'active')
    
    def test_contact_method_fields_returned(self):
        """Test that contact method fields are returned correctly."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Find regular_user in results
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
        """Test that invalid sort field defaults to registration_date."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/?sort_by=invalid_field')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should still return results with default sorting
    
    def test_invalid_sort_order_defaults_to_desc(self):
        """Test that invalid sort order defaults to desc."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/?sort_order=invalid')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def _directory_emails(self, query=''):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{query}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return [customer['email'] for customer in response.data['results']]

    def test_staff_and_superusers_are_not_listed(self):
        """Only customers are listed; staff and super-admins are not."""
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
        """Several payments on one booking must not inflate the booking count or the total."""
        from payments.models import PaymentTransaction
        booking2 = Booking.objects.create(
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
        # A failed attempt and two completed charges (e.g. a provider double charge)
        for key, txn_status in [
            ('test-payment-2a', 'failed'),
            ('test-payment-2b', 'completed'),
            ('test-payment-2c', 'completed'),
        ]:
            PaymentTransaction.objects.create(
                idempotency_key=key, booking=booking2, provider='payme',
                amount=Decimal('150.00'), currency='USD', status=txn_status,
            )

        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/?search=regular@example.com')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        customer = response.data['results'][0]
        self.assertEqual(customer['total_booking_count'], 2)
        # booking1: 200; booking2: two completed charges of 150
        self.assertEqual(customer['total_amount_paid'], '500.00')

    def test_sorting_and_pagination_happen_in_the_database(self):
        """The page is fetched with LIMIT instead of loading every user into memory."""
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
        """full_name sorting follows the displayed name (full_name, else first + last, else email), case-insensitively."""
        User.objects.create_user(email='zed@example.com', password='testpassword123', full_name='Aaron Zed')
        User.objects.create_user(email='anon@example.com', password='testpassword123')

        emails = self._directory_emails('?sort_by=full_name&sort_order=asc')

        # Display names: 'Aaron Zed', 'anon@example.com', 'Customer Two', 'Regular User'
        self.assertEqual(
            emails,
            ['zed@example.com', 'anon@example.com', 'customer2@example.com', 'regular@example.com'],
        )

    def test_sorting_by_customer_status(self):
        """Inactive customers sort after active ones in ascending order."""
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
        # Should still return results with default sorting


class AdminCustomerDetailTests(TestCase):
    """Tests for admin customer detail API endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create super-admin user
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )
        
        # Create regular user (customer)
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
        
        # Create property type and property
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
        
        # Create room type and rate plan
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
        
        # Create bookings with different statuses
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
        
        # Create payment transactions
        from payments.models import PaymentTransaction
        self.payment1 = PaymentTransaction.objects.create(
            idempotency_key='test-payment-1',
            booking=self.booking_confirmed,
            provider='payme',
            amount=Decimal('200.00'),
            currency='USD',
            status='completed'
        )
        
        self.payment2 = PaymentTransaction.objects.create(
            idempotency_key='test-payment-2',
            booking=self.booking_completed,
            provider='click',
            amount=Decimal('200.00'),
            currency='USD',
            status='completed'
        )
        
        # Create internal notes
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
        """Test that super-admin can access customer detail."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('customer', response.data)
        self.assertIn('bookings', response.data)
        self.assertIn('payments', response.data)
        self.assertIn('internal_notes', response.data)
        self.assertIn('last_activity', response.data)
    
    def test_staff_can_access_customer_detail(self):
        """Test that staff can access customer detail."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('customer', response.data)
    
    def test_regular_user_cannot_access_customer_detail(self):
        """Test that regular user cannot access customer detail."""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_customer_detail_returns_contact_info(self):
        """Test that customer detail returns full contact information."""
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
        """Test that customer detail returns all bookings by default."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bookings = response.data['bookings']
        self.assertEqual(len(bookings), 3)
    
    def test_customer_detail_filters_upcoming_bookings(self):
        """Test that customer detail can filter upcoming bookings."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/?booking_filter=upcoming')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bookings = response.data['bookings']
        self.assertEqual(len(bookings), 1)
        self.assertEqual(bookings[0]['status'], 'confirmed')
    
    def test_customer_detail_filters_completed_bookings(self):
        """Test that customer detail can filter completed bookings."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/?booking_filter=completed')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bookings = response.data['bookings']
        self.assertEqual(len(bookings), 1)
        self.assertEqual(bookings[0]['status'], 'completed')
    
    def test_customer_detail_filters_cancelled_bookings(self):
        """Test that customer detail can filter cancelled bookings."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/?booking_filter=cancelled')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bookings = response.data['bookings']
        self.assertEqual(len(bookings), 1)
        self.assertEqual(bookings[0]['status'], 'cancelled')
    
    def test_customer_detail_returns_payments(self):
        """Test that customer detail returns all payments."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payments = response.data['payments']
        self.assertEqual(len(payments), 2)
        self.assertEqual(payments[0]['amount'], '200.00')
    
    def test_customer_detail_returns_internal_notes(self):
        """Test that customer detail returns internal notes."""
        # Make the creation order unambiguous (both notes are created in setUp)
        InternalNote.objects.filter(pk=self.note1.pk).update(created_at=timezone.now() - timedelta(hours=1))
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notes = response.data['internal_notes']
        self.assertEqual(len(notes), 2)
        # Newest first: the WhatsApp note (note2) was added after the VIP note
        self.assertIn('Prefers WhatsApp', notes[0]['note'])
        self.assertIn('VIP customer', notes[1]['note'])
    
    def test_customer_detail_returns_last_activity(self):
        """Test that customer detail returns last activity timestamp."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('last_activity', response.data)
        self.assertIsNotNone(response.data['last_activity'])
    
    def test_customer_detail_not_found(self):
        """Test that customer detail returns 404 for non-existent customer."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/customers/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminInternalNotesTests(TestCase):
    """Tests for admin internal notes CRUD operations."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create super-admin user
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )
        
        # Create regular user (customer)
        self.customer = User.objects.create_user(
            email='customer@example.com',
            password='testpassword123',
            first_name='Customer',
            last_name='Test'
        )
        
        # Create initial internal note
        self.note = InternalNote.objects.create(
            customer=self.customer,
            author=self.super_admin,
            note='Initial note'
        )
    
    def test_staff_can_create_internal_note(self):
        """Test that staff can create internal note."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/',
            {'note': 'New note from staff'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['note'], 'New note from staff')
        self.assertEqual(response.data['author_email'], 'staff@example.com')
    
    def test_super_admin_can_create_internal_note(self):
        """Test that super-admin can create internal note."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.post(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/',
            {'note': 'New note from admin'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['note'], 'New note from admin')
    
    def test_note_is_created_for_customer_in_url_not_body(self):
        """The customer comes from the URL; a customer id in the body is ignored."""
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
        """Editing a note cannot reassign it to a different customer."""
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
        """Editing a note cannot rewrite who wrote it."""
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
        """The note PUT is partial; a body with only author must not change the author."""
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
        """Test that regular user cannot create internal note."""
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/',
            {'note': 'Should not work'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_note_requires_note_content(self):
        """Test that creating note requires note content."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/',
            {}
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_staff_can_update_internal_note(self):
        """Test that staff can update internal note."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.put(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/{self.note.id}/',
            {'note': 'Updated note content'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['note'], 'Updated note content')
    
    def test_staff_can_delete_internal_note(self):
        """Test that staff can delete internal note."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.delete(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/{self.note.id}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify note is soft-deleted
        self.note.refresh_from_db()
        self.assertTrue(self.note.is_deleted)
    
    def test_regular_user_cannot_update_internal_note(self):
        """Test that regular user cannot update internal note."""
        self.client.force_authenticate(user=self.customer)
        response = self.client.put(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/{self.note.id}/',
            {'note': 'Should not work'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_regular_user_cannot_delete_internal_note(self):
        """Test that regular user cannot delete internal note."""
        self.client.force_authenticate(user=self.customer)
        response = self.client.delete(
            f'/api/v1/admin-panel/customers/{self.customer.id}/notes/{self.note.id}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_cannot_access_note_for_different_customer(self):
        """Test that user cannot access note for different customer."""
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
        """Test that note response includes author name."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(f'/api/v1/admin-panel/customers/{self.customer.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notes = response.data['internal_notes']
        self.assertEqual(notes[0]['author_name'], 'Admin User')
        self.assertEqual(notes[0]['author_email'], 'admin@example.com')


class AdminStatisticsTests(TestCase):
    """Tests for admin statistics endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create super-admin user
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            first_name='Admin',
            last_name='User'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpassword123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='testpassword123',
            first_name='Regular',
            last_name='User'
        )
        
        # Create property type and property
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
        
        # Create room type and rate plan
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
        
        # Create users with different registration dates for statistics
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
        self.user3.date_joined = timezone.now() - timedelta(days=400)  # Over a year ago
        self.user3.save()
        
        # Create bookings for leaderboard tests
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
        
        # Create a cancelled booking (should not count in leaderboard)
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
        """Test that super-admin can access registration statistics."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/registrations/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('type', response.data)
        self.assertIn('statistics', response.data)
    
    def test_staff_can_access_registration_statistics(self):
        """Test that staff can access registration statistics."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin-panel/statistics/registrations/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_regular_user_cannot_access_registration_statistics(self):
        """Test that regular user cannot access registration statistics."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/admin-panel/statistics/registrations/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthenticated_user_cannot_access_registration_statistics(self):
        """Test that unauthenticated user cannot access registration statistics."""
        response = self.client.get('/api/v1/admin-panel/statistics/registrations/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_registration_statistics_rolling_12_months(self):
        """Test registration statistics for rolling 12-month window."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/registrations/?type=rolling_12_months')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'rolling_12_months')
        self.assertIn('start_date', response.data)
        self.assertIn('end_date', response.data)
        self.assertIn('statistics', response.data)
        self.assertIsInstance(response.data['statistics'], list)
    
    def test_registration_statistics_calendar_year(self):
        """Test registration statistics for calendar year."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/registrations/?type=calendar_year')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'calendar_year')
        self.assertIn('statistics', response.data)
        self.assertIsInstance(response.data['statistics'], list)
    
    def test_registration_statistics_defaults_to_rolling_12_months(self):
        """Test that registration statistics defaults to rolling 12-month window."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/registrations/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'rolling_12_months')
    
    def test_registration_statistics_no_registrations_in_period(self):
        """Test registration statistics when no registrations in period."""
        self.client.force_authenticate(user=self.super_admin)
        
        # Create a user that was deleted
        deleted_user = User.objects.create_user(
            email='deleted@example.com',
            password='testpassword123',
            first_name='Deleted',
            last_name='User'
        )
        deleted_user.soft_delete()
        
        # Get statistics for a period where no active registrations exist
        # This tests the edge case of empty statistics
        response = self.client.get('/api/v1/admin-panel/statistics/registrations/?type=calendar_year')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['statistics'], list)
    
    def test_super_admin_can_access_top_bookers_leaderboard(self):
        """Test that super-admin can access top bookers leaderboard."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('period', response.data)
        self.assertIn('limit', response.data)
        self.assertIn('leaderboard', response.data)
    
    def test_staff_can_access_top_bookers_leaderboard(self):
        """Test that staff can access top bookers leaderboard."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_regular_user_cannot_access_top_bookers_leaderboard(self):
        """Test that regular user cannot access top bookers leaderboard."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthenticated_user_cannot_access_top_bookers_leaderboard(self):
        """Test that unauthenticated user cannot access top bookers leaderboard."""
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_top_bookers_leaderboard_all_time(self):
        """Test top bookers leaderboard for all time period."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?period=all_time')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['period'], 'all_time')
        self.assertIn('leaderboard', response.data)
        self.assertIsInstance(response.data['leaderboard'], list)
        
        # Check that user1 is at the top (2 completed bookings)
        if response.data['leaderboard']:
            self.assertEqual(response.data['leaderboard'][0]['customer_name'], 'User One')
            self.assertEqual(response.data['leaderboard'][0]['completed_booking_count'], 2)
    
    def test_top_bookers_leaderboard_this_month(self):
        """Test top bookers leaderboard for this month period."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?period=this_month')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['period'], 'this_month')
        self.assertIn('leaderboard', response.data)
    
    def test_top_bookers_leaderboard_this_year(self):
        """Test top bookers leaderboard for this year period."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?period=this_year')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['period'], 'this_year')
        self.assertIn('leaderboard', response.data)
    
    def test_top_bookers_leaderboard_defaults_to_all_time(self):
        """Test that top bookers leaderboard defaults to all time."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['period'], 'all_time')
    
    def test_top_bookers_leaderboard_limit_parameter(self):
        """Test that limit parameter works correctly."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?limit=2')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['limit'], 2)
        self.assertLessEqual(len(response.data['leaderboard']), 2)
    
    def test_top_bookers_leaderboard_limit_max_constraint(self):
        """Test that limit parameter respects max constraint of 100."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?limit=200')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['limit'], 100)
    
    def test_top_bookers_leaderboard_invalid_limit_defaults(self):
        """Test that invalid limit parameter defaults to 10."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?limit=invalid')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['limit'], 10)
    
    def test_top_bookers_leaderboard_only_completed_bookings(self):
        """Test that only completed bookings count in leaderboard."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?period=all_time')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # user2 has 1 completed booking and 1 cancelled booking
        # Should only count the completed one
        user2_entry = None
        for entry in response.data['leaderboard']:
            if entry['customer_name'] == 'User Two':
                user2_entry = entry
                break
        
        self.assertIsNotNone(user2_entry)
        self.assertEqual(user2_entry['completed_booking_count'], 1)
    
    def test_top_bookers_leaderboard_no_bookings_in_period(self):
        """Test leaderboard when no bookings in period."""
        self.client.force_authenticate(user=self.super_admin)
        
        # Request leaderboard for this month when we have no bookings this month
        # (our test bookings are from previous days/months)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?period=this_month')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['leaderboard'], list)
        # May be empty if no bookings this month
    
    def test_top_bookers_leaderboard_ranking_order(self):
        """Test that leaderboard is correctly ranked by booking count."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?period=all_time')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that entries are in descending order of booking count
        leaderboard = response.data['leaderboard']
        for i in range(len(leaderboard) - 1):
            self.assertGreaterEqual(
                leaderboard[i]['completed_booking_count'],
                leaderboard[i + 1]['completed_booking_count']
            )
    
    def test_top_bookers_leaderboard_rank_field(self):
        """Test that leaderboard entries include rank field."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?period=all_time')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that entries have rank field starting from 1
        if response.data['leaderboard']:
            self.assertEqual(response.data['leaderboard'][0]['rank'], 1)
            if len(response.data['leaderboard']) > 1:
                self.assertEqual(response.data['leaderboard'][1]['rank'], 2)
    
    def test_top_bookers_leaderboard_sensitive_data_not_leaked(self):
        """Test that leaderboard doesn't leak sensitive customer data."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin-panel/statistics/top-bookers/?period=all_time')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that only necessary fields are returned
        if response.data['leaderboard']:
            entry = response.data['leaderboard'][0]
            self.assertIn('rank', entry)
            self.assertIn('customer_id', entry)
            self.assertIn('customer_name', entry)
            self.assertIn('completed_booking_count', entry)
            
            # Should NOT include sensitive data
            self.assertNotIn('email', entry)
            self.assertNotIn('phone_number', entry)
            self.assertNotIn('address', entry)

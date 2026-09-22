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
from decimal import Decimal
from datetime import date, timedelta

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
        response = self.client.get('/api/v1/admin/properties/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that at least our test property is in the list (paginated response)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        property_ids = [prop['id'] for prop in results]
        self.assertIn(self.property.id, property_ids)
    
    def test_staff_can_list_all_properties(self):
        """Test that staff can list all properties."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin/properties/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that at least our test property is in the list (paginated response)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        property_ids = [prop['id'] for prop in results]
        self.assertIn(self.property.id, property_ids)
    
    def test_regular_user_cannot_list_admin_properties(self):
        """Test that regular user cannot access admin property endpoints."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/admin/properties/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_super_admin_can_approve_property(self):
        """Test that super-admin can approve property."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.post(f'/api/v1/admin/properties/{self.property.id}/approve/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, 'active')
        self.assertEqual(self.property.approved_by, self.super_admin)
        self.assertIsNotNone(self.property.approved_at)
    
    def test_staff_can_approve_property(self):
        """Test that staff can approve property."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(f'/api/v1/admin/properties/{self.property.id}/approve/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, 'active')
    
    def test_admin_can_reject_property_with_reason(self):
        """Test that admin can reject property with reason."""
        self.client.force_authenticate(user=self.super_admin)
        data = {'rejection_reason': 'Property does not meet standards'}
        response = self.client.post(f'/api/v1/admin/properties/{self.property.id}/approve/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, 'rejected')
        self.assertEqual(self.property.rejection_reason, 'Property does not meet standards')
    
    def test_admin_can_suspend_property(self):
        """Test that admin can suspend property."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.post(f'/api/v1/admin/properties/{self.property.id}/suspend/')
        
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
        response = self.client.get('/api/v1/admin/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
    
    def test_staff_can_list_all_users(self):
        """Test that staff can list all users."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
    
    def test_regular_user_cannot_list_admin_users(self):
        """Test that regular user cannot access admin user endpoints."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/admin/users/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_super_admin_can_create_hotel_owner_account(self):
        """Test that super-admin can create hotel-owner account."""
        self.client.force_authenticate(user=self.super_admin)
        data = {
            'email': 'hotelowner@example.com',
            'first_name': 'Hotel',
            'last_name': 'Owner',
            'phone_number': '+998901234567',
            'password': 'testpassword123',
            'password_confirm': 'testpassword123'
        }
        response = self.client.post('/api/v1/admin/users/create-hotel-owner/', data, format='json')
        
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
        response = self.client.post('/api/v1/admin/users/create-hotel-owner/', data, format='json')
        
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
        response = self.client.post('/api/v1/admin/users/create-hotel-owner/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)
    
    def test_password_not_returned_in_response(self):
        """Test that password is not returned in response."""
        self.client.force_authenticate(user=self.super_admin)
        data = {
            'email': 'hotelowner4@example.com',
            'first_name': 'Hotel',
            'last_name': 'Owner',
            'password': 'testpassword123',
            'password_confirm': 'testpassword123'
        }
        response = self.client.post('/api/v1/admin/users/create-hotel-owner/', data, format='json')
        
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
        response = self.client.get('/api/v1/admin/amenities/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that at least our test amenity is in the list (paginated response)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        amenity_ids = [amenity['id'] for amenity in results]
        self.assertIn(self.amenity.id, amenity_ids)
    
    def test_staff_can_list_all_amenities(self):
        """Test that staff can list all amenities."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin/amenities/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that at least our test amenity is in the list (paginated response)
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        amenity_ids = [amenity['id'] for amenity in results]
        self.assertIn(self.amenity.id, amenity_ids)
    
    def test_regular_user_cannot_list_admin_amenities(self):
        """Test that regular user cannot access admin amenity endpoints."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/admin/amenities/')
        
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
        response = self.client.post('/api/v1/admin/amenities/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Amenity.objects.count(), 2)
    
    def test_super_admin_can_update_amenity(self):
        """Test that super-admin can update amenity."""
        self.client.force_authenticate(user=self.super_admin)
        data = {
            'name': 'Wireless Internet',
            'description': 'High-speed wireless internet'
        }
        response = self.client.patch(f'/api/v1/admin/amenities/{self.amenity.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.amenity.refresh_from_db()
        self.assertEqual(self.amenity.name, 'Wireless Internet')
    
    def test_super_admin_can_delete_amenity(self):
        """Test that super-admin can delete amenity (soft delete)."""
        self.client.force_authenticate(user=self.super_admin)
        amenity_id = self.amenity.id
        response = self.client.delete(f'/api/v1/admin/amenities/{amenity_id}/')
        
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
        response = self.client.post('/api/v1/admin/amenities/categories/', data)
        
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
        response = self.client.get('/api/v1/admin/payments/transactions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return empty list if no transactions exist
        self.assertEqual(response.data, [])
    
    def test_staff_can_list_payment_transactions(self):
        """Test that staff can list payment transactions."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin/payments/transactions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_regular_user_cannot_list_payment_transactions(self):
        """Test that regular user cannot access admin payment endpoints."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/admin/payments/transactions/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_can_filter_transactions_by_status(self):
        """Test that admin can filter transactions by status."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin/payments/transactions/?status=completed')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_admin_can_filter_transactions_by_provider(self):
        """Test that admin can filter transactions by provider."""
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/v1/admin/payments/transactions/?provider=payme')
        
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
            '/api/v1/admin/properties/',
            '/api/v1/admin/users/',
            '/api/v1/admin/amenities/',
            '/api/v1/admin/payments/transactions/'
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            # DRF returns 403 for unauthenticated users when authentication is required
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_non_staff_user_cannot_access_admin_endpoints(self):
        """Test that non-staff users cannot access admin endpoints."""
        self.client.force_authenticate(user=self.regular_user)
        endpoints = [
            '/api/v1/admin/properties/',
            '/api/v1/admin/users/',
            '/api/v1/admin/amenities/',
            '/api/v1/admin/payments/transactions/'
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
        response = self.client.post('/api/v1/admin/users/create-hotel-owner/', data, format='json')
        
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
        self.assertEqual(property_data['name'], self.property.name)
    
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

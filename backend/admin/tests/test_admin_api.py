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
from properties.models import Property, PropertyType, Amenity, AmenityCategory
from permissions.models import Role

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
        self.assertEqual(len(response.data), 1)
    
    def test_staff_can_list_all_properties(self):
        """Test that staff can list all properties."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin/properties/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
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
        response = self.client.post('/api/v1/admin/users/create-hotel-owner/', data)
        
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
        response = self.client.post('/api/v1/admin/users/create-hotel-owner/', data)
        
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
        response = self.client.post('/api/v1/admin/users/create-hotel-owner/', data)
        
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
        response = self.client.post('/api/v1/admin/users/create-hotel-owner/', data)
        
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
        self.assertEqual(len(response.data), 1)
    
    def test_staff_can_list_all_amenities(self):
        """Test that staff can list all amenities."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/admin/amenities/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
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
        response = self.client.delete(f'/api/v1/admin/amenities/{self.amenity.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.amenity.refresh_from_db()
        self.assertTrue(self.amenity.is_deleted)
    
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
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
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
        response = self.client.post('/api/v1/admin/users/create-hotel-owner/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

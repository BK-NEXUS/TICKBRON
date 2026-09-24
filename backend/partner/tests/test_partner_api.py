"""
Tests for partner API endpoints.

This module contains tests for property, room, rate, and availability
management scoped to hotel-owner accounts.
"""
import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from properties.models import Property, PropertyType, RoomType, RatePlan, DateInventory
from permissions.models import Role

User = get_user_model()


class PartnerPropertyTests(TestCase):
    """Tests for partner property management endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create hotel-owner role
        self.hotel_owner_role, _ = Role.objects.get_or_create(
            name='hotel-owner',
            defaults={'description': 'Hotel owner role', 'is_system_role': True}
        )
        
        # Create hotel-owner user
        self.hotel_owner = User.objects.create_user(
            email='hotelowner@example.com',
            password='testpassword123',
            first_name='John',
            last_name='Doe',
            role=self.hotel_owner_role
        )
        
        # Create another user (not hotel-owner)
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpassword123',
            first_name='Jane',
            last_name='Smith'
        )
        
        # Create property type
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment',
            description='Apartment property type'
        )
        
        # Create property for hotel-owner
        self.property = Property.objects.create(
            owner=self.hotel_owner,
            property_type=self.property_type,
            status='draft',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Main St',
            city='Tashkent',
            country='Uzbekistan',
            base_price=100.00,
            currency='USD'
        )
        
        # Create property for other user
        self.other_property = Property.objects.create(
            owner=self.other_user,
            property_type=self.property_type,
            status='draft',
            max_guests=2,
            bedrooms=1,
            bathrooms=1,
            address_line1='456 Oak Ave',
            city='Samarkand',
            country='Uzbekistan',
            base_price=50.00,
            currency='USD'
        )
    
    def test_hotel_owner_can_list_own_properties(self):
        """Test that hotel-owner can list their own properties."""
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.get('/api/v1/partner/properties/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.property.id)
    
    def test_hotel_owner_cannot_list_other_properties(self):
        """Test that hotel-owner cannot list other users' properties."""
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.get('/api/v1/partner/properties/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        # Should only see own property, not other user's property
        self.assertEqual(len(results), 1)
        self.assertNotEqual(results[0]['id'], self.other_property.id)
    
    def test_hotel_owner_can_create_property(self):
        """Test that hotel-owner can create new property."""
        self.client.force_authenticate(user=self.hotel_owner)
        data = {
            'property_type': self.property_type.id,
            'max_guests': 6,
            'bedrooms': 3,
            'bathrooms': 2,
            'address_line1': '789 Pine Rd',
            'city': 'Bukhara',
            'country': 'Uzbekistan',
            'base_price': 150.00,
            'currency': 'USD'
        }
        response = self.client.post('/api/v1/partner/properties/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Property.objects.count(), 3)
        
        # Verify owner is set to authenticated user
        # Get the most recent property created by hotel_owner
        new_property = Property.objects.filter(owner=self.hotel_owner).order_by('-created_at').first()
        self.assertIsNotNone(new_property)
        self.assertEqual(new_property.owner, self.hotel_owner)
    
    def test_hotel_owner_can_update_own_property(self):
        """Test that hotel-owner can update their own property."""
        self.client.force_authenticate(user=self.hotel_owner)
        data = {
            'max_guests': 5,
            'base_price': 120.00
        }
        response = self.client.patch(f'/api/v1/partner/properties/{self.property.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.max_guests, 5)
        self.assertEqual(float(self.property.base_price), 120.00)
    
    def test_hotel_owner_cannot_change_property_status(self):
        """Status comes from admin moderation; the owner cannot self-approve."""
        Property.objects.filter(pk=self.property.pk).update(status='pending_approval')
        self.client.force_authenticate(user=self.hotel_owner)
        
        for new_status in ('active', 'suspended', 'rejected'):
            response = self.client.patch(
                f'/api/v1/partner/properties/{self.property.id}/', {'status': new_status}, format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.property.refresh_from_db()
            self.assertEqual(self.property.status, 'pending_approval')
    
    def test_hotel_owner_cannot_reactivate_suspended_property(self):
        """A suspended owner cannot lift the suspension while editing other fields."""
        Property.objects.filter(pk=self.property.pk).update(status='suspended')
        self.client.force_authenticate(user=self.hotel_owner)
        
        response = self.client.patch(
            f'/api/v1/partner/properties/{self.property.id}/', {'status': 'active', 'max_guests': 6}, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, 'suspended')
        self.assertEqual(self.property.max_guests, 6)
    
    def test_new_property_starts_as_draft(self):
        """Creating a property never makes it public, even if status is sent."""
        self.client.force_authenticate(user=self.hotel_owner)
        data = {
            'property_type': self.property.property_type_id, 'status': 'active', 'max_guests': 2,
            'bedrooms': 1, 'bathrooms': 1, 'address_line1': '1 Status Test St', 'city': 'Samarkand',
            'country': 'Uzbekistan', 'base_price': '80.00', 'currency': 'USD'
        }
        
        response = self.client.post('/api/v1/partner/properties/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Property.objects.get(address_line1='1 Status Test St').status, 'draft')
    
    def test_hotel_owner_cannot_update_other_property(self):
        """Test that hotel-owner cannot update other users' property."""
        self.client.force_authenticate(user=self.hotel_owner)
        data = {
            'max_guests': 3,
            'base_price': 75.00
        }
        response = self.client.patch(f'/api/v1/partner/properties/{self.other_property.id}/', data)
        
        # Should return 404 because property is not in their queryset
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_hotel_owner_can_delete_own_property(self):
        """Test that hotel-owner can delete their own property (soft delete)."""
        self.client.force_authenticate(user=self.hotel_owner)
        property_id = self.property.id
        response = self.client.delete(f'/api/v1/partner/properties/{property_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Check that property is no longer in the active queryset (means it's soft deleted)
        self.assertFalse(Property.objects.filter(id=property_id).exists())
    
    def test_hotel_owner_cannot_delete_other_property(self):
        """Test that hotel-owner cannot delete other users' property."""
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.delete(f'/api/v1/partner/properties/{self.other_property.id}/')
        
        # Should return 404 because property is not in their queryset
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_unauthenticated_user_cannot_access_partner_endpoints(self):
        """Test that unauthenticated users cannot access partner endpoints."""
        response = self.client.get('/api/v1/partner/properties/')
        
        # DRF returns 403 for unauthenticated users when authentication is required
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_regular_user_cannot_access_partner_endpoints(self):
        """Test that regular users without hotel-owner role cannot access partner endpoints."""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get('/api/v1/partner/properties/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PartnerRoomTypeTests(TestCase):
    """Tests for partner room type management endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create hotel-owner role and user
        self.hotel_owner_role, _ = Role.objects.get_or_create(
            name='hotel-owner',
            defaults={'description': 'Hotel owner role', 'is_system_role': True}
        )
        
        self.hotel_owner = User.objects.create_user(
            email='hotelowner@example.com',
            password='testpassword123',
            first_name='John',
            last_name='Doe',
            role=self.hotel_owner_role
        )
        
        # Create property type and property
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment',
            description='Apartment property type'
        )
        
        self.property = Property.objects.create(
            owner=self.hotel_owner,
            property_type=self.property_type,
            status='draft',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Main St',
            city='Tashkent',
            country='Uzbekistan',
            base_price=100.00,
            currency='USD'
        )
        
        # Create room type
        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=100.00,
            currency='USD',
            total_rooms=5
        )
    
    def test_hotel_owner_can_list_own_room_types(self):
        """Test that hotel-owner can list their own room types."""
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.get('/api/v1/partner/rooms/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.room_type.id)
    
    def test_hotel_owner_can_create_room_type(self):
        """Test that hotel-owner can create room type."""
        self.client.force_authenticate(user=self.hotel_owner)
        data = {
            'property': self.property.id,
            'name': 'Deluxe Room',
            'slug': 'deluxe-room',
            'base_occupancy': 2,
            'max_occupancy': 4,
            'base_price': 150.00,
            'currency': 'USD',
            'total_rooms': 3
        }
        response = self.client.post('/api/v1/partner/rooms/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RoomType.objects.count(), 2)
    
    def test_hotel_owner_cannot_create_room_type_for_other_property(self):
        """Test that hotel-owner cannot create room type for other users' property."""
        # Create another user and property
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpassword123',
            first_name='Jane',
            last_name='Smith'
        )
        
        other_property = Property.objects.create(
            owner=other_user,
            property_type=self.property_type,
            status='draft',
            max_guests=2,
            bedrooms=1,
            bathrooms=1,
            address_line1='456 Oak Ave',
            city='Samarkand',
            country='Uzbekistan',
            base_price=50.00,
            currency='USD'
        )
        
        self.client.force_authenticate(user=self.hotel_owner)
        data = {
            'property': other_property.id,
            'name': 'Suite',
            'slug': 'suite',
            'base_occupancy': 2,
            'max_occupancy': 4,
            'base_price': 200.00,
            'currency': 'USD',
            'total_rooms': 2
        }
        response = self.client.post('/api/v1/partner/rooms/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check for error in the new response format
        if 'error' in response.data:
            self.assertIn('property', response.data['error'].get('details', {}))
        else:
            self.assertIn('property', response.data)


class PartnerRatePlanTests(TestCase):
    """Tests for partner rate plan management endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create hotel-owner role and user
        self.hotel_owner_role, _ = Role.objects.get_or_create(
            name='hotel-owner',
            defaults={'description': 'Hotel owner role', 'is_system_role': True}
        )
        
        self.hotel_owner = User.objects.create_user(
            email='hotelowner@example.com',
            password='testpassword123',
            first_name='John',
            last_name='Doe',
            role=self.hotel_owner_role
        )
        
        # Create property type, property, and room type
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment',
            description='Apartment property type'
        )
        
        self.property = Property.objects.create(
            owner=self.hotel_owner,
            property_type=self.property_type,
            status='draft',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Main St',
            city='Tashkent',
            country='Uzbekistan',
            base_price=100.00,
            currency='USD'
        )
        
        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=100.00,
            currency='USD',
            total_rooms=5
        )
        
        # Create rate plan
        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type,
            name='Standard Rate',
            slug='standard-rate',
            rate_type='standard',
            base_price=100.00,
            currency='USD',
            min_nights=1,
            is_active=True
        )
    
    def test_hotel_owner_can_list_own_rate_plans(self):
        """Test that hotel-owner can list their own rate plans."""
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.get('/api/v1/partner/rates/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.rate_plan.id)
    
    def test_hotel_owner_can_create_rate_plan(self):
        """Test that hotel-owner can create rate plan."""
        self.client.force_authenticate(user=self.hotel_owner)
        data = {
            'room_type': self.room_type.id,
            'name': 'Non-refundable Rate',
            'slug': 'non-refundable-rate',
            'rate_type': 'non_refundable',
            'base_price': 90.00,
            'currency': 'USD',
            'min_nights': 1,
            'is_active': True
        }
        response = self.client.post('/api/v1/partner/rates/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RatePlan.objects.count(), 2)


class PartnerDateInventoryTests(TestCase):
    """Tests for partner date inventory management endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create hotel-owner role and user
        self.hotel_owner_role, _ = Role.objects.get_or_create(
            name='hotel-owner',
            defaults={'description': 'Hotel owner role', 'is_system_role': True}
        )
        
        self.hotel_owner = User.objects.create_user(
            email='hotelowner@example.com',
            password='testpassword123',
            first_name='John',
            last_name='Doe',
            role=self.hotel_owner_role
        )
        
        # Create property type, property, room type, and rate plan
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment',
            description='Apartment property type'
        )
        
        self.property = Property.objects.create(
            owner=self.hotel_owner,
            property_type=self.property_type,
            status='draft',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Main St',
            city='Tashkent',
            country='Uzbekistan',
            base_price=100.00,
            currency='USD'
        )
        
        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=100.00,
            currency='USD',
            total_rooms=5
        )
        
        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type,
            name='Standard Rate',
            slug='standard-rate',
            rate_type='standard',
            base_price=100.00,
            currency='USD',
            min_nights=1,
            is_active=True
        )
        
        # Create date inventory
        from datetime import date
        self.date_inventory = DateInventory.objects.create(
            rate_plan=self.rate_plan,
            date=date.today(),
            available_rooms=5,
            booked_rooms=0,
            price=100.00,
            currency='USD',
            is_available=True
        )
    
    def test_hotel_owner_can_list_own_date_inventory(self):
        """Test that hotel-owner can list their own date inventory."""
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.get('/api/v1/partner/inventory/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.date_inventory.id)
    
    def test_hotel_owner_can_create_date_inventory(self):
        """Test that hotel-owner can create date inventory."""
        self.client.force_authenticate(user=self.hotel_owner)
        from datetime import date, timedelta
        data = {
            'rate_plan': self.rate_plan.id,
            'date': date.today() + timedelta(days=1),
            'available_rooms': 5,
            'booked_rooms': 0,
            'price': 110.00,
            'currency': 'USD',
            'is_available': True
        }
        response = self.client.post('/api/v1/partner/inventory/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DateInventory.objects.count(), 2)
    
    def test_hotel_owner_cannot_modify_booked_rooms(self):
        """Test that hotel-owner cannot modify booked_rooms field."""
        self.client.force_authenticate(user=self.hotel_owner)
        data = {
            'booked_rooms': 2
        }
        response = self.client.patch(f'/api/v1/partner/inventory/{self.date_inventory.id}/', data)
        
        # booked_rooms should be read-only
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.date_inventory.refresh_from_db()
        self.assertEqual(self.date_inventory.booked_rooms, 0)  # Should remain unchanged


class PartnerPropertyPhotoUploadTests(TestCase):
    """Tests for partner property photo upload validation (audit #23)."""

    # Minimal valid 1x1 GIF, matches the fixture used in properties/tests/test_models.py
    VALID_IMAGE_BYTES = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
        b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
        b'\x02\x4c\x01\x00\x3b'
    )

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        self.hotel_owner_role, _ = Role.objects.get_or_create(
            name='hotel-owner',
            defaults={'description': 'Hotel owner role', 'is_system_role': True}
        )

        self.hotel_owner = User.objects.create_user(
            email='hotelowner@example.com',
            password='testpassword123',
            first_name='John',
            last_name='Doe',
            role=self.hotel_owner_role
        )

        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment',
            description='Apartment property type'
        )

        self.property = Property.objects.create(
            owner=self.hotel_owner,
            property_type=self.property_type,
            status='draft',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Main St',
            city='Tashkent',
            country='Uzbekistan',
            base_price=100.00,
            currency='USD'
        )

        self.upload_url = f'/api/v1/partner/properties/{self.property.id}/photos/'

    def test_hotel_owner_can_upload_valid_photo(self):
        """A genuine, small, correctly-typed image is accepted."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.force_authenticate(user=self.hotel_owner)
        image = SimpleUploadedFile(
            name='photo.gif',
            content=self.VALID_IMAGE_BYTES,
            content_type='image/gif'
        )
        response = self.client.post(
            self.upload_url,
            {'photo': image, 'photo_type': 'exterior'},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_hotel_owner_cannot_upload_fake_image(self):
        """
        A non-image file disguised with an image extension/content-type must be rejected.

        DRF's ImageField already verifies the payload with Pillow before it reaches our
        code, so this passes even pre-fix -- it documents that existing coverage rather
        than testing the audit #23 gap itself (see the extension/size tests below for that).
        """
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.force_authenticate(user=self.hotel_owner)
        fake_image = SimpleUploadedFile(
            name='photo.jpg',
            content=b'this is definitely not image data, just plain bytes' * 10,
            content_type='image/jpeg'
        )
        response = self.client.post(
            self.upload_url,
            {'photo': fake_image, 'photo_type': 'exterior'},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('photo', response.data)

    def test_hotel_owner_cannot_upload_disallowed_extension(self):
        """
        A genuinely valid image (Pillow opens it fine) in a format outside our whitelist
        (jpg/jpeg/png/gif/webp) must still be rejected. model.clean() enforces this, but
        DRF never calls it -- audit #23's actual gap.
        """
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        import io

        img = Image.new('RGB', (10, 10), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format='BMP')

        self.client.force_authenticate(user=self.hotel_owner)
        bmp_file = SimpleUploadedFile(
            name='photo.bmp',
            content=buf.getvalue(),
            content_type='image/bmp'
        )
        response = self.client.post(
            self.upload_url,
            {'photo': bmp_file, 'photo_type': 'exterior'},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('photo', response.data)

    def test_hotel_owner_cannot_upload_oversized_photo(self):
        """
        A genuinely valid image larger than the 10MB limit must be rejected by the API,
        not just by model.clean() (which DRF never calls).
        """
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        import io
        import os

        width, height = 2000, 1800  # random-noise pixels compress poorly -> file stays > 10MB
        raw_pixels = os.urandom(width * height * 3)
        img = Image.frombytes('RGB', (width, height), raw_pixels)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        content = buf.getvalue()
        self.assertGreater(len(content), 10 * 1024 * 1024)

        self.client.force_authenticate(user=self.hotel_owner)
        oversized_file = SimpleUploadedFile(
            name='photo.png',
            content=content,
            content_type='image/png'
        )
        response = self.client.post(
            self.upload_url,
            {'photo': oversized_file, 'photo_type': 'exterior'},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('photo', response.data)


class PartnerBookingListTests(TestCase):
    """Tests for the partner bookings list endpoint (audit #26)."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        self.hotel_owner_role, _ = Role.objects.get_or_create(
            name='hotel-owner',
            defaults={'description': 'Hotel owner role', 'is_system_role': True}
        )

        self.hotel_owner = User.objects.create_user(
            email='hotelowner@example.com',
            password='testpassword123',
            first_name='John',
            last_name='Doe',
            role=self.hotel_owner_role
        )

        self.guest = User.objects.create_user(
            email='guest@example.com',
            password='testpassword123',
            first_name='Alice',
            last_name='Guest'
        )

        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment',
            description='Apartment property type'
        )

        self.property = Property.objects.create(
            owner=self.hotel_owner,
            property_type=self.property_type,
            status='active',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Main St',
            city='Tashkent',
            country='Uzbekistan',
            base_price=100.00,
            currency='USD'
        )

        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=100.00,
            currency='USD',
            total_rooms=5
        )

        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type,
            name='Standard Rate',
            slug='standard-rate',
            rate_type='standard',
            base_price=100.00,
            currency='USD',
            min_nights=1,
            is_active=True
        )

        from datetime import date, timedelta
        self.check_in = date.today() + timedelta(days=10)
        self.check_out = date.today() + timedelta(days=12)
        current_date = self.check_in
        while current_date < self.check_out:
            DateInventory.objects.create(
                rate_plan=self.rate_plan,
                date=current_date,
                available_rooms=5,
                booked_rooms=0,
                price=100.00,
                currency='USD',
                is_available=True
            )
            current_date += timedelta(days=1)

        from bookings.models import Booking
        self.booking = Booking.create_booking(
            guest=self.guest,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

    def test_hotel_owner_can_list_bookings_with_guest_name(self):
        """booking.guest_name doesn't exist on the model -- must not 500."""
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.get('/api/v1/partner/bookings/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['guest_name'], self.booking.guest_full_name)

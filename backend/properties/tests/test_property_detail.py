"""
Tests for property detail API endpoint.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from properties.models import (
    Property, PropertyType, PropertyTranslation, PropertyAmenity,
    Amenity, AmenityCategory, PropertyPhoto, PropertyPolicy,
    RoomType, RoomPhoto, RoomAmenity, RatePlan, DateInventory
)

User = get_user_model()


class PropertyDetailEndpointTest(TestCase):
    """Test cases for property detail API endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment',
            description='Apartment property type'
        )
        
        self.amenity_category = AmenityCategory.objects.create(
            name='Kitchen',
            slug='kitchen',
            description='Kitchen amenities'
        )
        
        self.wifi_amenity = Amenity.objects.create(
            category=self.amenity_category,
            name='WiFi',
            slug='wifi',
            description='Wireless internet',
            is_searchable=True
        )
        
        self.ac_amenity = Amenity.objects.create(
            category=self.amenity_category,
            name='Air Conditioning',
            slug='air-conditioning',
            description='Climate control',
            is_searchable=True
        )
        
        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            status='active',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Main St',
            city='Tashkent',
            country='Uzbekistan',
            latitude=41.2995,
            longitude=69.2401,
            base_price=50.00,
            currency='USD'
        )
        
        # Add translations
        PropertyTranslation.objects.create(
            property=self.property,
            language='en',
            name='Modern Apartment',
            description='A beautiful modern apartment in the city center'
        )
        
        # Add amenities to property
        PropertyAmenity.objects.create(
            property=self.property,
            amenity=self.wifi_amenity,
            is_available=True
        )
        
        PropertyAmenity.objects.create(
            property=self.property,
            amenity=self.ac_amenity,
            is_available=True
        )
        
        # Add policies
        PropertyPolicy.objects.create(
            property=self.property,
            policy_type='check_in',
            title='Check-in Policy',
            description='Check-in from 3:00 PM',
            is_strict=True
        )
        
        PropertyPolicy.objects.create(
            property=self.property,
            policy_type='cancellation',
            title='Cancellation Policy',
            description='Free cancellation up to 24 hours before check-in',
            is_strict=False
        )
        
        # Add photos (without actual file upload for testing)
        from django.core.files.uploadedfile import SimpleUploadedFile
        import io
        
        # Create a simple image file for testing
        image_content = io.BytesIO(b'fake image content')
        image_file = SimpleUploadedFile(
            "test.jpg",
            image_content.getvalue(),
            content_type="image/jpeg"
        )
        
        self.photo1 = PropertyPhoto.objects.create(
            property=self.property,
            photo=image_file,
            photo_type='exterior',
            caption='Exterior view',
            is_primary=True,
            display_order=1
        )
        
        # Create another image file
        image_content2 = io.BytesIO(b'fake image content 2')
        image_file2 = SimpleUploadedFile(
            "test2.jpg",
            image_content2.getvalue(),
            content_type="image/jpeg"
        )
        
        self.photo2 = PropertyPhoto.objects.create(
            property=self.property,
            photo=image_file2,
            photo_type='interior',
            caption='Living room',
            is_primary=False,
            display_order=2
        )
        
        # Add room type with rate plans
        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            description='Comfortable standard room',
            base_occupancy=2,
            max_occupancy=2,
            base_price=50.00,
            currency='USD',
            total_rooms=5
        )
        
        # Add room amenities
        RoomAmenity.objects.create(
            room_type=self.room_type,
            amenity=self.wifi_amenity,
            is_available=True
        )
        
        # Add rate plan
        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type,
            name='Standard Rate',
            slug='standard-rate',
            rate_type='standard',
            description='Standard rate with flexible cancellation',
            base_price=50.00,
            currency='USD',
            min_nights=1,
            is_active=True
        )
        
        # Add date inventory
        from datetime import date, timedelta
        tomorrow = date.today() + timedelta(days=1)
        DateInventory.objects.create(
            rate_plan=self.rate_plan,
            date=tomorrow,
            available_rooms=5,
            booked_rooms=0,
            price=50.00,
            currency='USD',
            is_available=True
        )
    
    def test_property_detail_success(self):
        """Test successful property detail request."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['id'], self.property.id)
        self.assertIn('gallery', response.data)
        self.assertIn('amenities', response.data)
        self.assertIn('room_types', response.data)
        self.assertIn('policies', response.data)
        self.assertIn('translations', response.data)
    
    def test_property_detail_includes_basic_info(self):
        """Test that property detail includes basic information."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['city'], 'Tashkent')
        self.assertEqual(response.data['country'], 'Uzbekistan')
        self.assertEqual(response.data['max_guests'], 4)
        self.assertEqual(str(response.data['base_price']), '50.00')
    
    def test_property_detail_includes_gallery(self):
        """Test that property detail includes gallery organized by type."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('gallery', response.data)
        gallery = response.data['gallery']
        self.assertIn('exterior', gallery)
        self.assertIn('interior', gallery)
        self.assertIn('amenity', gallery)
        self.assertIn('room', gallery)
        self.assertIn('other', gallery)
        self.assertGreater(len(gallery['exterior']), 0)
        self.assertGreater(len(gallery['interior']), 0)
    
    def test_property_detail_includes_amenities(self):
        """Test that property detail includes amenities with categories."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('amenities', response.data)
        amenities = response.data['amenities']
        self.assertGreater(len(amenities), 0)
        
        # Check amenity structure
        first_amenity = amenities[0]
        self.assertIn('amenity', first_amenity)
        self.assertIn('is_available', first_amenity)
        self.assertIn('category', first_amenity['amenity'])
    
    def test_property_detail_includes_policies(self):
        """Test that property detail includes policies."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('policies', response.data)
        policies = response.data['policies']
        self.assertGreater(len(policies), 0)
        
        # Check policy structure
        first_policy = policies[0]
        self.assertIn('policy_type', first_policy)
        self.assertIn('title', first_policy)
        self.assertIn('description', first_policy)
        self.assertIn('is_strict', first_policy)
    
    def test_property_detail_includes_translations(self):
        """Test that property detail includes translations."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('translations', response.data)
        translations = response.data['translations']
        self.assertGreater(len(translations), 0)
        
        # Check translation structure
        first_translation = translations[0]
        self.assertIn('language', first_translation)
        self.assertIn('name', first_translation)
        self.assertIn('description', first_translation)
    
    def test_property_detail_includes_room_types(self):
        """Test that property detail includes room types with rate plans."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('room_types', response.data)
        room_types = response.data['room_types']
        self.assertGreater(len(room_types), 0)
        
        # Check room type structure
        first_room_type = room_types[0]
        self.assertIn('id', first_room_type)
        self.assertIn('name', first_room_type)
        self.assertIn('base_occupancy', first_room_type)
        self.assertIn('max_occupancy', first_room_type)
        self.assertIn('rate_plans', first_room_type)
        self.assertIn('photos', first_room_type)
        self.assertIn('amenities', first_room_type)
    
    def test_property_detail_room_types_includes_rate_plans(self):
        """Test that room types include rate plans."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        room_types = response.data['room_types']
        first_room_type = room_types[0]
        
        self.assertIn('rate_plans', first_room_type)
        rate_plans = first_room_type['rate_plans']
        self.assertGreater(len(rate_plans), 0)
        
        # Check rate plan structure
        first_rate_plan = rate_plans[0]
        self.assertIn('id', first_rate_plan)
        self.assertIn('name', first_rate_plan)
        self.assertIn('rate_type', first_rate_plan)
        self.assertIn('base_price', first_rate_plan)
        self.assertIn('min_nights', first_rate_plan)
    
    def test_property_detail_not_found(self):
        """Test property detail with non-existent property ID."""
        response = self.client.get('/api/v1/properties/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_property_detail_deleted_property(self):
        """Test property detail with deleted property."""
        # Soft delete the property
        self.property.is_deleted = True
        self.property.save()
        
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_property_detail_inactive_property(self):
        """Test property detail with inactive property."""
        # Deactivate the property
        self.property.is_active = False
        self.property.save()
        
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_property_detail_public_access(self):
        """Test that property detail endpoint is publicly accessible."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')
        
        # Should work without authentication
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_property_detail_includes_full_address(self):
        """Test that property detail includes full address."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('full_address', response.data)
        self.assertIn('Tashkent', response.data['full_address'])
        self.assertIn('Uzbekistan', response.data['full_address'])
    
    def test_property_detail_gallery_photo_ordering(self):
        """Test that gallery photos are ordered by display_order."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        gallery = response.data['gallery']
        
        # Check that exterior photos are ordered
        exterior_photos = gallery['exterior']
        if len(exterior_photos) > 1:
            display_orders = [photo['display_order'] for photo in exterior_photos]
            self.assertEqual(display_orders, sorted(display_orders))
    
    def test_property_detail_includes_metadata(self):
        """Test that property detail includes metadata."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('created_at', response.data)
        self.assertIn('updated_at', response.data)
        self.assertIn('status', response.data)

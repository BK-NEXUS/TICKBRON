"""
Mehmanxana tolıq maǵlıwmatı API endpoint i ushın testler.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from properties.models import (
    Property, PropertyType, PropertyTranslation, PropertyAmenity,
    Amenity, AmenityCategory, PropertyPhoto, PropertyPolicy,
    RoomType, RoomAmenity, RatePlan, DateInventory
)

User = get_user_model()


class PropertyDetailEndpointTest(TestCase):
    """Mehmanxana tolıq maǵlıwmatı API endpoint i ushın test jaǵdayları."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
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

        # Awdarmalardı qosıw
        PropertyTranslation.objects.create(
            property=self.property,
            language='en',
            name='Modern Apartment',
            description='A beautiful modern apartment in the city center'
        )

        # Mehmanxanaǵa amenity lerdi qosıw
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

        # Siyasatlardı qosıw
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

        # Súwretlerdi qosıw (testlew ushın haqıyqıy fayl júklewsiz)
        from django.core.files.uploadedfile import SimpleUploadedFile
        import io

        # Testlew ushın ápiwayı súwret faylın jaratıw
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

        # Taǵı bir súwret faylın jaratıw
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

        # Rate plan lı xona túrin qosıw
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

        # Xona amenity lerin qosıw
        RoomAmenity.objects.create(
            room_type=self.room_type,
            amenity=self.wifi_amenity,
            is_available=True
        )

        # Rate plan dı qosıw
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

        # Date inventory di qosıw
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
        """Tabıslı mehmanxana tolıq maǵlıwmatı sorawın testlew."""
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
        """Mehmanxana tolıq maǵlıwmatı tiykarǵı maǵlıwmattı óz ishine alatuǵının testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['city'], 'Tashkent')
        self.assertEqual(response.data['country'], 'Uzbekistan')
        self.assertEqual(response.data['max_guests'], 4)
        self.assertEqual(str(response.data['base_price']), '50.00')

    def test_property_detail_includes_gallery(self):
        """Mehmanxana tolıq maǵlıwmatı túri boyınsha shólkemlestirilgen galereyanı óz ishine alatuǵının testlew."""
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
        """Mehmanxana tolıq maǵlıwmatı kategoriyaları menen amenity lerdi óz ishine alatuǵının testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('amenities', response.data)
        amenities = response.data['amenities']
        self.assertGreater(len(amenities), 0)

        # Amenity dúzilisin tekseriw
        first_amenity = amenities[0]
        self.assertIn('amenity', first_amenity)
        self.assertIn('is_available', first_amenity)
        self.assertIn('category', first_amenity['amenity'])

    def test_property_detail_includes_policies(self):
        """Mehmanxana tolıq maǵlıwmatı siyasatlardı óz ishine alatuǵının testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('policies', response.data)
        policies = response.data['policies']
        self.assertGreater(len(policies), 0)

        # Siyasat dúzilisin tekseriw
        first_policy = policies[0]
        self.assertIn('policy_type', first_policy)
        self.assertIn('title', first_policy)
        self.assertIn('description', first_policy)
        self.assertIn('is_strict', first_policy)

    def test_property_detail_includes_translations(self):
        """Mehmanxana tolıq maǵlıwmatı awdarmalardı óz ishine alatuǵının testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('translations', response.data)
        translations = response.data['translations']
        self.assertGreater(len(translations), 0)

        # Awdarma dúzilisin tekseriw
        first_translation = translations[0]
        self.assertIn('language', first_translation)
        self.assertIn('name', first_translation)
        self.assertIn('description', first_translation)

    def test_property_detail_includes_room_types(self):
        """Mehmanxana tolıq maǵlıwmatı rate plan lı xona túrlerin óz ishine alatuǵının testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('room_types', response.data)
        room_types = response.data['room_types']
        self.assertGreater(len(room_types), 0)

        # Xona túri dúzilisin tekseriw
        first_room_type = room_types[0]
        self.assertIn('id', first_room_type)
        self.assertIn('name', first_room_type)
        self.assertIn('base_occupancy', first_room_type)
        self.assertIn('max_occupancy', first_room_type)
        self.assertIn('rate_plans', first_room_type)
        self.assertIn('photos', first_room_type)
        self.assertIn('amenities', first_room_type)

    def test_property_detail_room_types_includes_rate_plans(self):
        """Xona túrleri rate plan lardı óz ishine alatuǵının testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        room_types = response.data['room_types']
        first_room_type = room_types[0]

        self.assertIn('rate_plans', first_room_type)
        rate_plans = first_room_type['rate_plans']
        self.assertGreater(len(rate_plans), 0)

        # Rate plan dúzilisin tekseriw
        first_rate_plan = rate_plans[0]
        self.assertIn('id', first_rate_plan)
        self.assertIn('name', first_rate_plan)
        self.assertIn('rate_type', first_rate_plan)
        self.assertIn('base_price', first_rate_plan)
        self.assertIn('min_nights', first_rate_plan)

    def test_property_detail_not_found(self):
        """Joq mehmanxana ID si menen mehmanxana tolıq maǵlıwmatın testlew."""
        response = self.client.get('/api/v1/properties/99999/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_property_detail_deleted_property(self):
        """Óshirilgen mehmanxana menen mehmanxana tolıq maǵlıwmatın testlew."""
        # Mehmanxananı soft-delete etiw
        self.property.is_deleted = True
        self.property.save()

        response = self.client.get(f'/api/v1/properties/{self.property.id}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_property_detail_inactive_property(self):
        """Aktiv emes mehmanxana menen mehmanxana tolıq maǵlıwmatın testlew."""
        # Mehmanxananı aktiv emes etiw
        self.property.is_active = False
        self.property.save()

        response = self.client.get(f'/api/v1/properties/{self.property.id}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_property_detail_public_access(self):
        """Mehmanxana tolıq maǵlıwmatı endpoint i ashıq qol jetimli ekenin testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')

        # Autentifikaciyasız islewi kerek
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_property_detail_includes_full_address(self):
        """Mehmanxana tolıq maǵlıwmatı tolıq mánzildi óz ishine alatuǵının testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('full_address', response.data)
        self.assertIn('Tashkent', response.data['full_address'])
        self.assertIn('Uzbekistan', response.data['full_address'])

    def test_property_detail_gallery_photo_ordering(self):
        """Galereya súwretleri display_order boyınsha tártiplengenin testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        gallery = response.data['gallery']

        # Sırtqı súwretler tártiplengenin tekseriw
        exterior_photos = gallery['exterior']
        if len(exterior_photos) > 1:
            display_orders = [photo['display_order'] for photo in exterior_photos]
            self.assertEqual(display_orders, sorted(display_orders))

    def test_property_detail_includes_metadata(self):
        """Mehmanxana tolıq maǵlıwmatı metadata nı óz ishine alatuǵının testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('created_at', response.data)
        self.assertIn('updated_at', response.data)
        self.assertIn('status', response.data)

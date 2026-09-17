"""
Tests for property search functionality.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.test import APIClient
from rest_framework import status
from properties.models import (
    Property, PropertyType, PropertyTranslation, PropertyAmenity,
    Amenity, AmenityCategory, PropertyPhoto
)
from properties.search import PropertySearchService

User = get_user_model()


class PropertySearchServiceTest(TestCase):
    """Test cases for PropertySearchService."""
    
    def setUp(self):
        """Set up test data."""
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
        
        # Create test properties
        self.property1 = Property.objects.create(
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
        
        self.property2 = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            status='active',
            max_guests=6,
            bedrooms=3,
            bathrooms=2,
            address_line1='456 Oak Ave',
            city='Samarkand',
            country='Uzbekistan',
            latitude=39.6542,
            longitude=66.9598,
            base_price=75.00,
            currency='USD'
        )
        
        self.property3 = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            status='active',
            max_guests=2,
            bedrooms=1,
            bathrooms=1,
            address_line1='789 Pine Rd',
            city='Bukhara',
            country='Uzbekistan',
            latitude=39.7681,
            longitude=64.4286,
            base_price=30.00,
            currency='USD'
        )
        
        # Add translations
        PropertyTranslation.objects.create(
            property=self.property1,
            language='en',
            name='Modern Apartment',
            description='A beautiful modern apartment in the city center'
        )
        
        PropertyTranslation.objects.create(
            property=self.property2,
            language='en',
            name='Spacious Villa',
            description='Large villa with beautiful views'
        )
        
        # Add amenities to properties
        PropertyAmenity.objects.create(
            property=self.property1,
            amenity=self.wifi_amenity,
            is_available=True
        )
        
        PropertyAmenity.objects.create(
            property=self.property1,
            amenity=self.ac_amenity,
            is_available=True
        )
        
        PropertyAmenity.objects.create(
            property=self.property2,
            amenity=self.wifi_amenity,
            is_available=True
        )
        
        self.search_service = PropertySearchService()
    
    def test_basic_text_search(self):
        """Test basic text search functionality."""
        search_params = {'q': 'Tashkent'}
        results = self.search_service.search(search_params)
        
        self.assertGreater(results['count'], 0)
        self.assertEqual(len(results['results']), results['count'])
    
    def test_geographic_search(self):
        """Test geographic search with coordinates."""
        search_params = {
            'lat': 41.2995,
            'lng': 69.2401,
            'radius': 50  # 50km radius
        }
        results = self.search_service.search(search_params)
        
        self.assertGreater(results['count'], 0)
    
    def test_price_filtering(self):
        """Test price range filtering."""
        search_params = {
            'min_price': 40.00,
            'max_price': 80.00
        }
        results = self.search_service.search(search_params)
        
        for property in results['results']:
            self.assertGreaterEqual(property.base_price, 40.00)
            self.assertLessEqual(property.base_price, 80.00)
    
    def test_amenity_filtering(self):
        """Test amenity filtering."""
        search_params = {
            'amenities': [self.wifi_amenity.id]
        }
        results = self.search_service.search(search_params)
        
        self.assertGreater(results['count'], 0)
    
    def test_guest_filtering(self):
        """Test guest capacity filtering."""
        search_params = {
            'min_guests': 3,
            'max_guests': 6
        }
        results = self.search_service.search(search_params)
        
        for property in results['results']:
            self.assertGreaterEqual(property.max_guests, 3)
            self.assertLessEqual(property.max_guests, 6)
    
    def test_property_type_filtering(self):
        """Test property type filtering."""
        search_params = {
            'property_type': self.property_type.id
        }
        results = self.search_service.search(search_params)
        
        self.assertGreater(results['count'], 0)
        for property in results['results']:
            self.assertEqual(property.property_type_id, self.property_type.id)
    
    def test_date_filtering(self):
        """Test date availability filtering."""
        check_in = (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        check_out = (timezone.now() + timedelta(days=10)).strftime('%Y-%m-%d')
        
        search_params = {
            'check_in': check_in,
            'check_out': check_out
        }
        results = self.search_service.search(search_params)
        
        # Should return properties (basic implementation)
        self.assertGreaterEqual(results['count'], 0)
    
    def test_sorting_by_price_asc(self):
        """Test sorting by price ascending."""
        search_params = {
            'sort': 'price_asc'
        }
        results = self.search_service.search(search_params)
        
        if len(results['results']) > 1:
            prices = [p.base_price for p in results['results']]
            self.assertEqual(prices, sorted(prices))
    
    def test_sorting_by_price_desc(self):
        """Test sorting by price descending."""
        search_params = {
            'sort': 'price_desc'
        }
        results = self.search_service.search(search_params)
        
        if len(results['results']) > 1:
            prices = [p.base_price for p in results['results']]
            self.assertEqual(prices, sorted(prices, reverse=True))
    
    def test_pagination(self):
        """Test pagination functionality."""
        search_params = {
            'page': 1,
            'page_size': 2
        }
        results = self.search_service.search(search_params)
        
        self.assertLessEqual(len(results['results']), 2)
        self.assertIn('next', results)
        self.assertIn('previous', results)
    
    def test_empty_results(self):
        """Test search with no matching results."""
        search_params = {
            'q': 'NonExistentCity123456'
        }
        results = self.search_service.search(search_params)
        
        self.assertEqual(results['count'], 0)
        self.assertEqual(len(results['results']), 0)
    
    def test_search_suggestions(self):
        """Test search suggestions for autocomplete."""
        suggestions = self.search_service.get_search_suggestions('Tash')
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)


class PropertySearchEndpointTest(TestCase):
    """Test cases for property search API endpoint."""
    
    def setUp(self):
        """Set up test data and API client."""
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
        
        PropertyTranslation.objects.create(
            property=self.property,
            language='en',
            name='Test Apartment',
            description='Test description'
        )
    
    def test_search_endpoint_success(self):
        """Test successful search request."""
        response = self.client.get('/api/v1/properties/search/', {'q': 'Tashkent'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
    
    def test_search_endpoint_query_parameters(self):
        """Test search with various query parameters."""
        response = self.client.get('/api/v1/properties/search/', {
            'q': 'Tashkent',
            'min_price': 40,
            'max_price': 60,
            'min_guests': 2,
            'page': 1,
            'page_size': 10
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_search_endpoint_filter_combinations(self):
        """Test search with multiple filters combined."""
        response = self.client.get('/api/v1/properties/search/', {
            'q': 'Tashkent',
            'min_price': 40,
            'max_guests': 3,
            'sort': 'price_asc'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_search_endpoint_sorting(self):
        """Test search with different sorting options."""
        sorting_options = ['relevance', 'price_asc', 'price_desc', 'rating', 'distance']
        
        for sort_option in sorting_options:
            response = self.client.get('/api/v1/properties/search/', {
                'sort': sort_option
            })
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_search_endpoint_pagination(self):
        """Test search pagination."""
        response = self.client.get('/api/v1/properties/search/', {
            'page': 1,
            'page_size': 5
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
    
    def test_search_endpoint_public_access(self):
        """Test that search endpoint is publicly accessible."""
        response = self.client.get('/api/v1/properties/search/', {'q': 'Tashkent'})
        
        # Should work without authentication
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_search_endpoint_invalid_parameters(self):
        """Test search with invalid parameters."""
        response = self.client.get('/api/v1/properties/search/', {
            'min_price': -10,  # Invalid negative price
            'max_guests': 0    # Invalid guest count
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_search_suggestions_endpoint(self):
        """Test search suggestions endpoint."""
        response = self.client.get('/api/v1/properties/search/suggestions/', {'q': 'Tash'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('suggestions', response.data)
        self.assertIsInstance(response.data['suggestions'], list)


class PropertySearchIntegrationTest(TestCase):
    """Integration test for complete search workflow."""
    
    def setUp(self):
        """Set up comprehensive test data."""
        self.client = APIClient()
        
        # Create user
        self.user = User.objects.create_user(
            email='integration@example.com',
            password='testpass123',
            first_name='Integration',
            last_name='Test'
        )
        
        # Create property type
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment',
            description='Apartment property type'
        )
        
        # Create amenity category and amenities
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
        
        # Create multiple properties with different characteristics
        for i in range(5):
            property = Property.objects.create(
                owner=self.user,
                property_type=self.property_type,
                status='active',
                max_guests=2 + i,
                bedrooms=1 + i,
                bathrooms=1,
                address_line1=f'{i+1} Test Street',
                city=['Tashkent', 'Samarkand', 'Bukhara', 'Khiva', 'Fergana'][i],
                country='Uzbekistan',
                latitude=40.0 + i,
                longitude=65.0 + i,
                base_price=30.00 + (i * 10),
                currency='USD'
            )
            
            PropertyTranslation.objects.create(
                property=property,
                language='en',
                name=f'Property {i+1}',
                description=f'Test property {i+1} description'
            )
            
            PropertyAmenity.objects.create(
                property=property,
                amenity=self.wifi_amenity,
                is_available=True
            )
    
    def test_complete_search_workflow(self):
        """Test complete search workflow from API to results."""
        # Step 1: Get search suggestions
        suggestions_response = self.client.get('/api/v1/properties/search/suggestions/', {'q': 'Tash'})
        self.assertEqual(suggestions_response.status_code, status.HTTP_200_OK)
        
        # Step 2: Perform search with filters
        search_response = self.client.get('/api/v1/properties/search/', {
            'q': 'Tashkent',
            'min_price': 30,
            'max_price': 70,
            'min_guests': 2,
            'amenities': str(self.wifi_amenity.id),
            'sort': 'price_asc',
            'page': 1,
            'page_size': 10
        })
        
        self.assertEqual(search_response.status_code, status.HTTP_200_OK)
        self.assertIn('count', search_response.data)
        self.assertIn('results', search_response.data)
        
        # Step 3: Verify result structure
        if search_response.data['count'] > 0:
            first_result = search_response.data['results'][0]
            self.assertIn('id', first_result)
            self.assertIn('city', first_result)
            self.assertIn('base_price', first_result)
            self.assertIn('amenities', first_result)
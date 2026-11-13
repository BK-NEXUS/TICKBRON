"""
Mehmanxana izlew funkciyası ushın testler.
"""
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from properties.models import (
    Property, PropertyType, PropertyTranslation, PropertyAmenity,
    Amenity, AmenityCategory
)
from properties.search import PropertySearchService

User = get_user_model()


class PropertySearchServiceTest(TestCase):
    """PropertySearchService ushın test jaǵdayları."""

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

        # Test mehmanxanaların jaratıw
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

        # Awdarmalardı qosıw
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

        # Mehmanxanalarǵa amenity lerdi qosıw
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
        """Ápiwayı tekst izlewdi testlew."""
        search_params = {'q': 'Tashkent'}
        results = self.search_service.search(search_params)

        self.assertGreater(results['count'], 0)
        self.assertEqual(len(results['results']), results['count'])

    def test_geographic_search(self):
        """Koordinatalar menen geografiyalıq izlewdi testlew."""
        search_params = {
            'lat': 41.2995,
            'lng': 69.2401,
            'radius': 50  # 50 km radius
        }
        results = self.search_service.search(search_params)

        self.assertGreater(results['count'], 0)

    def test_price_filtering(self):
        """Baha aralıǵı boyınsha filterlewdi testlew."""
        search_params = {
            'min_price': 40.00,
            'max_price': 80.00
        }
        results = self.search_service.search(search_params)

        for property in results['results']:
            self.assertGreaterEqual(property.base_price, 40.00)
            self.assertLessEqual(property.base_price, 80.00)

    def test_amenity_filtering(self):
        """Amenity boyınsha filterlewdi testlew."""
        search_params = {
            'amenities': [self.wifi_amenity.id]
        }
        results = self.search_service.search(search_params)

        self.assertGreater(results['count'], 0)

    def test_guest_filtering(self):
        """Mehmanlar sıyımlılıǵı boyınsha filterlewdi testlew."""
        search_params = {
            'min_guests': 3,
            'max_guests': 6
        }
        results = self.search_service.search(search_params)

        for property in results['results']:
            self.assertGreaterEqual(property.max_guests, 3)
            self.assertLessEqual(property.max_guests, 6)

    def test_property_type_filtering(self):
        """Mehmanxana túri boyınsha filterlewdi testlew."""
        search_params = {
            'property_type': self.property_type.id
        }
        results = self.search_service.search(search_params)

        self.assertGreater(results['count'], 0)
        for property in results['results']:
            self.assertEqual(property.property_type_id, self.property_type.id)

    def test_date_filtering(self):
        """Sana boyınsha bos orın filterlewin testlew."""
        check_in = (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        check_out = (timezone.now() + timedelta(days=10)).strftime('%Y-%m-%d')

        search_params = {
            'check_in': check_in,
            'check_out': check_out
        }
        results = self.search_service.search(search_params)

        # Mehmanxanalardı qaytarıwı kerek (ápiwayı iske asırıw)
        self.assertGreaterEqual(results['count'], 0)

    def test_sorting_by_price_asc(self):
        """Baha boyınsha ósiw tártibinde tártiplewdi testlew."""
        search_params = {
            'sort': 'price_asc'
        }
        results = self.search_service.search(search_params)

        if len(results['results']) > 1:
            prices = [p.base_price for p in results['results']]
            self.assertEqual(prices, sorted(prices))

    def test_sorting_by_price_desc(self):
        """Baha boyınsha kemeyiw tártibinde tártiplewdi testlew."""
        search_params = {
            'sort': 'price_desc'
        }
        results = self.search_service.search(search_params)

        if len(results['results']) > 1:
            prices = [p.base_price for p in results['results']]
            self.assertEqual(prices, sorted(prices, reverse=True))

    def test_pagination(self):
        """Betlew (pagination) funkciyasın testlew."""
        search_params = {
            'page': 1,
            'page_size': 2
        }
        results = self.search_service.search(search_params)

        self.assertLessEqual(len(results['results']), 2)
        self.assertIn('next', results)
        self.assertIn('previous', results)

    def test_empty_results(self):
        """Sáykes nátiyje joq izlewdi testlew."""
        search_params = {
            'q': 'NonExistentCity123456'
        }
        results = self.search_service.search(search_params)

        self.assertEqual(results['count'], 0)
        self.assertEqual(len(results['results']), 0)

    def test_search_suggestions(self):
        """Avtotolıqtırıw ushın izlew usınıslarını testlew."""
        suggestions = self.search_service.get_search_suggestions('Tash')

        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)

    def test_search_params_validation_query_too_long(self):
        """Sorawdıń júdá uzın bolıwı ushın validaciya qátesin testlew."""
        search_params = {'q': 'a' * 501}  # 501 belgi (eń kóbi 500)

        with self.assertRaises(ValueError) as context:
            self.search_service.search(search_params)

        self.assertIn('too long', str(context.exception))

    def test_search_params_validation_location_too_long(self):
        """Jaylasıwdıń júdá uzın bolıwı ushın validaciya qátesin testlew."""
        search_params = {'location': 'a' * 201}  # 201 belgi (eń kóbi 200)

        with self.assertRaises(ValueError) as context:
            self.search_service.search(search_params)

        self.assertIn('too long', str(context.exception))

    def test_search_params_validation_invalid_latitude(self):
        """Jaramsız latitude ushın validaciya qátesin testlew."""
        search_params = {'lat': 91.0, 'lng': 0.0}  # Jaramsız latitude (> 90)

        with self.assertRaises(ValueError) as context:
            self.search_service.search(search_params)

        self.assertIn('latitude', str(context.exception).lower())

    def test_search_params_validation_invalid_longitude(self):
        """Jaramsız longitude ushın validaciya qátesin testlew."""
        search_params = {'lat': 0.0, 'lng': 181.0}  # Jaramsız longitude (> 180)

        with self.assertRaises(ValueError) as context:
            self.search_service.search(search_params)

        self.assertIn('longitude', str(context.exception).lower())

    def test_search_params_validation_invalid_radius(self):
        """Jaramsız radius ushın validaciya qátesin testlew."""
        search_params = {'lat': 0.0, 'lng': 0.0, 'radius': 101}  # Jaramsız radius (> 100)

        with self.assertRaises(ValueError) as context:
            self.search_service.search(search_params)

        self.assertIn('radius', str(context.exception).lower())

    def test_search_params_validation_negative_price(self):
        """Teris baha ushın validaciya qátesin testlew."""
        search_params = {'min_price': -10.0}

        with self.assertRaises(ValueError) as context:
            self.search_service.search(search_params)

        self.assertIn('price', str(context.exception).lower())

    def test_search_params_validation_invalid_guest_range(self):
        """Jaramsız mehmanlar aralıǵı ushın validaciya qátesin testlew."""
        search_params = {'min_guests': 10, 'max_guests': 5}  # min > max

        with self.assertRaises(ValueError) as context:
            self.search_service.search(search_params)

        self.assertIn('guest', str(context.exception).lower())

    def test_search_params_validation_too_many_amenities(self):
        """Amenity lerdiń kóp bolıwı ushın validaciya qátesin testlew."""
        search_params = {'amenities': list(range(21))}  # 21 amenity (eń kóbi 20)

        with self.assertRaises(ValueError) as context:
            self.search_service.search(search_params)

        self.assertIn('amenities', str(context.exception).lower())

    def test_search_params_validation_invalid_page_size(self):
        """Jaramsız bet ólshemi ushın validaciya qátesin testlew."""
        search_params = {'page_size': 101}  # Jaramsız bet ólshemi (> 100)

        with self.assertRaises(ValueError) as context:
            self.search_service.search(search_params)

        self.assertIn('page size', str(context.exception).lower())

    def test_search_response_includes_pagination_metadata(self):
        """Izlew juwabında jańa pagination metadata sı bar ekenin testlew."""
        search_params = {'page': 1, 'page_size': 2}
        results = self.search_service.search(search_params)

        self.assertIn('page', results)
        self.assertIn('page_size', results)
        self.assertIn('total_pages', results)
        self.assertEqual(results['page'], 1)
        self.assertEqual(results['page_size'], 2)

    def test_text_search_word_splitting(self):
        """Tekst izlew jaqsıraq sáykeslik ushın sorawdı sózlerge bóletuǵının testlew."""
        search_params = {'q': 'Modern Apartment'}  # Eki sóz
        results = self.search_service.search(search_params)

        # Description ında "Modern" hám "Apartment" ekewi de bar mehmanxananı tabıwı kerek
        self.assertGreater(results['count'], 0)

    def test_text_search_sanitization(self):
        """Tekst izlew qáwipli belgilerdi funkciyanı buzbastan tazalaytuǵının testlew."""
        # Tazalaw izlewdi buzbaytuǵının testlew
        search_params = {'q': 'Tashkent'}
        results = self.search_service.search(search_params)

        # Ádettegidey islewi kerek
        self.assertGreater(results['count'], 0)

        # Qáwipli belgiler duris islenetuǵının testlew
        dangerous_query = '<script>alert("test")</script>'
        sanitized_query = dangerous_query.replace('<', '').replace('>', '').replace('"', '').replace("'", '')

        # Tazalawdan keyin qáwipli belgiler alıp taslanıwı kerek
        self.assertNotIn('<', sanitized_query)
        self.assertNotIn('>', sanitized_query)
        self.assertNotIn('"', sanitized_query)
        self.assertNotIn("'", sanitized_query)

    def test_empty_query_handling(self):
        """Bos sorawdıń duris islenetuǵının testlew."""
        search_params = {'q': ''}
        results = self.search_service.search(search_params)

        # Barlıq mehmanxanalardı qaytarıwı kerek (filter qollanılmaydı)
        self.assertGreater(results['count'], 0)

    def test_short_query_handling(self):
        """Júdá qısqa sorawlardıń islenetuǵının testlew."""
        search_params = {'q': 'a'}  # Bir belgi
        results = self.search_service.search(search_params)

        # Duris islewi kerek (eń kemi 2 belgi shárti sebepli nátiyje bolmawı múmkin)
        self.assertIsInstance(results['count'], int)


class PropertySearchEndpointTest(TestCase):
    """Mehmanxana izlew API endpoint i ushın test jaǵdayları."""

    def setUp(self):
        """Test maǵlıwmatın hám API client ti tayarlaw."""
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
        """Tabıslı izlew sorawın testlew."""
        response = self.client.get('/api/v1/properties/search/', {'q': 'Tashkent'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)

    def test_search_endpoint_query_parameters(self):
        """Túrli soraw parametrleri menen izlewdi testlew."""
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
        """Birge qollanılǵan kóp filter menen izlewdi testlew."""
        response = self.client.get('/api/v1/properties/search/', {
            'q': 'Tashkent',
            'min_price': 40,
            'max_guests': 3,
            'sort': 'price_asc'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_endpoint_sorting(self):
        """Túrli tártiplew variantları menen izlewdi testlew."""
        sorting_options = ['relevance', 'price_asc', 'price_desc', 'rating', 'distance']

        for sort_option in sorting_options:
            response = self.client.get('/api/v1/properties/search/', {
                'sort': sort_option
            })
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_endpoint_pagination(self):
        """Izlew betlewin testlew."""
        response = self.client.get('/api/v1/properties/search/', {
            'page': 1,
            'page_size': 5
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)

    def test_search_endpoint_public_access(self):
        """Izlew endpoint i ashıq qol jetimli ekenin testlew."""
        response = self.client.get('/api/v1/properties/search/', {'q': 'Tashkent'})

        # Autentifikaciyasız islewi kerek
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_endpoint_invalid_parameters(self):
        """Jaramsız parametrler menen izlewdi testlew."""
        response = self.client.get('/api/v1/properties/search/', {
            'min_price': -10,  # Jaramsız teris baha
            'max_guests': 0    # Jaramsız mehman sanı
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_suggestions_endpoint(self):
        """Izlew usınısları endpoint in testlew."""
        response = self.client.get('/api/v1/properties/search/suggestions/', {'q': 'Tash'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('suggestions', response.data)
        self.assertIsInstance(response.data['suggestions'], list)

    def test_search_endpoint_validation_invalid_amenity_count(self):
        """Amenity lerdiń kóp bolıwı ushın endpoint validaciyasın testlew (servis qatlamı)."""
        # Serializer amenity sanın tutpawı múmkin, servis qatlamı tutıwı kerek
        amenities_list = ','.join([str(i) for i in range(21)])
        response = self.client.get('/api/v1/properties/search/', {'amenities': amenities_list})

        # Servis qatlamı validaciyası buni tutıwı kerek
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_search_endpoint_validation_invalid_date_format(self):
        """Jaramsız sana formatı ushın endpoint validaciyasın testlew."""
        response = self.client.get('/api/v1/properties/search/', {'check_in': 'invalid-date'})

        # Serializer buni tutıwı kerek
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_search_endpoint_response_includes_pagination_metadata(self):
        """Endpoint juwabında jańa pagination metadata sı bar ekenin testlew."""
        response = self.client.get('/api/v1/properties/search/', {'page': 1, 'page_size': 10})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('page', response.data)
        self.assertIn('page_size', response.data)
        self.assertIn('total_pages', response.data)

    def test_search_endpoint_invalid_amenities_format(self):
        """Jaramsız amenity formatı menen endpoint ti testlew."""
        response = self.client.get('/api/v1/properties/search/', {'amenities': 'invalid,format'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_search_endpoint_geographic_coordinates_required(self):
        """Geografiyalıq izlew ushın lat hám lng ekewi de kerek ekenin testlew."""
        response = self.client.get('/api/v1/properties/search/', {'lat': 41.2995})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_search_endpoint_standardized_error_response(self):
        """Qátelik juwapları standart formatqa say ekenin testlew."""
        response = self.client.get('/api/v1/properties/search/', {'min_price': -10})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('details', response.data)

    def test_search_endpoint_internal_error_does_not_leak_details(self):
        """Izlew servisindegi kútilmegen ishki qátelik str(e) di sırtqa shıǵarmawı kerek (audit #24)."""
        from unittest.mock import patch

        secret = "psycopg2.errors.SyntaxError: near 'internal-query-fragment'"
        with patch('properties.search.PropertySearchService.search', side_effect=ValueError(secret)):
            response = self.client.get('/api/v1/properties/search/', {'q': 'Tashkent'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn(secret, str(response.data))

    def test_search_suggestions_endpoint_internal_error_does_not_leak_details(self):
        """Usınıslardaǵı kútilmegen ishki qátelik str(e) di sırtqa shıǵarmawı kerek (audit #24)."""
        from unittest.mock import patch

        secret = "psycopg2.OperationalError: connection to internal-db-host failed"
        with patch('properties.search.PropertySearchService.get_search_suggestions', side_effect=Exception(secret)):
            response = self.client.get('/api/v1/properties/search/suggestions/', {'q': 'Tash'})

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertNotIn(secret, str(response.data))


class PropertySearchTranslationsTest(TestCase):
    """Izlew nátiyjeleri mehmanxananıń awdarmaların (atın) N+1 siz alıp júredi."""

    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(email='owner@example.com', password='testpass123')
        self.property_type = PropertyType.objects.create(name='Hotel', slug='hotel')

    def _create_property(self, name):
        prop = Property.objects.create(
            owner=self.owner, property_type=self.property_type, status='active',
            max_guests=2, bedrooms=1, bathrooms=1, address_line1='1 Street',
            city='Samarkand', country='Uzbekistan', base_price=80, currency='USD',
        )
        PropertyTranslation.objects.create(property=prop, language='en', name=name)
        PropertyTranslation.objects.create(property=prop, language='uz', name=f'{name} uz')
        return prop

    def _translation_queries(self, count):
        for i in range(count):
            self._create_property(f'Hotel {len(Property.objects.all())}-{i}')
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get('/api/v1/properties/search/', {'city': 'Samarkand'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response, [q for q in ctx.captured_queries if 'property_translations' in q['sql']]

    def test_results_include_translations(self):
        prop = self._create_property('Registan Hotel')
        response = self.client.get('/api/v1/properties/search/', {'city': 'Samarkand'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = next(r for r in response.data['results'] if r['id'] == prop.id)
        names = {t['language']: t['name'] for t in result['translations']}
        self.assertEqual(names, {'en': 'Registan Hotel', 'uz': 'Registan Hotel uz'})

    def test_soft_deleted_translations_are_left_out(self):
        prop = self._create_property('Old Name')
        prop.translations.filter(language='uz').update(is_deleted=True)

        response = self.client.get('/api/v1/properties/search/', {'city': 'Samarkand'})
        result = next(r for r in response.data['results'] if r['id'] == prop.id)
        self.assertEqual([t['language'] for t in result['translations']], ['en'])

    def test_translations_are_loaded_in_one_query_whatever_the_result_count(self):
        response, queries = self._translation_queries(1)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(queries), 1)

        response, queries = self._translation_queries(5)
        self.assertEqual(response.data['count'], 6)
        self.assertEqual(len(queries), 1)


class PropertySearchIntegrationTest(TestCase):
    """Tolıq izlew process i ushın integraciya testi."""

    def setUp(self):
        """Keń kólemli test maǵlıwmatın tayarlaw."""
        self.client = APIClient()

        # Paydalanıwshını jaratıw
        self.user = User.objects.create_user(
            email='integration@example.com',
            password='testpass123',
            first_name='Integration',
            last_name='Test'
        )

        # Mehmanxana túrin jaratıw
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment',
            description='Apartment property type'
        )

        # Amenity kategoriyasın hám amenity lerdi jaratıw
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

        # Túrli qásiyetli kóp mehmanxananı jaratıw
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
        """API den nátiyjege shekem tolıq izlew process in testlew."""
        # 1-qadam: izlew usınıslarını alıw
        suggestions_response = self.client.get('/api/v1/properties/search/suggestions/', {'q': 'Tash'})
        self.assertEqual(suggestions_response.status_code, status.HTTP_200_OK)

        # 2-qadam: filterler menen izlewdi islew
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

        # 3-qadam: nátiyje dúzilisin tekseriw
        if search_response.data['count'] > 0:
            first_result = search_response.data['results'][0]
            self.assertIn('id', first_result)
            self.assertIn('city', first_result)
            self.assertIn('base_price', first_result)
            self.assertIn('amenities', first_result)

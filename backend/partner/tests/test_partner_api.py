"""
Partner API endpoint leri ushın testler.

Bul modul mehmanxana iyesi akkaunt larına shekemlengen mehmanxana, xona, baha hám
bos orınlardı basqarıw testlerin óz ishine aladı.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from properties.models import Property, PropertyType, RoomType, RatePlan, DateInventory, PropertyPhoto
from permissions.models import Role
from partner.tests.geography_helpers import uzbek_location
from currency.testing import make_usd_rate

User = get_user_model()


class PartnerPropertyTests(TestCase):
    """Partner mehmanxana basqarıw endpoint leri ushın testler."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.client = APIClient()

        # Mehmanxana iyesi rolin jaratıw
        self.hotel_owner_role, _ = Role.objects.get_or_create(
            name='hotel-owner',
            defaults={'description': 'Hotel owner role', 'is_system_role': True}
        )

        # Mehmanxana iyesi paydalanıwshısın jaratıw
        self.hotel_owner = User.objects.create_user(
            email='hotelowner@example.com',
            password='testpassword123',
            first_name='John',
            last_name='Doe',
            role=self.hotel_owner_role
        )

        # Basqa paydalanıwshı jaratıw (mehmanxana iyesi emes)
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpassword123',
            first_name='Jane',
            last_name='Smith'
        )

        # Mehmanxana túrin jaratıw
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment',
            description='Apartment property type'
        )

        # Mehmanxana iyesi ushın mehmanxana jaratıw
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

        # Basqa paydalanıwshı ushın mehmanxana jaratıw
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
        """Mehmanxana iyesi óz mehmanxanaların dizimley alatuǵının testlew."""
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.get('/api/v1/partner/properties/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Betlengen juwaptı islew
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.property.id)

    def test_hotel_owner_cannot_list_other_properties(self):
        """Mehmanxana iyesi basqa paydalanıwshılardıń mehmanxanaların dizimley almaytuǵının testlew."""
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.get('/api/v1/partner/properties/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Betlengen juwaptı islew
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        # Tek óz mehmanxanasın kóriwi kerek, basqa paydalanıwshınıń emes
        self.assertEqual(len(results), 1)
        self.assertNotEqual(results[0]['id'], self.other_property.id)

    def test_hotel_owner_can_create_property(self):
        """Mehmanxana iyesi jańa mehmanxana jarata alatuǵının testlew."""
        self.client.force_authenticate(user=self.hotel_owner)
        data = {
            'property_type': self.property_type.id,
            'translations': {'en': {'name': 'Pine Hotel'}},
            'max_guests': 6,
            'bedrooms': 3,
            'bathrooms': 2,
            'address_line1': '789 Pine Rd',
            **uzbek_location('Bukhara'),
            'base_price': 150.00,
            'currency': 'USD'
        }
        response = self.client.post('/api/v1/partner/properties/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Property.objects.count(), 3)

        # Iye kirgen paydalanıwshı etip belgilengenin tekseriw
        # hotel_owner jaratqan eń sońǵı mehmanxananı alıw
        new_property = Property.objects.filter(owner=self.hotel_owner).order_by('-created_at').first()
        self.assertIsNotNone(new_property)
        self.assertEqual(new_property.owner, self.hotel_owner)

    def test_hotel_owner_can_update_own_property(self):
        """Mehmanxana iyesi óz mehmanxanasın jańalay alatuǵının testlew."""
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
        """Status admin moderation ınan keledi; iye ózin tastıyıqlay almaydı."""
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
        """Toqtatılǵan iye basqa maydanlardı ózgertkende toqtatıwdı alıp taslay almaydı."""
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
        """Mehmanxana jaratıw hesh qashan onı ashıq etpeydi, status jiberilse de."""
        self.client.force_authenticate(user=self.hotel_owner)
        data = {
            'property_type': self.property.property_type_id, 'status': 'active', 'max_guests': 2,
            'bedrooms': 1, 'bathrooms': 1, 'address_line1': '1 Status Test St', **uzbek_location('Samarkand'),
            'base_price': '80.00', 'currency': 'USD', 'translations': {'en': {'name': 'Status Test Hotel'}},
        }

        response = self.client.post('/api/v1/partner/properties/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Property.objects.get(address_line1='1 Status Test St').status, 'draft')

    def test_hotel_owner_cannot_update_other_property(self):
        """Mehmanxana iyesi basqa paydalanıwshılardıń mehmanxanasın jańalay almaytuǵının testlew."""
        self.client.force_authenticate(user=self.hotel_owner)
        data = {
            'max_guests': 3,
            'base_price': 75.00
        }
        response = self.client.patch(f'/api/v1/partner/properties/{self.other_property.id}/', data)

        # 404 qaytarıwı kerek, sebebi mehmanxana olardıń queryset inde joq
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_hotel_owner_can_delete_own_property(self):
        """Mehmanxana iyesi óz mehmanxanasın óshire alatuǵının testlew (soft delete)."""
        self.client.force_authenticate(user=self.hotel_owner)
        property_id = self.property.id
        response = self.client.delete(f'/api/v1/partner/properties/{property_id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Qatar qaladı (soft delete) hám belgilenedi; iyeniń dizimi onı endi kórsetpeydi
        self.assertTrue(Property.objects.get(id=property_id).is_deleted)
        self.assertEqual(self.client.get(f'/api/v1/partner/properties/{property_id}/').status_code,
                         status.HTTP_404_NOT_FOUND)

    def test_hotel_owner_cannot_delete_other_property(self):
        """Mehmanxana iyesi basqa paydalanıwshılardıń mehmanxanasın óshire almaytuǵının testlew."""
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.delete(f'/api/v1/partner/properties/{self.other_property.id}/')

        # 404 qaytarıwı kerek, sebebi mehmanxana olardıń queryset inde joq
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_user_cannot_access_partner_endpoints(self):
        """Kirmegen paydalanıwshılar partner endpoint lerge kire almaytuǵının testlew."""
        response = self.client.get('/api/v1/partner/properties/')

        # Autentifikaciya kerek bolǵanda DRF kirmegen paydalanıwshılarǵa 403 qaytaradı
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_access_partner_endpoints(self):
        """Mehmanxana iyesi rolisiz ápiwayı paydalanıwshılar partner endpoint lerge kire almaytuǵının testlew."""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get('/api/v1/partner/properties/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PartnerRoomTypeTests(TestCase):
    """Partner xona túrin basqarıw endpoint leri ushın testler."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.client = APIClient()

        # Mehmanxana iyesi rolin hám paydalanıwshısın jaratıw
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

        # Mehmanxana túrin hám mehmanxananı jaratıw
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

        # Xona túrin jaratıw
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
        """Mehmanxana iyesi óz xona túrlerin dizimley alatuǵının testlew."""
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.get('/api/v1/partner/rooms/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Betlengen juwaptı islew
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.room_type.id)

    def test_hotel_owner_can_create_room_type(self):
        """Mehmanxana iyesi xona túri jarata alatuǵının testlew."""
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
        """Mehmanxana iyesi basqa paydalanıwshılardıń mehmanxanası ushın xona túri jarata almaytuǵının testlew."""
        # Basqa paydalanıwshı hám mehmanxana jaratıw
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
        # Jańa juwap formatında qátelikti tekseriw
        if 'error' in response.data:
            self.assertIn('property', response.data['error'].get('details', {}))
        else:
            self.assertIn('property', response.data)


class PartnerRatePlanTests(TestCase):
    """Partner rate plan basqarıw endpoint leri ushın testler."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.client = APIClient()

        # Mehmanxana iyesi rolin hám paydalanıwshısın jaratıw
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

        # Mehmanxana túrin, mehmanxananı hám xona túrin jaratıw
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

        # Rate plan jaratıw
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
        """Mehmanxana iyesi óz rate planların dizimley alatuǵının testlew."""
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.get('/api/v1/partner/rates/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Betlengen juwaptı islew
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.rate_plan.id)

    def test_hotel_owner_can_create_rate_plan(self):
        """Mehmanxana iyesi rate plan jarata alatuǵının testlew."""
        self.client.force_authenticate(user=self.hotel_owner)
        data = {
            'room_type': self.room_type.id,
            'name': 'Non-refundable Rate',
            'slug': 'non-refundable-rate',
            'rate_type': 'non_refundable',
            'base_price': 90.00,
            'currency': 'USD',
            'prices': {'USD': '90.00', 'UZS': '1100000', 'KZT': '40000', 'RUB': '8000'},
            'min_nights': 1,
            'is_active': True
        }
        response = self.client.post('/api/v1/partner/rates/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RatePlan.objects.count(), 2)


class PartnerDateInventoryTests(TestCase):
    """Partner date inventory basqarıw endpoint leri ushın testler."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.client = APIClient()

        # Mehmanxana iyesi rolin hám paydalanıwshısın jaratıw
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

        # Mehmanxana túrin, mehmanxananı, xona túrin hám rate plan dı jaratıw
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

        # Date inventory jaratıw
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
        """Mehmanxana iyesi óz date inventory sın dizimley alatuǵının testlew."""
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.get('/api/v1/partner/inventory/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Betlengen juwaptı islew
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.date_inventory.id)

    def test_hotel_owner_can_create_date_inventory(self):
        """Mehmanxana iyesi date inventory jarata alatuǵının testlew."""
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
        """Mehmanxana iyesi booked_rooms maydanın ózgerte almaytuǵının testlew."""
        self.client.force_authenticate(user=self.hotel_owner)
        data = {
            'booked_rooms': 2
        }
        response = self.client.patch(f'/api/v1/partner/inventory/{self.date_inventory.id}/', data)

        # booked_rooms tek oqıw bolıwı kerek
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.date_inventory.refresh_from_db()
        self.assertEqual(self.date_inventory.booked_rooms, 0)  # Ózgerissiz qalıwı kerek


class PartnerDateInventoryFilterTests(TestCase):
    """?rate_plan, ?date_from hám ?date_to inventory dizimin shekemleydi."""

    def setUp(self):
        PartnerDateInventoryTests.setUp(self)
        from datetime import date, timedelta
        self.today = date.today()
        self.other_plan = RatePlan.objects.create(
            room_type=self.room_type, name='Flexible', slug='flexible', rate_type='standard',
            base_price=120.00, currency='USD', min_nights=1, is_active=True,
        )
        for offset in range(1, 40):
            DateInventory.objects.create(
                rate_plan=self.rate_plan, date=self.today + timedelta(days=offset),
                available_rooms=5, booked_rooms=0, price=100.00, currency='USD',
            )
        self.other_row = DateInventory.objects.create(
            rate_plan=self.other_plan, date=self.today + timedelta(days=2),
            available_rooms=3, booked_rooms=0, price=120.00, currency='USD',
        )
        self.client.force_authenticate(user=self.hotel_owner)

    def _get(self, **params):
        return self.client.get('/api/v1/partner/inventory/', params)

    def test_date_range_and_rate_plan_filter(self):
        from datetime import timedelta
        response = self._get(
            rate_plan=self.rate_plan.id,
            date_from=(self.today + timedelta(days=1)).isoformat(),
            date_to=(self.today + timedelta(days=7)).isoformat(),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 7)
        dates = [row['date'] for row in response.data['results']]
        self.assertEqual(dates, sorted(dates))
        self.assertEqual(dates[0], (self.today + timedelta(days=1)).isoformat())
        self.assertEqual(dates[-1], (self.today + timedelta(days=7)).isoformat())
        self.assertTrue(all(row['rate_plan'] == self.rate_plan.id for row in response.data['results']))

    def test_rate_plan_filter_alone(self):
        response = self._get(rate_plan=self.other_plan.id)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.other_row.id)

    def test_no_filters_keeps_the_old_behaviour(self):
        response = self._get()
        self.assertEqual(response.data['count'], 41)
        self.assertIsNotNone(response.data['next'])

    def test_invalid_filters_are_rejected(self):
        for params, field in [
            ({'rate_plan': 'abc'}, 'rate_plan'),
            ({'date_from': '24-09-2026'}, 'date_from'),
            ({'date_to': '2026-02-30'}, 'date_to'),
            ({'date_from': '2026-10-10', 'date_to': '2026-10-01'}, 'date_to'),
        ]:
            response = self._get(**params)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, params)
            self.assertIn(field, str(response.data), params)

    def test_filters_never_show_another_owners_inventory(self):
        other_owner = User.objects.create_user(
            email='other-owner@example.com', password='testpassword123', role=self.hotel_owner_role
        )
        self.client.force_authenticate(user=other_owner)
        response = self._get(rate_plan=self.rate_plan.id)
        self.assertEqual(response.data['count'], 0)


class PartnerPropertyPhotoUploadTests(TestCase):
    """Partner mehmanxana súwretin júklew tekseriwi ushın testler (audit #23)."""

    # Eń kishi jaramlı 1x1 GIF, properties/tests/test_models.py degi fixture menen sáykes
    VALID_IMAGE_BYTES = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
        b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
        b'\x02\x4c\x01\x00\x3b'
    )

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
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
        """Haqıyqıy, durıs túrdegi, saytta jaqsı kórinetuǵın ólshemdegi súwret qabıllanadı."""
        from common.testing import image_upload

        self.client.force_authenticate(user=self.hotel_owner)
        image = image_upload(name='photo.jpg')
        response = self.client.post(
            self.upload_url,
            {'photo': image, 'photo_type': 'exterior'},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_hotel_owner_cannot_upload_fake_image(self):
        """
        Súwret keńeytpesi/content-type penen jasırılǵan súwret emes fayl biykar etiliwi kerek.

        DRF tiń ImageField ı payload dı bizdiń kodqa jetpesten aldın Pillow menen aldınan tekseredi,
        sol sebepli bul túzetiwden aldın da ótedi -- ol audit #23 tesigin emes, bar qaplawdı hújjetlestiredi
        (onıń ushın tómendegi keńeytpe/ólshem testlerin qarań).
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
        Bizdiń ruxsat dizimimizden (jpg/jpeg/png/gif/webp) sırtındaǵı formattaǵı haqıyqıy jaramlı súwret
        (Pillow onı jaqsı ashadı) ele biykar etiliwi kerek. model.clean() bunı májbúrleydi, biraq
        DRF onı hesh qashan shaqırmaydı -- audit #23 tiń haqıyqıy tesigi.
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
        10MB shegi nen úlken haqıyqıy jaramlı súwret API tárepinen biykar etiliwi kerek,
        tek model.clean() tárepinen emes (DRF onı hesh qashan shaqırmaydı).
        """
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        import io
        import os

        width, height = 2000, 1800  # tosınarlıq shawqın pikselleri jaman qısıladı -> fayl > 10MB qaladı
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


    def _png(self, width, height):
        import io
        from PIL import Image

        buf = io.BytesIO()
        Image.new('L', (width, height)).save(buf, format='PNG')  # tegis reń: kishi fayl, úlken piksel sanı
        return buf.getvalue()

    def test_hotel_owner_cannot_upload_huge_pixel_dimensions(self):
        """Kishi fayl ele gigabaytlap pikselge ashılıwı múmkin (decompression bomb)."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.force_authenticate(user=self.hotel_owner)
        bomb = SimpleUploadedFile('bomb.png', self._png(12000, 12000), content_type='image/png')

        response = self.client.post(
            self.upload_url, {'photo': bomb, 'photo_type': 'exterior'}, format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('photo', response.data)

    def test_hotel_owner_cannot_exceed_photo_limit_per_property(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from partner.serializers import MAX_PHOTOS_PER_PROPERTY

        PropertyPhoto.objects.bulk_create([
            PropertyPhoto(property=self.property, photo=f'properties/{self.property.id}/photos/p{i}.png')
            for i in range(MAX_PHOTOS_PER_PROPERTY)
        ])
        self.client.force_authenticate(user=self.hotel_owner)
        one_more = SimpleUploadedFile('more.png', self._png(10, 10), content_type='image/png')

        response = self.client.post(
            self.upload_url, {'photo': one_more, 'photo_type': 'exterior'}, format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PropertyPhoto.objects.filter(property=self.property).count(), MAX_PHOTOS_PER_PROPERTY)


class PartnerBookingListTests(TestCase):
    """Partner bronlar dizimi endpoint i ushın testler (audit #26)."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        make_usd_rate()  # R6: USD mehmanxanasın tek kurs bar bolǵanda bronlap boladı
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
        """booking.guest_name modelde joq -- 500 bermewi kerek."""
        self.client.force_authenticate(user=self.hotel_owner)
        response = self.client.get('/api/v1/partner/bookings/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['guest_name'], self.booking.guest_full_name)

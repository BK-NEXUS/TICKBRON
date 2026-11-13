"""
Mehmanxana bos orınları API endpoint i ushın testler.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from properties.models import (
    Property, PropertyType, PropertyAmenity,
    Amenity, AmenityCategory,
    RoomType, RoomAmenity, RatePlan, DateInventory, RoomInventory
)
from datetime import date, timedelta

User = get_user_model()


class PropertyAvailabilityEndpointTest(TestCase):
    """Mehmanxana bos orınları API endpoint i ushın test jaǵdayları."""

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

        # Mehmanxanaǵa amenity lerdi qosıw
        PropertyAmenity.objects.create(
            property=self.property,
            amenity=self.wifi_amenity,
            is_available=True
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

        # Keyingi 7 kún ushın date inventory qosıw
        today = date.today()
        for i in range(1, 8):
            inventory_date = today + timedelta(days=i)
            DateInventory.objects.create(
                rate_plan=self.rate_plan,
                date=inventory_date,
                available_rooms=5,
                booked_rooms=0,
                price=50.00,
                currency='USD',
                is_available=True
            )

        # Taǵı bir xona túrin qosıw
        self.room_type_2 = RoomType.objects.create(
            property=self.property,
            name='Deluxe Room',
            slug='deluxe-room',
            description='Spacious deluxe room',
            base_occupancy=2,
            max_occupancy=3,
            base_price=80.00,
            currency='USD',
            total_rooms=3
        )

        # Ekinshi xona túri ushın rate plan qosıw
        self.rate_plan_2 = RatePlan.objects.create(
            room_type=self.room_type_2,
            name='Deluxe Rate',
            slug='deluxe-rate',
            rate_type='standard',
            description='Deluxe rate with extra amenities',
            base_price=80.00,
            currency='USD',
            min_nights=1,
            is_active=True
        )

        # Ekinshi rate plan ushın date inventory qosıw
        for i in range(1, 8):
            inventory_date = today + timedelta(days=i)
            DateInventory.objects.create(
                rate_plan=self.rate_plan_2,
                date=inventory_date,
                available_rooms=3,
                booked_rooms=0,
                price=80.00,
                currency='USD',
                is_available=True
            )

    def test_availability_success(self):
        """Tabıslı bos orın sorawın testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['id'], self.property.id)
        self.assertIn('room_types', response.data)

    def test_availability_includes_property_info(self):
        """Bos orın tiykarǵı mehmanxana maǵlıwmatın óz ishine alatuǵının testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['city'], 'Tashkent')
        self.assertEqual(response.data['country'], 'Uzbekistan')
        self.assertEqual(response.data['max_guests'], 4)
        self.assertEqual(str(response.data['base_price']), '50.00')

    def test_availability_includes_room_types(self):
        """Bos orın xona túrlerin óz ishine alatuǵının testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')

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

    def test_availability_includes_rate_plans(self):
        """Xona túrleri rate plan lardı óz ishine alatuǵının testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')

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

    def test_availability_includes_date_inventory(self):
        """Rate plan lar date inventory di óz ishine alatuǵının testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        room_types = response.data['room_types']
        first_room_type = room_types[0]
        rate_plans = first_room_type['rate_plans']
        first_rate_plan = rate_plans[0]

        self.assertIn('date_inventory', first_rate_plan)
        date_inventory = first_rate_plan['date_inventory']
        self.assertGreater(len(date_inventory), 0)

        # Date inventory dúzilisin tekseriw
        first_inventory = date_inventory[0]
        self.assertIn('date', first_inventory)
        self.assertIn('available_rooms', first_inventory)
        self.assertIn('booked_rooms', first_inventory)
        self.assertIn('remaining_rooms', first_inventory)
        self.assertIn('price', first_inventory)
        self.assertIn('is_available', first_inventory)

    def test_availability_with_date_range(self):
        """Sana aralıǵı parametrleri menen bos orındı testlew."""
        today = date.today()
        check_in = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        check_out = (today + timedelta(days=3)).strftime('%Y-%m-%d')

        response = self.client.get(
            f'/api/v1/properties/{self.property.id}/availability/',
            {'check_in': check_in, 'check_out': check_out}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Date inventory sana aralıǵı boyınsha filterlengenin tekseriw
        room_types = response.data['room_types']
        first_room_type = room_types[0]
        rate_plans = first_room_type['rate_plans']
        first_rate_plan = rate_plans[0]
        date_inventory = first_rate_plan['date_inventory']

        # Tek aralıqtaǵı sanalardı óz ishine alıwı kerek
        self.assertLessEqual(len(date_inventory), 3)

    def test_availability_with_only_check_in(self):
        """Tek check_in parametri menen bos orındı testlew."""
        today = date.today()
        check_in = (today + timedelta(days=2)).strftime('%Y-%m-%d')

        response = self.client.get(
            f'/api/v1/properties/{self.property.id}/availability/',
            {'check_in': check_in}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Date inventory check_in nen baslap filterlengenin tekseriw
        room_types = response.data['room_types']
        first_room_type = room_types[0]
        rate_plans = first_room_type['rate_plans']
        first_rate_plan = rate_plans[0]
        date_inventory = first_rate_plan['date_inventory']

        # Tek check_in nen baslap sanalardı óz ishine alıwı kerek
        self.assertGreater(len(date_inventory), 0)

    def test_availability_invalid_date_format(self):
        """Jaramsız sana formatı menen bos orındı testlew."""
        response = self.client.get(
            f'/api/v1/properties/{self.property.id}/availability/',
            {'check_in': 'invalid-date', 'check_out': '2024-01-10'}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_availability_invalid_date_range(self):
        """Jaramsız sana aralıǵı (check_in nen aldın check_out) menen bos orındı testlew."""
        today = date.today()
        check_in = (today + timedelta(days=5)).strftime('%Y-%m-%d')
        check_out = (today + timedelta(days=2)).strftime('%Y-%m-%d')

        response = self.client.get(
            f'/api/v1/properties/{self.property.id}/availability/',
            {'check_in': check_in, 'check_out': check_out}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_availability_property_not_found(self):
        """Joq mehmanxana ID si menen bos orındı testlew."""
        response = self.client.get('/api/v1/properties/99999/availability/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_availability_deleted_property(self):
        """Óshirilgen mehmanxana menen bos orındı testlew."""
        # Mehmanxananı soft-delete etiw
        self.property.is_deleted = True
        self.property.save()

        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_availability_inactive_property(self):
        """Aktiv emes mehmanxana menen bos orındı testlew."""
        # Mehmanxananı aktiv emes etiw
        self.property.is_active = False
        self.property.save()

        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_availability_public_access(self):
        """Bos orın endpoint i ashıq qol jetimli ekenin testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')

        # Autentifikaciyasız islewi kerek
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_availability_deterministic_pricing(self):
        """Bos orın bahası anıq ekenin testlew (birdey kirisiw = birdey shıǵıs)."""
        today = date.today()
        check_in = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        check_out = (today + timedelta(days=3)).strftime('%Y-%m-%d')

        # Birdey sorawdı eki ret islew
        response1 = self.client.get(
            f'/api/v1/properties/{self.property.id}/availability/',
            {'check_in': check_in, 'check_out': check_out}
        )

        response2 = self.client.get(
            f'/api/v1/properties/{self.property.id}/availability/',
            {'check_in': check_in, 'check_out': check_out}
        )

        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Juwaplardı salıstırıw
        self.assertEqual(response1.data, response2.data)

    def test_availability_remaining_rooms_calculation(self):
        """remaining_rooms durıs esaplanatuǵının testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        room_types = response.data['room_types']
        first_room_type = room_types[0]
        rate_plans = first_room_type['rate_plans']
        first_rate_plan = rate_plans[0]
        date_inventory = first_rate_plan['date_inventory']

        # remaining_rooms esaplawın tekseriw
        first_inventory = date_inventory[0]
        expected_remaining = first_inventory['available_rooms'] - first_inventory['booked_rooms']
        self.assertEqual(first_inventory['remaining_rooms'], expected_remaining)

    def test_availability_filters_inactive_rate_plans(self):
        """Aktiv emes rate plan lar filterlenip taslanatuǵının testlew."""
        # Bir rate plan dı aktiv emes etiw
        self.rate_plan.is_active = False
        self.rate_plan.save()

        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        room_types = response.data['room_types']
        first_room_type = room_types[0]
        rate_plans = first_room_type['rate_plans']

        # Aktiv emes rate plan kirmewi kerek
        rate_plan_ids = [rp['id'] for rp in rate_plans]
        self.assertNotIn(self.rate_plan.id, rate_plan_ids)

    def test_availability_multiple_room_types(self):
        """Bir neshe xona túri menen bos orındı testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        room_types = response.data['room_types']

        # Eki xona túri de kiriwi kerek
        self.assertEqual(len(room_types), 2)
        room_type_ids = [rt['id'] for rt in room_types]
        self.assertIn(self.room_type.id, room_type_ids)
        self.assertIn(self.room_type_2.id, room_type_ids)

    def test_availability_no_date_range(self):
        """Sana aralıǵı parametrlerisiz bos orındı testlew."""
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Barlıq date inventory di qaytarıwı kerek
        room_types = response.data['room_types']
        first_room_type = room_types[0]
        rate_plans = first_room_type['rate_plans']
        first_rate_plan = rate_plans[0]
        date_inventory = first_rate_plan['date_inventory']

        # Barlıq 7 kúnlik inventory di óz ishine alıwı kerek
        self.assertEqual(len(date_inventory), 7)


class PropertyAvailabilityUsesRoomInventoryTest(TestCase):
    """
    3.4 (audit #31): ashıq bos orın juwabınıń remaining_rooms (hám
    available_rooms/booked_rooms) DateInventory diń óz baǵanalarınan emes, RoomInventory den,
    xona túriniń ortaq fizikalıq xona sanınan kelwi kerek -- bron sisteması olardı 3.3 te jazıwdı toqtattı,
    sol sebepli olar haqıyqatında bronlanǵannan ayrılıp ketiwi múmkin.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='owner-ri@example.com', password='testpass123')
        self.property_type = PropertyType.objects.create(name='Hotel', slug='hotel-ri')
        self.property = Property.objects.create(
            owner=self.user, property_type=self.property_type, status='active',
            max_guests=2, bedrooms=1, bathrooms=1, address_line1='1 RI St',
            city='Tashkent', country='Uzbekistan', base_price=50.00, currency='USD',
        )
        self.room_type = RoomType.objects.create(
            property=self.property, name='Room', slug='room-ri',
            base_occupancy=2, max_occupancy=2, base_price=50.00, currency='USD', total_rooms=5,
        )
        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type, name='Standard', slug='standard-ri', rate_type='standard',
            base_price=50.00, currency='USD', min_nights=1, is_active=True,
        )
        self.date = date.today() + timedelta(days=1)
        # DateInventory pútkilley bos deydi -- eskirgen, bron sisteması bunı endi jazbaydı
        DateInventory.objects.create(
            rate_plan=self.rate_plan, date=self.date, available_rooms=5, booked_rooms=0,
            price=50.00, currency='USD', is_available=True,
        )
        # RoomInventory (audit #31) bron sisteması haqıyqatında jańalaytuǵın nárse
        RoomInventory.objects.create(
            room_type=self.room_type, date=self.date, available_rooms=5, booked_rooms=3, is_available=True,
        )

    def _date_row(self, response, target_date):
        date_inventory = response.data['room_types'][0]['rate_plans'][0]['date_inventory']
        return next(row for row in date_inventory if str(row['date']) == target_date.isoformat())

    def test_remaining_rooms_reflects_room_inventory_not_date_inventory(self):
        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = self._date_row(response, self.date)
        self.assertEqual(row['booked_rooms'], 3)  # RoomInventory diń haqıyqıy sanı, DateInventory diń eskirgen 0 emes
        self.assertEqual(row['remaining_rooms'], 2)

    def test_unmanaged_night_falls_back_to_room_type_total(self):
        """RoomInventory qatarı joq tún basqarılmaydı: xona túriniń tolıq total_rooms ı menen ashıq."""
        other_date = self.date + timedelta(days=1)
        DateInventory.objects.create(
            rate_plan=self.rate_plan, date=other_date, available_rooms=1, booked_rooms=1,
            price=50.00, currency='USD', is_available=True,
        )

        response = self.client.get(f'/api/v1/properties/{self.property.id}/availability/')

        row = self._date_row(response, other_date)
        self.assertEqual(row['available_rooms'], 5)
        self.assertEqual(row['booked_rooms'], 0)
        self.assertEqual(row['remaining_rooms'], 5)

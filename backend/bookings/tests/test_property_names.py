"""
Bookings and support lookup show the hotel name, not the address (E2E UX 13).
"""
from rest_framework.test import APIClient

from bookings.tests.test_booking_logic import BookingLogicTestBase
from properties.models import PropertyTranslation
from users.models import User


class TestPropertyNameInBookings(BookingLogicTestBase):
    def setUp(self):
        super().setUp()
        PropertyTranslation.objects.create(property=self.property, language='ru', name='Отель Тест', description='x')
        PropertyTranslation.objects.create(property=self.property, language='en', name='Test Hotel', description='x')
        self.booking = self.create_booking()

    def test_booking_list_shows_the_english_hotel_name(self):
        response = self.client.get('/api/v1/bookings/')

        assert response.status_code == 200
        assert response.data[0]['property_name'] == 'Test Hotel'

    def test_support_lookup_shows_the_hotel_name(self):
        staff = User.objects.create_user(email='staff@example.com', password='x', is_staff=True)
        client = APIClient()
        client.force_authenticate(user=staff)

        response = client.get('/api/v1/admin-panel/bookings/lookup/', {'reference_code': self.booking.confirmation_code})

        assert response.status_code == 200
        assert response.data['property']['name'] == 'Test Hotel'

    def test_name_falls_back_to_another_language_then_the_address(self):
        self.property.translations.filter(language='en').delete()
        assert self.property.display_name() == 'Отель Тест'

        self.property.translations.all().delete()
        assert self.property.display_name() == self.property.get_full_address()

    def test_admin_customer_profile_bookings_show_the_hotel_name(self):
        staff = User.objects.create_user(email='staff2@example.com', password='x', is_staff=True)
        client = APIClient()
        client.force_authenticate(user=staff)

        response = client.get(f'/api/v1/admin-panel/customers/{self.user.id}/')

        assert response.status_code == 200
        assert [b['property_name'] for b in response.data['bookings']] == ['Test Hotel']

    def test_partner_bookings_show_the_hotel_name(self):
        # BookingLogicTestBase makes the guest the property owner
        client = APIClient()
        from permissions.models import Role
        self.user.role = Role.objects.create(name='hotel-owner')
        self.user.save(update_fields=['role'])
        client.force_authenticate(user=self.user)

        response = client.get('/api/v1/partner/bookings/')

        assert response.status_code == 200
        assert [b['property_name'] for b in response.data] == ['Test Hotel']

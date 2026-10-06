"""
R12 1d: notifications carry a machine-readable `code` + `params` (ids, amounts, dates only)
and an English fallback title/message, created through `accounts.notify()`.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from rest_framework.test import APIClient

import accounts
from accounts.models import Notification
from accounts.notifications import NOTIFICATION_CODES, NotificationParamsError
from bookings.tests.r12_helpers import make_booking
from common.dates import business_today
from properties.models import Property, PropertyType
from users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def guest():
    return User.objects.create_user(email='guest@example.com', password='x', first_name='Alisher')


@pytest.fixture
def booking(guest):
    owner = User.objects.create_user(email='owner@example.com', password='x')
    hotel = Property.objects.create(
        owner=owner, property_type=PropertyType.objects.create(name='Hotel', slug='hotel'),
        status='active', max_guests=2, bedrooms=1, bathrooms=1, address_line1='1', city='Tashkent',
        country='Uzbekistan', base_price=500000, currency='UZS',
    )
    return make_booking(hotel, guest, business_today() + timedelta(days=3))


class TestNotify:

    def test_stores_code_params_and_english_fallback(self, guest, booking):
        n = accounts.notify(guest, 'no_show_marked', {
            'booking_id': booking.id, 'booking_reference': booking.confirmation_code,
            'amount': Decimal('1177295'), 'currency': 'UZS', 'percent': 50,
        }, booking=booking)
        n.refresh_from_db()
        assert n.user == guest and n.booking == booking
        assert n.code == 'no_show_marked'
        assert n.notification_type == 'booking'
        assert n.params == {
            'booking_id': booking.id, 'booking_reference': booking.confirmation_code,
            'amount': '1177295', 'currency': 'UZS', 'percent': 50,
        }
        assert booking.confirmation_code in n.title + n.message
        assert '1177295' in n.message and '50%' in n.message
        assert n.is_read is False

    def test_dates_are_stored_as_iso_strings(self, guest, booking):
        n = accounts.notify(guest, 'no_show_report_rejected', {
            'report_id': 7, 'booking_id': booking.id, 'booking_reference': booking.confirmation_code,
            'check_in': date(2026, 10, 1),
        })
        n.refresh_from_db()
        assert n.params['check_in'] == '2026-10-01'

    def test_every_code_renders_with_its_documented_params(self, guest):
        sample = {
            'booking_id': 1, 'booking_reference': 'TB-ABC123', 'report_id': 2, 'refund_id': 3,
            'amount': '1000', 'currency': 'UZS', 'percent': 50, 'check_in': '2026-10-01',
            'check_out': '2026-10-03',
        }
        for code, spec in NOTIFICATION_CODES.items():
            params = {key: sample[key] for key in spec['params']}
            n = accounts.notify(guest, code, params)
            assert n.title and n.message and '{' not in n.title + n.message, code

    def test_unknown_code_is_refused(self, guest):
        with pytest.raises(ValueError):
            accounts.notify(guest, 'no_such_code', {})
        assert Notification.objects.count() == 0

    def test_missing_param_is_refused(self, guest):
        with pytest.raises(NotificationParamsError):
            accounts.notify(guest, 'no_show_marked', {'booking_id': 1})
        assert Notification.objects.count() == 0


class TestParamsNeverContainPersonalData:

    BASE = {'report_id': 1, 'booking_id': 1, 'booking_reference': 'TB-ABC123'}

    @pytest.mark.parametrize('key, value', [
        ('email', 'guest@example.com'),
        ('phone', '+998901234567'),
        ('guest_name', 'Alisher Navoiy'),
        ('first_name', 'Alisher'),
        ('comment', 'The guest never came'),
        ('address', 'Amir Temur 1'),
        ('passport', 'AA1234567'),
    ])
    def test_personal_keys_are_refused(self, guest, key, value):
        with pytest.raises(NotificationParamsError):
            accounts.notify(guest, 'no_show_report_rejected', {**self.BASE, key: value})
        assert Notification.objects.count() == 0

    @pytest.mark.parametrize('key, value', [
        ('booking_reference', 'guest@example.com'),
        ('booking_reference', 'Alisher Navoiy'),
        ('booking_reference', '+998901234567'),
        ('booking_id', 'guest@example.com'),
        ('booking_id', '12'),
        ('report_id', True),
        ('amount', 'Alisher'),
        ('amount', '+998901234567'),
        ('currency', 'Alisher'),
        ('percent', 150),
        ('check_in', 'Alisher'),
    ])
    def test_values_that_are_not_ids_amounts_or_dates_are_refused(self, guest, key, value):
        params = {**self.BASE, 'amount': '1000', 'currency': 'UZS', 'percent': 50, key: value}
        with pytest.raises(NotificationParamsError):
            accounts.notify(guest, 'no_show_marked', params)
        assert Notification.objects.count() == 0

    def test_fallback_text_contains_no_personal_data(self, guest, booking):
        n = accounts.notify(guest, 'no_show_marked', {
            'booking_id': booking.id, 'booking_reference': booking.confirmation_code,
            'amount': '1000', 'currency': 'UZS', 'percent': 50,
        }, booking=booking)
        text = n.title + n.message
        assert guest.email not in text
        assert 'Alisher' not in text and 'Test Guest' not in text


class TestApi:

    def test_list_returns_code_and_params(self, guest, booking):
        accounts.notify(guest, 'no_show_report_approved', {
            'report_id': 5, 'booking_id': booking.id, 'booking_reference': booking.confirmation_code,
        }, booking=booking)
        client = APIClient()
        client.force_authenticate(guest)
        response = client.get('/api/v1/me/notifications/')
        assert response.status_code == 200
        rows = response.data['results'] if isinstance(response.data, dict) else response.data
        assert rows[0]['code'] == 'no_show_report_approved'
        assert rows[0]['params'] == {
            'report_id': 5, 'booking_id': booking.id, 'booking_reference': booking.confirmation_code,
        }

    def test_old_notifications_have_null_code_and_params(self, guest):
        Notification.objects.create(user=guest, notification_type='system', title='Hello', message='Old')
        client = APIClient()
        client.force_authenticate(guest)
        rows = client.get('/api/v1/me/notifications/').data
        rows = rows['results'] if isinstance(rows, dict) else rows
        assert rows[0]['code'] is None and rows[0]['params'] is None

    def test_code_and_params_cannot_be_changed_by_the_user(self, guest):
        n = accounts.notify(guest, 'no_show_report_rejected', {
            'report_id': 1, 'booking_id': 1, 'booking_reference': 'TB-ABC123',
        })
        client = APIClient()
        client.force_authenticate(guest)
        client.patch(f'/api/v1/me/notifications/{n.id}/', {'code': 'x', 'params': {'a': 1}}, format='json')
        n.refresh_from_db()
        assert n.code == 'no_show_report_rejected' and n.params['report_id'] == 1


class NotificationMigrationIsReversible(TransactionTestCase):

    def setUp(self):
        super().setUp()
        if connection.vendor != 'postgresql':
            self.skipTest('Migration executor tests need PostgreSQL')

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def _columns(self):
        with connection.cursor() as cursor:
            return {c.name for c in connection.introspection.get_table_description(cursor, 'notifications')}

    def test_reverse_drops_code_and_params_and_forward_adds_them(self):
        user = User.objects.create_user(email='m@example.com', password='x')
        Notification.objects.create(user=user, notification_type='system', title='Old', message='Kept')
        executor = MigrationExecutor(connection)
        executor.migrate([('accounts', '0001_initial')])
        assert not {'code', 'params'} & self._columns()
        with connection.cursor() as cursor:
            cursor.execute("SELECT title FROM notifications")
            assert [row[0] for row in cursor.fetchall()] == ['Old']
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate([('accounts', '0002_notification_code_params')])
        assert {'code', 'params'} <= self._columns()

"""
R4 / audit #21: admin access audit log.

Every time staff open customer data (customer list, a customer profile, a support
lookup by booking reference, the user list, the Status users list) one row is
written: who, what, which customer/booking id, when. Only ids are stored, never
copies of personal data. Rows cannot be changed or deleted, and only staff can
read them through GET /api/v1/admin-panel/audit-log/.
"""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from admin_panel.models import AdminAccessLog
from bookings.models import Booking
from permissions.models import Role
from properties.models import Property, PropertyType
from users.models import User

A = '/api/v1/admin-panel'


@pytest.fixture
def people(db):
    staff = User.objects.create_user(email='staff@example.com', password='x', is_staff=True)
    guest = User.objects.create_user(email='guest@example.com', password='x', phone_number='+998901112233')
    owner = User.objects.create_user(
        email='owner@example.com', password='x',
        role=Role.objects.get_or_create(name='hotel-owner')[0],
    )
    prop = Property.objects.create(
        owner=owner, property_type=PropertyType.objects.create(name='Hotel', slug='hotel'),
        status='active', max_guests=2, bedrooms=1, bathrooms=1, city='Tashkent', country='Uzbekistan',
        base_price=Decimal('50'), currency='USD',
    )
    check_in = timezone.localdate() + timedelta(days=5)
    booking = Booking.objects.create(
        guest=guest, property=prop, status='confirmed', payment_status='paid', check_in=check_in,
        check_out=check_in + timedelta(days=2), number_of_nights=2, guest_count=1,
        total_price=Decimal('100'), currency='USD', confirmation_code='AUD123',
    )
    return {'staff': staff, 'guest': guest, 'owner': owner, 'booking': booking}


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestAccessIsRecorded:

    def test_customer_profile_view(self, people):
        response = _client(people['staff']).get(f"{A}/customers/{people['guest'].id}/")

        assert response.status_code == 200
        entry = AdminAccessLog.objects.get()
        assert entry.actor_id == people['staff'].id
        assert entry.action == 'customer_view'
        assert entry.target_user_id == people['guest'].id
        assert entry.created_at is not None

    def test_customer_list(self, people):
        assert _client(people['staff']).get(f'{A}/customers/').status_code == 200
        assert AdminAccessLog.objects.get().action == 'customer_list'

    def test_support_lookup(self, people):
        response = _client(people['staff']).get(f'{A}/bookings/lookup/', {'reference_code': 'aud123'})

        assert response.status_code == 200
        entry = AdminAccessLog.objects.get()
        assert entry.action == 'booking_lookup'
        assert entry.target_booking_id == people['booking'].id
        assert entry.target_user_id == people['guest'].id

    def test_user_list(self, people):
        assert _client(people['staff']).get(f'{A}/users/').status_code == 200
        assert AdminAccessLog.objects.get().action == 'user_list'

    def test_status_users_list(self, people):
        assert _client(people['staff']).get(f'{A}/status/users/').status_code == 200
        assert AdminAccessLog.objects.get().action == 'status_users'

    def test_nothing_recorded_when_nothing_was_shown(self, people):
        staff = _client(people['staff'])
        assert staff.get(f'{A}/customers/999999/').status_code == 404
        assert staff.get(f'{A}/bookings/lookup/', {'reference_code': 'NOPE00'}).status_code == 404
        assert _client(people['guest']).get(f"{A}/customers/{people['guest'].id}/").status_code == 403

        assert not AdminAccessLog.objects.exists()


@pytest.mark.django_db
class TestLogHoldsIdsOnly:

    def test_fields_are_ids_action_and_time(self):
        names = {f.name for f in AdminAccessLog._meta.get_fields()}
        assert names == {'id', 'actor_id', 'action', 'target_user_id', 'target_booking_id', 'created_at'}

    def test_search_terms_are_not_stored(self, people):
        _client(people['staff']).get(f'{A}/status/users/', {'search': '+998901112233'})

        entry = AdminAccessLog.objects.values().get()
        assert '+998901112233' not in str(entry)


@pytest.mark.django_db
class TestAppendOnly:

    def test_entry_cannot_be_changed(self, people):
        entry = AdminAccessLog.record(people['staff'], 'customer_view', target_user_id=people['guest'].id)
        entry.target_user_id = 1

        with pytest.raises(PermissionError):
            entry.save()
        with pytest.raises(PermissionError):
            AdminAccessLog.objects.filter(pk=entry.pk).update(target_user_id=1)
        assert AdminAccessLog.objects.get(pk=entry.pk).target_user_id == people['guest'].id

    def test_entry_cannot_be_deleted(self, people):
        entry = AdminAccessLog.record(people['staff'], 'customer_view', target_user_id=people['guest'].id)

        with pytest.raises(PermissionError):
            entry.delete()
        with pytest.raises(PermissionError):
            AdminAccessLog.objects.all().delete()
        assert AdminAccessLog.objects.count() == 1


@pytest.mark.django_db
class TestAuditLogEndpoint:

    def test_staff_can_read_the_log_newest_first(self, people):
        staff = _client(people['staff'])
        staff.get(f'{A}/customers/')
        staff.get(f"{A}/customers/{people['guest'].id}/")

        response = staff.get(f'{A}/audit-log/')

        assert response.status_code == 200
        rows = response.data['results']
        assert [r['action'] for r in rows] == ['customer_view', 'customer_list']
        assert set(rows[0]) == {'id', 'actor_id', 'action', 'target_user_id', 'target_booking_id', 'created_at'}

    def test_filters(self, people):
        staff = _client(people['staff'])
        staff.get(f'{A}/customers/')
        staff.get(f"{A}/customers/{people['guest'].id}/")

        by_target = staff.get(f'{A}/audit-log/', {'target_user_id': people['guest'].id}).data['results']
        by_action = staff.get(f'{A}/audit-log/', {'action': 'customer_list'}).data['results']

        assert [r['action'] for r in by_target] == ['customer_view']
        assert [r['action'] for r in by_action] == ['customer_list']

    def test_reading_the_log_is_not_itself_a_customer_access(self, people):
        _client(people['staff']).get(f'{A}/audit-log/')
        assert not AdminAccessLog.objects.exists()

    @pytest.mark.parametrize('who', ['anonymous', 'guest', 'owner'])
    def test_non_staff_cannot_read_the_log(self, people, who):
        client = APIClient() if who == 'anonymous' else _client(people[who])
        assert client.get(f'{A}/audit-log/').status_code in (401, 403)

    @pytest.mark.parametrize('method', ['post', 'put', 'patch', 'delete'])
    def test_log_cannot_be_written_through_the_api(self, people, method):
        response = getattr(_client(people['staff']), method)(f'{A}/audit-log/', {}, format='json')
        assert response.status_code == 405

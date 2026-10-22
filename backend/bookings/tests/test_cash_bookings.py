"""
Cash at the hotel (plan .ai/PLAN_CASH_ONLY.md stage 2): a booking is confirmed at once, the guest says
when they will arrive, the hotel marks "guest arrived", and a confirmed booking whose guest has not
arrived 2 hours after the given time is cancelled and the room is released.
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
import zoneinfo

from django.conf import settings
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import Notification
from bookings.arrival import arrival_deadline, arrival_time_error, cancel_unarrived_bookings
from bookings.models import Booking
from bookings.tests import test_views
from permissions.models import Role
from properties.models import RoomInventory
from users.models import User

TASHKENT = zoneinfo.ZoneInfo('Asia/Tashkent')


def tashkent(day, hour, minute=0):
    return datetime.combine(day, time(hour, minute), tzinfo=TASHKENT)


class CashFixture(APITestCase):
    """The hotel of the booking view tests, owned by a real hotel owner (not the guest)."""

    def setUp(self):
        test_views.BookingViewTests.setUp(self)
        role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'is_system_role': True})
        self.owner = User.objects.create_user(email='owner@example.com', password='OwnerPass#123', role=role,
                                              phone_number='+998901110000')
        self.other_owner = User.objects.create_user(email='owner2@example.com', password='OwnerPass#123', role=role,
                                                    phone_number='+998901110001')
        self.property.owner = self.owner
        self.property.save()
        self.client.force_authenticate(user=self.user)

    def book(self, **extra):
        data = {
            'property_id': self.property.id, 'room_type_id': self.room_type.id, 'rate_plan_id': self.rate_plan.id,
            'check_in': self.check_in.strftime('%Y-%m-%d'), 'check_out': self.check_out.strftime('%Y-%m-%d'),
            'guest_count': 1, 'expected_arrival_time': '14:00', **extra,
        }
        return self.client.post('/api/v1/bookings/', data, format='json')

    def owner_client(self, user=None):
        api = APIClient()
        api.force_authenticate(user=user or self.owner)
        return api


class CreateTests(CashFixture):
    def test_a_booking_is_confirmed_at_once_with_the_arrival_time(self):
        response = self.book(expected_arrival_time='10:30')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['status'], 'confirmed')
        self.assertEqual(response.data['expected_arrival_time'], '10:30:00')
        self.assertIsNone(response.data['arrived_at'])
        self.assertTrue(response.data['arrival_deadline'].startswith(f'{self.check_in.isoformat()}T12:30:00'))
        booking = Booking.objects.get()
        self.assertEqual((booking.status, booking.payment_status), ('confirmed', 'pending'))
        self.assertIsNone(booking.expires_at)  # no payment window any more

    def test_the_room_is_taken_at_once(self):
        self.book()
        inventory = RoomInventory.objects.filter(room_type=self.room_type)
        self.assertTrue(inventory.exists())
        self.assertTrue(all(row.booked_rooms == 1 for row in inventory))

    def test_the_arrival_time_is_required(self):
        data = {'property_id': self.property.id, 'room_type_id': self.room_type.id, 'rate_plan_id': self.rate_plan.id,
                'check_in': self.check_in.isoformat(), 'check_out': self.check_out.isoformat(), 'guest_count': 1}
        response = self.client.post('/api/v1/bookings/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('expected_arrival_time', response.data['details'])
        self.assertFalse(Booking.objects.exists())

    def test_a_bad_arrival_time_is_refused(self):
        for value in ('25:00', 'noon', '', '10'):
            response = self.book(expected_arrival_time=value)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, value)
        self.assertFalse(Booking.objects.exists())

    def test_a_guest_cannot_hold_more_than_the_limit_of_upcoming_bookings(self):
        from bookings.views import MAX_UPCOMING_BOOKINGS_PER_GUEST
        for _ in range(MAX_UPCOMING_BOOKINGS_PER_GUEST):
            self.assertEqual(self.book().status_code, status.HTTP_201_CREATED)
        response = self.book()
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.data['code'], 'too_many_upcoming_bookings')

    def test_cancelled_and_arrived_bookings_do_not_count_against_the_limit(self):
        from bookings.views import BookingViewSet, MAX_UPCOMING_BOOKINGS_PER_GUEST
        for _ in range(MAX_UPCOMING_BOOKINGS_PER_GUEST):
            self.book()
        self.assertTrue(BookingViewSet._pending_cap_reached(self.user))
        first, second = Booking.objects.order_by('id')[:2]
        first.cancel_booking('user_cancelled')
        self.assertFalse(BookingViewSet._pending_cap_reached(self.user))
        Booking.objects.filter(pk=second.pk).update(arrived_at=datetime.now(tz=TASHKENT))
        self.assertEqual(BookingViewSet._pending_cap_reached(self.user), False)
        Booking.objects.filter(pk__in=list(Booking.objects.values_list('pk', flat=True))).update(check_out=date.today() - timedelta(days=1))
        self.assertFalse(BookingViewSet._pending_cap_reached(self.user))  # stays that are over do not count


class ArrivalRulesTests(TestCase):
    def test_deadline_is_the_arrival_time_plus_the_grace_in_business_time(self):
        booking = Booking(check_in=date(2026, 11, 3), expected_arrival_time=time(10, 0))
        self.assertEqual(arrival_deadline(booking), tashkent(date(2026, 11, 3), 12, 0))

    def test_a_late_evening_arrival_is_cancelled_after_midnight(self):
        booking = Booking(check_in=date(2026, 11, 3), expected_arrival_time=time(23, 0))
        self.assertEqual(arrival_deadline(booking), tashkent(date(2026, 11, 4), 1, 0))

    def test_the_grace_is_a_setting(self):
        self.assertEqual(settings.ARRIVAL_GRACE_HOURS, 2)

    def test_an_old_booking_without_an_arrival_time_has_no_deadline(self):
        self.assertIsNone(arrival_deadline(Booking(check_in=date(2026, 11, 3), expected_arrival_time=None)))

    def test_arriving_today_needs_a_time_that_has_not_passed(self):
        today = date(2026, 11, 3)
        now = tashkent(today, 14, 0)
        self.assertIsNotNone(arrival_time_error(today, time(9, 0), now))
        self.assertIsNone(arrival_time_error(today, time(15, 0), now))
        self.assertIsNone(arrival_time_error(today + timedelta(days=1), time(9, 0), now))


class MarkArrivedTests(CashFixture):
    def make(self):
        return Booking.objects.get(pk=self.book().data['id'])

    def url(self, booking):
        return f'/api/v1/partner/bookings/{booking.id}/arrived/'

    def test_the_owner_marks_the_guest_as_arrived(self):
        booking = self.make()
        response = self.owner_client().post(self.url(booking), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        Booking.objects.filter(pk=booking.pk).update(check_in=date.today() - timedelta(days=0))
        response = self.owner_client().post(self.url(booking), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        booking.refresh_from_db()
        self.assertIsNotNone(booking.arrived_at)
        self.assertEqual(response.json()['arrived_at'], booking.arrived_at.isoformat().replace('+00:00', 'Z'))

    def test_marking_twice_keeps_the_first_time(self):
        booking = self.make()
        Booking.objects.filter(pk=booking.pk).update(check_in=date.today())
        first = self.owner_client().post(self.url(booking), format='json').json()['arrived_at']
        second = self.owner_client().post(self.url(booking), format='json')
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(second.json()['arrived_at'], first)

    def test_another_owner_gets_404_and_the_guest_403(self):
        booking = self.make()
        Booking.objects.filter(pk=booking.pk).update(check_in=date.today())
        self.assertEqual(self.owner_client(self.other_owner).post(self.url(booking), format='json').status_code, 404)
        self.assertEqual(self.client.post(self.url(booking), format='json').status_code, 403)
        self.assertEqual(APIClient().post(self.url(booking), format='json').status_code, 403)  # anonymous: session auth
        self.assertIsNone(Booking.objects.get(pk=booking.pk).arrived_at)

    def test_a_cancelled_booking_cannot_be_marked(self):
        booking = self.make()
        Booking.objects.filter(pk=booking.pk).update(check_in=date.today())
        booking.refresh_from_db()
        booking.cancel_booking('user_cancelled')
        response = self.owner_client().post(self.url(booking), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_the_owner_sees_the_arrival_time_in_the_bookings_list(self):
        self.make()
        rows = self.owner_client().get('/api/v1/partner/bookings/').json()
        rows = rows['results'] if isinstance(rows, dict) else rows
        self.assertEqual(rows[0]['expected_arrival_time'], '14:00:00')
        self.assertIsNone(rows[0]['arrived_at'])


class AutoCancelTests(CashFixture):
    def make(self, arrival='10:00'):
        booking = Booking.objects.get(pk=self.book(expected_arrival_time=arrival).data['id'])
        return booking

    def test_a_guest_who_did_not_arrive_is_cancelled_after_the_grace_and_the_room_is_released(self):
        booking = self.make('10:00')
        after = tashkent(self.check_in, 12, 1)
        result = cancel_unarrived_bookings(now=after)
        self.assertEqual(result['cancelled'], 1)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
        self.assertEqual(booking.cancellation_reason, 'no_arrival')
        self.assertTrue(all(row.booked_rooms == 0 for row in RoomInventory.objects.filter(room_type=self.room_type)))

    def test_nothing_happens_before_the_deadline(self):
        booking = self.make('10:00')
        self.assertEqual(cancel_unarrived_bookings(now=tashkent(self.check_in, 11, 59))['cancelled'], 0)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'confirmed')

    def test_an_arrived_guest_is_never_cancelled(self):
        booking = self.make('10:00')
        Booking.objects.filter(pk=booking.pk).update(arrived_at=tashkent(self.check_in, 10, 20))
        self.assertEqual(cancel_unarrived_bookings(now=tashkent(self.check_in + timedelta(days=1), 3))['cancelled'], 0)

    def test_an_old_booking_without_an_arrival_time_is_never_cancelled(self):
        booking = self.make('10:00')
        Booking.objects.filter(pk=booking.pk).update(expected_arrival_time=None)
        self.assertEqual(cancel_unarrived_bookings(now=tashkent(self.check_in + timedelta(days=3), 3))['cancelled'], 0)

    def test_running_twice_cancels_once_and_notifies_once(self):
        self.make('10:00')
        after = tashkent(self.check_in, 13, 0)
        self.assertEqual(cancel_unarrived_bookings(now=after)['cancelled'], 1)
        self.assertEqual(cancel_unarrived_bookings(now=after)['cancelled'], 0)
        self.assertEqual(Notification.objects.filter(code='booking_not_arrived').count(), 1)
        self.assertEqual(Notification.objects.filter(code='guest_not_arrived').count(), 1)

    def test_the_guest_and_the_owner_are_told_without_personal_data(self):
        booking = self.make('10:00')
        cancel_unarrived_bookings(now=tashkent(self.check_in, 13, 0))
        guest_note = Notification.objects.get(code='booking_not_arrived')
        owner_note = Notification.objects.get(code='guest_not_arrived')
        self.assertEqual((guest_note.user_id, owner_note.user_id), (self.user.id, self.owner.id))
        for note in (guest_note, owner_note):
            self.assertEqual(note.booking_id, booking.id)
            self.assertNotIn('+998', note.message)
            self.assertNotIn(self.user.email, note.message)

    def test_one_failing_booking_does_not_stop_the_others(self):
        first = self.make('10:00')
        second = self.make('10:00')
        original = Booking.cancel_booking
        calls = []

        def flaky(self_, *args, **kwargs):
            calls.append(self_.pk)
            if self_.pk == first.pk:
                raise RuntimeError('boom')
            return original(self_, *args, **kwargs)

        Booking.cancel_booking = flaky
        try:
            result = cancel_unarrived_bookings(now=tashkent(self.check_in, 13, 0))
        finally:
            Booking.cancel_booking = original
        self.assertEqual((result['cancelled'], result['failed']), (1, 1))
        second.refresh_from_db()
        self.assertEqual(second.status, 'cancelled')

    def test_the_task_is_scheduled(self):
        self.assertIn('bookings.tasks.cancel_unarrived_bookings',
                      [entry['task'] for entry in settings.CELERY_BEAT_SCHEDULE.values()])


class PendingBookingsAtDeployTests(CashFixture):
    """Migration 0012: pending bookings still inside their payment window are confirmed; expired ones are left to the expiry task."""

    def test_only_bookings_inside_their_window_are_confirmed(self):
        from importlib import import_module

        from django.apps import apps
        from django.utils import timezone

        from bookings.tests.r12_helpers import make_booking

        step = import_module('bookings.migrations.0012_cash_arrival')
        start = date.today() + timedelta(days=20)
        inside = make_booking(self.property, self.user, start, status='pending')
        no_window = make_booking(self.property, self.user, start, status='pending')
        expired = make_booking(self.property, self.user, start, status='pending')
        done = make_booking(self.property, self.user, start, status='cancelled')
        now = timezone.now()
        Booking.objects.filter(pk=inside.pk).update(expires_at=now + timedelta(minutes=5))
        Booking.objects.filter(pk=expired.pk).update(expires_at=now - timedelta(minutes=5))

        step.confirm_pending_bookings(apps, None)

        statuses = {key: Booking.objects.get(pk=row.pk).status
                    for key, row in {'inside': inside, 'no_window': no_window, 'expired': expired, 'done': done}.items()}
        self.assertEqual(statuses, {'inside': 'confirmed', 'no_window': 'confirmed', 'expired': 'pending', 'done': 'cancelled'})
        self.assertIsNone(Booking.objects.get(pk=inside.pk).expires_at)

"""After a booking is made or cancelled the guest and the hotel owner are told: in the site's list and by e-mail."""
from unittest import mock

from django.core import mail

from accounts.models import Notification
from bookings.models import Booking
from bookings.tasks import send_booking_notice
from bookings.tests.test_cash_bookings import CashFixture


class BookingNoticeTests(CashFixture):
    def book_and_run_tasks(self):
        with mock.patch('bookings.tasks.send_booking_notice.apply_async',
                        side_effect=lambda args, retry, connection: send_booking_notice.run(*args)):
            with self.captureOnCommitCallbacks(execute=True):
                return self.book()

    def test_new_booking_tells_the_guest_and_the_owner_in_the_list(self):
        response = self.book_and_run_tasks()
        self.assertEqual(response.status_code, 201, response.data)
        booking = Booking.objects.get()
        guest_note = Notification.objects.get(user=self.user)
        owner_note = Notification.objects.get(user=self.owner)
        self.assertEqual((guest_note.code, owner_note.code), ('booking_confirmed', 'new_booking'))
        self.assertEqual(guest_note.params['booking_reference'], booking.confirmation_code)
        self.assertEqual(owner_note.booking_id, booking.id)

    def test_new_booking_mails_the_guest_and_the_owner_without_guest_details(self):
        self.book_and_run_tasks()
        recipients = sorted(address for message in mail.outbox for address in message.to)
        self.assertEqual(recipients, sorted([self.user.email, self.owner.email]))
        owner_mail = next(message for message in mail.outbox if self.owner.email in message.to)
        self.assertIn(Booking.objects.get().confirmation_code, owner_mail.body)
        self.assertNotIn(self.user.email, owner_mail.body)
        self.assertNotIn(self.user.get_full_name() or 'no name', owner_mail.body)

    def test_cancelling_tells_the_owner(self):
        self.book_and_run_tasks()
        mail.outbox.clear()
        booking = Booking.objects.get()
        with mock.patch('bookings.tasks.send_booking_notice.apply_async',
                        side_effect=lambda args, retry, connection: send_booking_notice.run(*args)):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(f'/api/v1/bookings/{booking.id}/cancel/', {}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(Notification.objects.filter(user=self.owner, code='booking_cancelled_by_guest').exists())
        self.assertEqual([message.to for message in mail.outbox], [[self.owner.email]])

    def test_a_broken_queue_does_not_fail_the_booking(self):
        with mock.patch('bookings.tasks.send_booking_notice.apply_async', side_effect=ConnectionError('no broker')):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.book()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Booking.objects.count(), 1)

    def test_a_dead_broker_answers_the_booking_at_once(self):
        import time

        started = time.monotonic()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.book()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertLess(time.monotonic() - started, 10)  # the default retries take 20 s or more

    def test_the_task_ignores_a_booking_that_is_gone(self):
        self.assertIsNone(send_booking_notice.run(999999, 'owner_new'))
        self.assertEqual(mail.outbox, [])

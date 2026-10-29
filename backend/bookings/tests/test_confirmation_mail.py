"""The guest's e-mail after a booking is a full confirmation: hotel, dates, room, arrival rule, the sum, how to pay."""
from decimal import Decimal
from unittest import mock

from django.conf import settings
from django.core import mail

from bookings.confirmation_mail import money
from bookings.models import Booking
from bookings.tasks import send_booking_notice
from bookings.tests.test_cash_bookings import CashFixture


class ConfirmationMailTests(CashFixture):
    def book_and_run_tasks(self, **extra):
        with mock.patch('bookings.tasks.send_booking_notice.apply_async',
                        side_effect=lambda args, retry, connection: send_booking_notice.run(*args)):
            with self.captureOnCommitCallbacks(execute=True):
                return self.book(**extra)

    def guest_mail(self, **extra):
        response = self.book_and_run_tasks(**extra)
        self.assertEqual(response.status_code, 201, response.data)
        return next(message for message in mail.outbox if self.user.email in message.to)

    def test_the_guest_gets_the_hotel_the_dates_the_room_and_the_sum(self):
        message = self.guest_mail(expected_arrival_time='10:30')
        booking = Booking.objects.get()
        body = message.body
        for expected in (
            booking.confirmation_code, self.property.display_name('en'), self.property.address_line1,
            self.check_in.isoformat(), self.check_out.isoformat(), self.room_type.name, '10:30',
            money(booking.charge_amount, booking.charge_currency),
        ):
            self.assertIn(expected, body)
        self.assertIn(f'{settings.FRONTEND_URL}/bookings', body)
        self.assertIn(booking.confirmation_code, message.subject)

    def test_the_text_comes_in_uzbek_russian_and_english(self):
        body = self.guest_mail().body
        for marker in ('Uz:', 'Ru:', 'En:', 'mehmonxonada', 'в отеле', 'at the hotel'):
            self.assertIn(marker, body)

    def test_it_says_how_long_the_hotel_waits_after_the_arrival_time(self):
        body = self.guest_mail().body
        self.assertIn(str(settings.ARRIVAL_GRACE_HOURS), body)
        self.assertIn('14:00', body)

    def test_it_carries_no_special_requests_and_no_phone(self):
        body = self.guest_mail(special_requests='Quiet room please', guest_phone='+998901234567').body
        self.assertNotIn('Quiet room please', body)
        self.assertNotIn('+998901234567', body)

    def test_an_old_booking_without_an_arrival_time_still_gets_the_mail(self):
        self.book_and_run_tasks()
        booking = Booking.objects.get()
        Booking.objects.filter(pk=booking.pk).update(expected_arrival_time=None)
        mail.outbox.clear()
        send_booking_notice.run(booking.pk, 'guest_confirmed')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(booking.confirmation_code, mail.outbox[0].body)
        self.assertNotIn('None', mail.outbox[0].body)

    def test_the_owner_mail_is_unchanged_short_and_without_guest_details_or_the_sum(self):
        self.book_and_run_tasks()
        owner_mail = next(message for message in mail.outbox if self.owner.email in message.to)
        booking = Booking.objects.get()
        self.assertIn(booking.confirmation_code, owner_mail.body)
        self.assertNotIn(self.user.email, owner_mail.body)
        self.assertNotIn(money(booking.charge_amount, booking.charge_currency), owner_mail.body)
        self.assertNotIn('Uz: ' + 'mehmonxonada', owner_mail.body)


class MoneyFormatTests(CashFixture):
    def test_so_m_has_no_decimals_and_spaces_between_thousands(self):
        self.assertEqual(money(Decimal('514350.00'), 'UZS'), '514 350 UZS')
        self.assertEqual(money(Decimal('1200000'), 'UZS'), '1 200 000 UZS')

    def test_other_currencies_keep_two_decimals(self):
        self.assertEqual(money(Decimal('60'), 'USD'), '60.00 USD')
        self.assertEqual(money(Decimal('1234.5'), 'USD'), '1 234.50 USD')

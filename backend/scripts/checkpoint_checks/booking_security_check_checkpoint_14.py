"""
Checkpoint 14 qáwipsizlik tekseriw skripti - Bronnıń múddeti pitiwi, biykar etiw hám inventory di tiklew

Bul skript bron múddeti pitiwin iske asırıwdı, sonıń ishinde anıq (deterministic) status
ótiwlerin hám inventory di tiklewdi tolıq qáwipsizlik tekseriwinen ótkeredi.
"""

import os
import sys
import django

# Django dı tayarlaw
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('ALLOWED_HOSTS', 'testserver,localhost,127.0.0.1')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from properties.models import Property, PropertyType, RoomType, RatePlan, DateInventory
from bookings.models import Booking

User = get_user_model()


class BookingExpirySecurityCheck(TestCase):
    """Bron múddeti pitiwi iske asırılıwı ushın qáwipsizlik tekseriwleri."""

    def setUp(self):
        """Qáwipsizlik tekseriwleri ushın test maǵlıwmatın tayarlaw."""
        self.user = User.objects.create_user(
            email='security@example.com',
            password='SecurePassword123!',
            first_name='Security',
            last_name='Test'
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='OtherPassword123!',
            first_name='Other',
            last_name='User'
        )

        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )

        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            status='active',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Test St',
            city='Test City',
            country='Test Country',
            base_price=Decimal('100.00'),
            currency='USD'
        )

        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('100.00'),
            currency='USD',
            total_rooms=5
        )

        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type,
            name='Standard Rate',
            slug='standard-rate',
            rate_type='standard',
            base_price=Decimal('100.00'),
            currency='USD',
            min_nights=1,
            max_nights=30,
            is_active=True
        )

        # Date inventory di jaratıw
        self.check_in = date.today() + timedelta(days=10)
        self.check_out = date.today() + timedelta(days=12)

        current_date = self.check_in
        while current_date < self.check_out:
            DateInventory.objects.create(
                rate_plan=self.rate_plan,
                date=current_date,
                available_rooms=5,
                booked_rooms=0,
                price=Decimal('100.00'),
                currency='USD',
                is_available=True
            )
            current_date += timedelta(days=1)

        self.client = Client()

    def test_01_expiry_field_is_properly_indexed(self):
        """Múddet maydanı ónimdarlıq ushın durıs indekslengenin testlew."""
        # Modelde múddet maydanı barlıǵın tekseriw
        from bookings.models import Booking as BookingModel
        booking = BookingModel(
            guest=self.user,
            property=self.property,
            status='pending',
            check_in=self.check_in,
            check_out=self.check_out,
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD'
        )
        self.assertTrue(hasattr(booking, 'expires_at'))

        # Maydan modelde db_index=True ekenin tekseriw
        field = BookingModel._meta.get_field('expires_at')
        self.assertTrue(field.db_index, "Expiry field should be indexed")

    def test_02_expiry_timestamp_auto_generated(self):
        """Kútip turǵan bronlar ushın múddet waqıtı avtomatik jaratılatuǵının testlew."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        self.assertIsNotNone(booking.expires_at)
        # Múddet jaratılǵannan shama menen 15 minut keyin ekenin tekseriw
        expected_expiry = booking.created_at + timedelta(minutes=15)
        time_difference = abs((booking.expires_at - expected_expiry).total_seconds())
        self.assertLess(time_difference, 5)  # 5 sekund parıqqa ruxsat

    def test_03_expiry_only_for_pending_bookings(self):
        """Múddet tek kútip turǵan bronlar ushın qoyılatuǵının testlew."""
        # Kútip turǵan bronnı jaratıw
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        self.assertEqual(booking.status, 'pending')
        self.assertIsNotNone(booking.expires_at)

        # Bronnı biykar etiw
        booking.cancel_booking('Test cancellation')

        # Confirmed status ına jańalaw (tólemdi uqsatıw)
        booking.status = 'confirmed'
        booking.save()

        # Tuwrıdan-tuwrı confirmed ǵa ótetuǵın taǵı bir bron jaratıw
        booking2 = Booking(
            guest=self.user,
            property=self.property,
            status='confirmed',
            payment_status='paid',
            check_in=self.check_in,
            check_out=self.check_out,
            number_of_nights=2,
            guest_count=2,
            total_price=Decimal('200.00'),
            currency='USD'
        )
        booking2.save()

        # Confirmed bronlarǵa múddet avtomatik jaratılmawı kerek
        self.assertIsNone(booking2.expires_at)

    def test_04_expiry_transaction_safety(self):
        """Múddet islemleri tranzakciya-qáwipsiz ekenin testlew."""
        from django.db import transaction

        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # Inventory diń dáslepki jaǵdayın alıw
        initial_inventory = list(DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date__gte=self.check_in,
            date__lt=self.check_out
        ))

        # Májbúriy qaytarıw menen múddetin pitkeriwge urınıw
        try:
            with transaction.atomic():
                booking.expire_booking()
                # Qaytarıwdı májbúrlew
                raise ValueError("Test rollback")
        except ValueError:
            pass

        # Qaytarıwdan keyin inventory ózgermey qalǵanın tekseriw
        final_inventory = list(DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date__gte=self.check_in,
            date__lt=self.check_out
        ))

        for initial, final in zip(initial_inventory, final_inventory):
            self.assertEqual(initial.booked_rooms, final.booked_rooms)

    def test_05_expiry_inventory_restoration_accuracy(self):
        """Múddet pitiwi inventory di anıq tiklewin testlew."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # Bronlawdan keyingi inventory di alıw
        booked_after_booking = DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date=self.check_in
        ).first().booked_rooms

        # Bronnıń múddetin pitkeriw
        booking.expire_booking()

        # Inventory tiklengenin tekseriw
        booked_after_expiry = DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date=self.check_in
        ).first().booked_rooms

        self.assertEqual(booked_after_expiry, booked_after_booking - 1)

    def test_06_expiry_status_validation(self):
        """Múddet pitiwi tek kútip turǵan bronlar ushın bolatuǵının testlew."""
        # Bronnı jaratıw hám tastıyıqlaw
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        booking.status = 'confirmed'
        booking.save()

        # Confirmed bronnıń múddetin pitkeriwge urınıw (sátsiz bolıwı kerek)
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as context:
            booking.expire_booking()

        self.assertIn('status', context.exception.message_dict)

    def test_07_expiry_cancellation_reason_integrity(self):
        """Múddet pitiwi durıs biykar etiw sebebin qoyatuǵının testlew."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        booking.expire_booking()

        self.assertEqual(booking.status, 'cancelled')
        self.assertEqual(booking.cancellation_reason, 'Booking expired - payment not completed within time limit')
        self.assertIsNotNone(booking.cancelled_at)

    def test_08_deterministic_state_transitions(self):
        """Status ótiwleri anıq (deterministic) hám jaqsı anıqlanǵanın testlew."""
        # pending -> cancelled (múddet pitiwi) di testlew
        booking1 = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        self.assertEqual(booking1.status, 'pending')
        booking1.expire_booking()
        self.assertEqual(booking1.status, 'cancelled')

        # pending -> cancelled (paydalanıwshı biykar etiwi) di testlew
        booking2 = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        self.assertEqual(booking2.status, 'pending')
        booking2.cancel_booking('User cancelled')
        self.assertEqual(booking2.status, 'cancelled')

        # Biykar etilgen bronnıń taǵı biykar etilmeytuǵının testlew
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            booking1.cancel_booking('Try again')

        with self.assertRaises(ValidationError):
            booking1.expire_booking()

    def test_09_process_expired_bookings_safety(self):
        """process_expired_bookings qátelerdi durıs islewin testlew."""
        # Bir neshe bronnı jaratıw
        booking1 = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # Ekinshi bron ushın inventory jaratıw
        check_in2 = date.today() + timedelta(days=20)
        check_out2 = date.today() + timedelta(days=22)

        current_date = check_in2
        while current_date < check_out2:
            DateInventory.objects.create(
                rate_plan=self.rate_plan,
                date=current_date,
                available_rooms=5,
                booked_rooms=0,
                price=Decimal('100.00'),
                currency='USD',
                is_available=True
            )
            current_date += timedelta(days=1)

        booking2 = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=check_in2,
            check_out=check_out2,
            guest_count=2
        )

        # Ekewin de múddeti pitken etip qoyıw
        past_time = timezone.now() - timedelta(minutes=30)
        booking1.expires_at = past_time
        booking1.save(update_fields=['expires_at'])

        booking2.expires_at = past_time
        booking2.save(update_fields=['expires_at'])

        # Múddeti pitken bronlardı islew
        processed_count = Booking.process_expired_bookings()

        self.assertEqual(processed_count, 2)

        # Ekewiniń de múddeti pitkenin tekseriw
        booking1.refresh_from_db()
        booking2.refresh_from_db()
        self.assertEqual(booking1.status, 'cancelled')
        self.assertEqual(booking2.status, 'cancelled')

    def test_10_expiry_field_not_exposed_to_manipulation(self):
        """Múddet maydanın API arqalı ózgertip bolmaytuǵının testlew."""
        # Paydalanıwshı retinde kiriw
        self.client.login(email='security@example.com', password='SecurePassword123!')

        # Bronnı jaratıw
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # Múddetti API arqalı jańalawǵa urınıw (ruxsat berilmewi kerek)
        data = {
            'expires_at': '2099-12-31T23:59:59Z'
        }

        response = self.client.put(f'/api/v1/bookings/{booking.id}/', data, content_type='application/json')
        # 405 Method Not Allowed yamasa 403/400 qaytarıwı kerek
        self.assertIn(response.status_code, [405, 403, 400])

    def test_11_concurrent_expiry_safety(self):
        """Bir waqıttaǵı múddet pitiriw islemleri status tekseriwi arqalı qáwipsiz ekenin testlew."""
        # Bronnı jaratıw
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # Birinshi múddet pitiriw tabıslı bolıwı kerek
        booking.expire_booking()
        self.assertEqual(booking.status, 'cancelled')

        # Ekinshi múddet pitiriw urınısı status tekseriwi sebepli sátsiz bolıwı kerek
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as context:
            booking.expire_booking()

        self.assertIn('status', context.exception.message_dict)

        # Bron biykar etilgen qalpında qalǵanın tekseriw
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')

    def test_12_management_command_authentication(self):
        """Management command durıs sazlawdı talap etetuǵının testlew."""
        from django.core.management import call_command
        from io import StringIO

        # Múddeti pitken bronnı jaratıw
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        past_time = timezone.now() - timedelta(minutes=30)
        booking.expires_at = past_time
        booking.save(update_fields=['expires_at'])

        # Command dı dry-run rejiminde islew (management command bolǵanı ushın auth siz islewi kerek)
        out = StringIO()
        call_command('process_expired_bookings', '--dry-run', stdout=out)

        output = out.getvalue()
        self.assertIn('Dry run mode', output)

    def test_13_inventory_restoration_for_multiple_nights(self):
        """Múddet pitiwi bir neshe tún ushın inventory di anıq tiklewin testlew."""
        # 3 tún ushın bron jaratıw
        check_in = date.today() + timedelta(days=30)
        check_out = date.today() + timedelta(days=33)

        current_date = check_in
        while current_date < check_out:
            DateInventory.objects.create(
                rate_plan=self.rate_plan,
                date=current_date,
                available_rooms=5,
                booked_rooms=0,
                price=Decimal('100.00'),
                currency='USD',
                is_available=True
            )
            current_date += timedelta(days=1)

        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=check_in,
            check_out=check_out,
            guest_count=2
        )

        # Inventory 3 tún ushın bronlanǵanın tekseriw
        inventory_records = DateInventory.objects.filter(
            rate_plan=self.rate_plan,
            date__gte=check_in,
            date__lt=check_out
        )
        self.assertEqual(inventory_records.count(), 3)

        for inventory in inventory_records:
            self.assertEqual(inventory.booked_rooms, 1)

        # Bronnıń múddetin pitkeriw
        booking.expire_booking()

        # Inventory barlıq 3 tún ushın tiklengenin tekseriw
        for inventory in inventory_records:
            inventory.refresh_from_db()
            self.assertEqual(inventory.booked_rooms, 0)

    def test_14_expiry_time_reasonable_default(self):
        """Múddet waqıtı maqul ádettegi mánisti (15 minut) paydalanatuǵının testlew."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        # Múddet maqul ekenin (júdá qısqa emes, júdá uzın emes) tekseriw
        time_until_expiry = (booking.expires_at - booking.created_at).total_seconds()
        self.assertGreater(time_until_expiry, 60)  # Keminde 1 minut
        self.assertLess(time_until_expiry, 3600)  # 1 saattan kem
        self.assertAlmostEqual(time_until_expiry, 900, delta=5)  # Shama menen 15 minut

    def test_15_booking_status_integrity_after_expiry(self):
        """Bron status ı hám baylanıslı maydanlar múddet pitkennen keyin putinligin saqlaytuǵının testlew."""
        booking = Booking.create_booking(
            guest=self.user,
            property_obj=self.property,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            check_in=self.check_in,
            check_out=self.check_out,
            guest_count=2
        )

        original_payment_status = booking.payment_status

        booking.expire_booking()

        # Status putinligin tekseriw
        self.assertEqual(booking.status, 'cancelled')
        self.assertEqual(booking.payment_status, original_payment_status)  # Tólem status ı ózgermegen
        self.assertIsNotNone(booking.cancelled_at)
        self.assertIsNotNone(booking.cancellation_reason)
        self.assertEqual(booking.guest, self.user)
        self.assertEqual(booking.property, self.property)


def run_security_checks():
    """Barlıq qáwipsizlik tekseriwlerin islew hám nátiyjelerdi bildiriw."""
    from django.test.runner import DiscoverRunner

    runner = DiscoverRunner(verbosity=2)
    test_suite = runner.test_loader.loadTestsFromTestCase(BookingExpirySecurityCheck)
    result = runner.run_suite(test_suite)

    print("\n" + "="*70)
    print("SECURITY REVIEW SUMMARY")
    print("="*70)
    print(f"Total tests: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    if result.wasSuccessful():
        print("✓ ALL SECURITY CHECKS PASSED")
        return 0
    else:
        print("✗ SECURITY CHECKS FAILED")
        return 1


if __name__ == '__main__':
    exit_code = run_security_checks()
    sys.exit(exit_code)

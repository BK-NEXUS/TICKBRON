"""
Tests for payment models.
"""
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from users.models import User
from properties.models import Property, PropertyType, RoomType, RatePlan, DateInventory
from bookings.models import Booking, BookingItem
from payments.models import PaymentTransaction, WebhookEvent, PaymentAuditLog


class PaymentTransactionModelTests(TestCase):
    """Tests for PaymentTransaction model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
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
            address_line1='123 Test Street',
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
            is_active=True
        )
        
        # Create date inventory
        check_in = timezone.now().date() + timedelta(days=7)
        check_out = check_in + timedelta(days=3)
        
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
        
        # Create booking
        self.booking = Booking.objects.create(
            guest=self.user,
            property=self.property,
            status='pending',
            payment_status='pending',
            check_in=check_in,
            check_out=check_out,
            number_of_nights=3,
            guest_count=2,
            total_price=Decimal('300.00'),
            currency='USD',
            confirmation_code='TEST12345'
        )
        
        BookingItem.objects.create(
            booking=self.booking,
            room_type=self.room_type,
            rate_plan=self.rate_plan,
            number_of_rooms=1,
            price_per_night=Decimal('100.00'),
            currency='USD'
        )
    
    def test_payment_transaction_creation(self):
        """Test creating a payment transaction."""
        transaction = PaymentTransaction.objects.create(
            idempotency_key='test_key_123',
            booking=self.booking,
            provider='payme',
            amount=Decimal('300.00'),
            currency='USD',
            client_ip='127.0.0.1',
            user_agent='Test Agent'
        )
        
        self.assertEqual(transaction.idempotency_key, 'test_key_123')
        self.assertEqual(transaction.booking, self.booking)
        self.assertEqual(transaction.provider, 'payme')
        self.assertEqual(transaction.amount, Decimal('300.00'))
        self.assertEqual(transaction.status, 'pending')
    
    def test_idempotency_key_unique(self):
        """Test that idempotency key is unique."""
        PaymentTransaction.objects.create(
            idempotency_key='test_key_123',
            booking=self.booking,
            provider='payme',
            amount=Decimal('300.00'),
            currency='USD'
        )
        
        # Attempt to create duplicate should fail
        with self.assertRaises(Exception):
            PaymentTransaction.objects.create(
                idempotency_key='test_key_123',
                booking=self.booking,
                provider='payme',
                amount=Decimal('300.00'),
                currency='USD'
            )
    
    def test_get_or_create_idempotent_new(self):
        """Test get_or_create_idempotent for new transaction."""
        transaction, created = PaymentTransaction.get_or_create_idempotent(
            idempotency_key='new_key_123',
            booking=self.booking,
            provider='payme',
            amount=Decimal('300.00'),
            currency='USD'
        )
        
        self.assertTrue(created)
        self.assertEqual(transaction.idempotency_key, 'new_key_123')
    
    def test_get_or_create_idempotent_existing(self):
        """Test get_or_create_idempotent for existing transaction."""
        # Create initial transaction
        PaymentTransaction.objects.create(
            idempotency_key='existing_key_123',
            booking=self.booking,
            provider='payme',
            amount=Decimal('300.00'),
            currency='USD'
        )
        
        # Attempt to create with same key should return existing
        transaction, created = PaymentTransaction.get_or_create_idempotent(
            idempotency_key='existing_key_123',
            booking=self.booking,
            provider='payme',
            amount=Decimal('300.00'),
            currency='USD'
        )
        
        self.assertFalse(created)
        self.assertEqual(transaction.idempotency_key, 'existing_key_123')
    
    def test_payment_transaction_validation_invalid_booking_status(self):
        """Test validation fails for non-pending booking."""
        self.booking.status = 'confirmed'
        self.booking.save()
        
        transaction = PaymentTransaction(
            idempotency_key='test_key_456',
            booking=self.booking,
            provider='payme',
            amount=Decimal('300.00'),
            currency='USD'
        )
        
        with self.assertRaises(Exception):
            transaction.full_clean()
    
    def test_payment_transaction_validation_amount_mismatch(self):
        """Test validation fails when amount doesn't match booking total."""
        transaction = PaymentTransaction(
            idempotency_key='test_key_789',
            booking=self.booking,
            provider='payme',
            amount=Decimal('200.00'),  # Wrong amount
            currency='USD'
        )
        
        with self.assertRaises(Exception):
            transaction.full_clean()


class WebhookEventModelTests(TestCase):
    """Tests for WebhookEvent model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
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
            address_line1='123 Test Street',
            city='Test City',
            country='Test Country',
            base_price=Decimal('100.00'),
            currency='USD'
        )
        
        self.booking = Booking.objects.create(
            guest=self.user,
            property=self.property,
            status='pending',
            payment_status='pending',
            check_in=timezone.now().date() + timedelta(days=7),
            check_out=timezone.now().date() + timedelta(days=10),
            number_of_nights=3,
            guest_count=2,
            total_price=Decimal('300.00'),
            currency='USD',
            confirmation_code='TEST12345'
        )
        
        self.payment_transaction = PaymentTransaction.objects.create(
            idempotency_key='test_key_123',
            booking=self.booking,
            provider='payme',
            amount=Decimal('300.00'),
            currency='USD'
        )
    
    def test_webhook_event_creation(self):
        """Test creating a webhook event."""
        webhook = WebhookEvent.objects.create(
            provider='payme',
            provider_event_id='event_123',
            payload={'test': 'data'},
            signature='test_signature'
        )
        
        self.assertEqual(webhook.provider, 'payme')
        self.assertEqual(webhook.provider_event_id, 'event_123')
        self.assertEqual(webhook.status, 'received')
    
    def test_webhook_event_replay_attack_detection(self):
        """Test replay attack detection."""
        # Create initial webhook
        webhook1 = WebhookEvent.objects.create(
            provider='payme',
            provider_event_id='event_123',
            payload={'test': 'data'},
            signature='test_signature'
        )
        
        # Test that the first webhook is not a replay attack
        self.assertFalse(webhook1.is_replay_attack())
        
        # Try to create another webhook with same event ID (should fail due to unique constraint)
        with self.assertRaises(Exception):
            WebhookEvent.objects.create(
                provider='payme',
                provider_event_id='event_123',
                payload={'test': 'data'},
                signature='test_signature'
            )
    
    def test_webhook_event_timestamp_validation(self):
        """Test timestamp validation."""
        webhook = WebhookEvent(
            provider='payme',
            provider_event_id='event_456',
            payload={'test': 'data'},
            signature='test_signature',
            timestamp=timezone.now()
        )
        
        self.assertTrue(webhook.is_timestamp_valid())
    
    def test_webhook_event_timestamp_too_old(self):
        """Test timestamp validation fails for old timestamp."""
        old_timestamp = timezone.now() - timedelta(minutes=10)
        webhook = WebhookEvent(
            provider='payme',
            provider_event_id='event_789',
            payload={'test': 'data'},
            signature='test_signature',
            timestamp=old_timestamp
        )
        
        self.assertFalse(webhook.is_timestamp_valid(max_age_seconds=300))
    
    def test_webhook_event_unique_constraint(self):
        """Test unique constraint on provider and provider_event_id."""
        WebhookEvent.objects.create(
            provider='payme',
            provider_event_id='event_123',
            payload={'test': 'data'},
            signature='test_signature'
        )
        
        # Attempt to create duplicate should fail
        with self.assertRaises(Exception):
            WebhookEvent.objects.create(
                provider='payme',
                provider_event_id='event_123',
                payload={'test': 'data'},
                signature='test_signature'
            )


class PaymentAuditLogModelTests(TestCase):
    """Tests for PaymentAuditLog model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
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
            address_line1='123 Test Street',
            city='Test City',
            country='Test Country',
            base_price=Decimal('100.00'),
            currency='USD'
        )
        
        self.booking = Booking.objects.create(
            guest=self.user,
            property=self.property,
            status='pending',
            payment_status='pending',
            check_in=timezone.now().date() + timedelta(days=7),
            check_out=timezone.now().date() + timedelta(days=10),
            number_of_nights=3,
            guest_count=2,
            total_price=Decimal('300.00'),
            currency='USD',
            confirmation_code='TEST12345'
        )
        
        self.payment_transaction = PaymentTransaction.objects.create(
            idempotency_key='test_key_123',
            booking=self.booking,
            provider='payme',
            amount=Decimal('300.00'),
            currency='USD'
        )
    
    def test_payment_audit_log_creation(self):
        """Test creating a payment audit log."""
        audit_log = PaymentAuditLog.objects.create(
            payment_transaction=self.payment_transaction,
            booking=self.booking,
            action='payment_initiated',
            old_status=None,
            new_status='pending',
            actor=self.user,
            ip_address='127.0.0.1'
        )
        
        self.assertEqual(audit_log.action, 'payment_initiated')
        self.assertEqual(audit_log.payment_transaction, self.payment_transaction)
        self.assertEqual(audit_log.booking, self.booking)
    
    def test_payment_audit_log_log_action(self):
        """Test log_action class method."""
        audit_log = PaymentAuditLog.log_action(
            action='payment_completed',
            payment_transaction=self.payment_transaction,
            booking=self.booking,
            old_status='pending',
            new_status='completed',
            actor=self.user,
            ip_address='127.0.0.1',
            details={'test': 'data'}
        )
        
        self.assertEqual(audit_log.action, 'payment_completed')
        self.assertEqual(audit_log.old_status, 'pending')
        self.assertEqual(audit_log.new_status, 'completed')
        self.assertEqual(audit_log.details, {'test': 'data'})
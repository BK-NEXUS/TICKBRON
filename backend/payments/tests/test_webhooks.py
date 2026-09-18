"""
Tests for webhook processing.
"""
from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from payments.webhooks import (
    WebhookProcessor,
    validate_webhook_request,
    get_webhook_processor,
    SignatureValidationError
)
from payments.models import WebhookEvent, PaymentTransaction, PaymentAuditLog
from payments.adapters import SignatureValidationError as AdapterSignatureValidationError
from decimal import Decimal
import json


class WebhookProcessorTests(TestCase):
    """Tests for WebhookProcessor."""
    
    def setUp(self):
        """Set up test data."""
        self.user = None
        self.property = None
        self.booking = None
        self.payment_transaction = None
    
    def test_webhook_processor_initialization(self):
        """Test webhook processor initialization."""
        processor = WebhookProcessor('payme')
        self.assertEqual(processor.provider, 'payme')
        self.assertIsNotNone(processor.adapter)
    
    def test_process_webhook_success(self):
        """Test successful webhook processing."""
        processor = WebhookProcessor('payme')
        payload = {
            'id': 'event_123',
            'transaction_id': 'txn_456',
            'status': 'completed',
            'amount': '30000',
            'currency': 'USD',
            'timestamp': int(timezone.now().timestamp())
        }
        
        # Generate signature
        signature = processor.adapter.generate_signature(payload, 'test_secret')
        
        with patch.object(processor.adapter, 'secret_key', 'test_secret'):
            webhook_event, is_new = processor.process_webhook(payload, signature)
            
            self.assertTrue(is_new)
            self.assertEqual(webhook_event.status, 'processed')
            self.assertTrue(webhook_event.signature_valid)
            self.assertTrue(webhook_event.timestamp_valid)
    
    def test_process_webhook_replay_attack(self):
        """Test replay attack detection."""
        payload = {
            'id': 'event_123',
            'transaction_id': 'txn_456',
            'status': 'completed',
            'timestamp': int(timezone.now().timestamp())
        }
        signature = 'test_signature'
        
        # Create initial webhook
        WebhookEvent.objects.create(
            provider='payme',
            provider_event_id='event_123',
            payload=payload,
            signature=signature,
            status='processed'
        )
        
        processor = WebhookProcessor('payme')
        
        with self.assertRaises(ValueError) as context:
            processor.process_webhook(payload, signature)
        
        self.assertIn('Replay attack', str(context.exception))
    
    def test_process_webhook_invalid_signature(self):
        """Test webhook processing with invalid signature."""
        payload = {
            'id': 'event_456',
            'timestamp': int(timezone.now().timestamp())
        }
        signature = 'invalid_signature'
        
        processor = WebhookProcessor('payme')
        
        with patch.object(processor.adapter, 'verify_webhook_signature', return_value=False):
            with self.assertRaises(AdapterSignatureValidationError):
                processor.process_webhook(payload, signature)
    
    def test_process_webhook_old_timestamp(self):
        """Test webhook processing with old timestamp."""
        payload = {
            'id': 'event_789',
            'timestamp': int((timezone.now() - timedelta(minutes=10)).timestamp())
        }
        signature = 'test_signature'
        
        processor = WebhookProcessor('payme')
        
        with patch.object(processor.adapter, 'verify_webhook_signature', return_value=True):
            with self.assertRaises(AdapterSignatureValidationError):
                processor.process_webhook(payload, signature)
    
    def test_extract_event_id(self):
        """Test event ID extraction from payload."""
        processor = WebhookProcessor('payme')
        
        # Test with 'id' field
        payload1 = {'id': 'event_123'}
        event_id1 = processor._extract_event_id(payload1)
        self.assertEqual(event_id1, 'event_123')
        
        # Test with 'payment_id' field
        payload2 = {'payment_id': 'payment_456'}
        event_id2 = processor._extract_event_id(payload2)
        self.assertEqual(event_id2, 'payment_456')
        
        # Test with fallback hash
        payload3 = {'data': 'test'}
        event_id3 = processor._extract_event_id(payload3)
        self.assertTrue(event_id3.startswith('unknown_'))
    
    def test_extract_timestamp(self):
        """Test timestamp extraction from payload."""
        processor = WebhookProcessor('payme')
        
        # Test with Unix timestamp
        payload1 = {'timestamp': int(timezone.now().timestamp())}
        timestamp1 = processor._extract_timestamp(payload1)
        self.assertIsNotNone(timestamp1)
        
        # Test with ISO format
        current_time = timezone.now()
        payload2 = {'created_at': current_time.isoformat()}
        timestamp2 = processor._extract_timestamp(payload2)
        self.assertIsNotNone(timestamp2)
        
        # Test with no timestamp
        payload3 = {'data': 'test'}
        timestamp3 = processor._extract_timestamp(payload3)
        self.assertIsNone(timestamp3)
    
    def test_link_to_payment_transaction(self):
        """Test linking webhook to payment transaction."""
        # Create test payment transaction
        from users.models import User
        from properties.models import Property, PropertyType
        from bookings.models import Booking
        
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )
        
        property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
        
        property_obj = Property.objects.create(
            owner=user,
            property_type=property_type,
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
        
        booking = Booking.objects.create(
            guest=user,
            property=property_obj,
            status='pending',
            payment_status='pending',
            check_in=timezone.now().date() + timedelta(days=7),
            check_out=timezone.now().date() + timedelta(days=10),
            number_of_nights=3,
            guest_count=2,
            total_price=Decimal('300.00'),
            currency='USD'
        )
        
        payment_transaction = PaymentTransaction.objects.create(
            idempotency_key='test_key_123',
            booking=booking,
            provider='payme',
            amount=Decimal('300.00'),
            currency='USD',
            provider_transaction_id='txn_456'
        )
        
        processor = WebhookProcessor('payme')
        
        processed_data = {
            'provider_transaction_id': 'txn_456',
            'status': 'completed'
        }
        
        linked_transaction = processor._link_to_payment_transaction(processed_data)
        
        self.assertEqual(linked_transaction, payment_transaction)
    
    def test_link_to_payment_transaction_not_found(self):
        """Test linking webhook when transaction not found."""
        processor = WebhookProcessor('payme')
        
        processed_data = {
            'provider_transaction_id': 'txn_999',
            'status': 'completed'
        }
        
        linked_transaction = processor._link_to_payment_transaction(processed_data)
        
        self.assertIsNone(linked_transaction)


class ValidateWebhookRequestTests(TestCase):
    """Tests for validate_webhook_request function."""
    
    def test_validate_webhook_request_valid(self):
        """Test valid webhook request validation."""
        # Create mock request
        request = MagicMock()
        request.content_type = 'application/json'
        request.body = json.dumps({'test': 'data'}).encode('utf-8')
        request.headers = {'X-Signature': 'test_signature'}
        
        payload, signature = validate_webhook_request(request)
        
        self.assertEqual(payload, {'test': 'data'})
        self.assertEqual(signature, 'test_signature')
    
    def test_validate_webhook_request_invalid_content_type(self):
        """Test webhook request validation with invalid content type."""
        request = MagicMock()
        request.content_type = 'text/plain'
        request.body = b'test data'
        request.headers = {'X-Signature': 'test_signature'}
        
        with self.assertRaises(ValueError) as context:
            validate_webhook_request(request)
        
        self.assertIn('Invalid content type', str(context.exception))
    
    def test_validate_webhook_request_invalid_json(self):
        """Test webhook request validation with invalid JSON."""
        request = MagicMock()
        request.content_type = 'application/json'
        request.body = b'invalid json'
        request.headers = {'X-Signature': 'test_signature'}
        
        with self.assertRaises(ValueError) as context:
            validate_webhook_request(request)
        
        self.assertIn('Invalid JSON', str(context.exception))
    
    def test_validate_webhook_request_missing_signature(self):
        """Test webhook request validation with missing signature."""
        request = MagicMock()
        request.content_type = 'application/json'
        request.body = json.dumps({'test': 'data'}).encode('utf-8')
        request.headers = {}
        
        with self.assertRaises(ValueError) as context:
            validate_webhook_request(request)
        
        self.assertIn('Missing signature', str(context.exception))


class GetWebhookProcessorTests(TestCase):
    """Tests for get_webhook_processor factory function."""
    
    def test_get_webhook_processor(self):
        """Test getting webhook processor."""
        processor = get_webhook_processor('payme')
        self.assertIsInstance(processor, WebhookProcessor)
        self.assertEqual(processor.provider, 'payme')
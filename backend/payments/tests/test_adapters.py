"""
Tests for payment adapters.
"""
from django.test import TestCase
from django.conf import settings
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from unittest.mock import patch, MagicMock
from payments.adapters import (
    BasePaymentAdapter, 
    PaymeAdapter, 
    ClickAdapter, 
    VisaAdapter,
    get_payment_adapter,
    PaymentAdapterError,
    SignatureValidationError
)
from users.models import User
from properties.models import Property, PropertyType
from bookings.models import Booking


class BasePaymentAdapterTests(TestCase):
    """Tests for BasePaymentAdapter."""
    
    def setUp(self):
        """Set up test data."""
        self.adapter = BasePaymentAdapter()
    
    def test_adapter_initialization(self):
        """Test adapter initialization."""
        self.assertIsNotNone(self.adapter)
        self.assertTrue(hasattr(self.adapter, 'test_mode'))
    
    def test_generate_signature(self):
        """Test signature generation."""
        data = {'key1': 'value1', 'key2': 'value2'}
        secret_key = 'test_secret'
        
        signature = self.adapter.generate_signature(data, secret_key)
        
        self.assertIsInstance(signature, str)
        self.assertEqual(len(signature), 64)  # SHA256 hex length
    
    def test_signature_deterministic(self):
        """Test signature generation is deterministic."""
        data = {'key1': 'value1', 'key2': 'value2'}
        secret_key = 'test_secret'
        
        signature1 = self.adapter.generate_signature(data, secret_key)
        signature2 = self.adapter.generate_signature(data, secret_key)
        
        self.assertEqual(signature1, signature2)
    
    def test_verify_signature_valid(self):
        """Test signature verification for valid signature."""
        data = {'key1': 'value1', 'key2': 'value2'}
        secret_key = 'test_secret'
        
        signature = self.adapter.generate_signature(data, secret_key)
        is_valid = self.adapter.verify_signature(data, signature, secret_key)
        
        self.assertTrue(is_valid)
    
    def test_verify_signature_invalid(self):
        """Test signature verification for invalid signature."""
        data = {'key1': 'value1', 'key2': 'value2'}
        secret_key = 'test_secret'
        
        is_valid = self.adapter.verify_signature(data, 'invalid_signature', secret_key)
        
        self.assertFalse(is_valid)
    
    def test_validate_timestamp_valid(self):
        """Test timestamp validation for valid timestamp."""
        timestamp = timezone.now()
        is_valid = self.adapter.validate_timestamp(timestamp)
        
        self.assertTrue(is_valid)
    
    def test_validate_timestamp_too_old(self):
        """Test timestamp validation for old timestamp."""
        timestamp = timezone.now() - timedelta(minutes=10)
        is_valid = self.adapter.validate_timestamp(timestamp, max_age_seconds=300)
        
        self.assertFalse(is_valid)
    
    def test_validate_timestamp_none(self):
        """Test timestamp validation for None timestamp."""
        is_valid = self.adapter.validate_timestamp(None)
        
        self.assertFalse(is_valid)
    
    def test_mock_initiate_payment(self):
        """Test mock payment initiation in test mode."""
        # Create mock booking
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
            currency='USD',
            confirmation_code='TEST12345'
        )
        
        response = self.adapter.initiate_payment(
            booking=booking,
            amount=Decimal('300.00'),
            currency='USD'
        )
        
        self.assertTrue(response['success'])
        self.assertIn('provider_transaction_id', response)
        self.assertEqual(response['status'], 'pending')


class PaymeAdapterTests(TestCase):
    """Tests for PaymeAdapter."""
    
    def setUp(self):
        """Set up test data."""
        self.adapter = PaymeAdapter()
    
    def test_adapter_initialization(self):
        """Test Payme adapter initialization."""
        self.assertEqual(self.adapter.provider_name, 'payme')
        self.assertIsNotNone(self.adapter.test_mode)
    
    def test_verify_webhook_signature(self):
        """Test Payme webhook signature verification."""
        payload = {'key1': 'value1', 'key2': 'value2'}
        signature = self.adapter.generate_signature(payload, 'test_secret')
        
        # Mock secret key
        with patch.object(self.adapter, 'secret_key', 'test_secret'):
            is_valid = self.adapter.verify_webhook_signature(payload, signature)
            self.assertTrue(is_valid)
    
    def test_verify_webhook_signature_invalid(self):
        """Test Payme webhook signature verification with invalid signature."""
        payload = {'key1': 'value1', 'key2': 'value2'}
        
        with patch.object(self.adapter, 'secret_key', 'test_secret'):
            is_valid = self.adapter.verify_webhook_signature(payload, 'invalid_signature')
            self.assertFalse(is_valid)
    
    def test_process_webhook(self):
        """Test Payme webhook processing."""
        payload = {
            'id': 'event_123',
            'transaction_id': 'txn_456',
            'status': 'completed',
            'amount': '30000',  # Payme uses smallest currency unit
            'currency': 'USD',
            'timestamp': int(timezone.now().timestamp())
        }
        signature = self.adapter.generate_signature(payload, 'test_secret')
        
        with patch.object(self.adapter, 'secret_key', 'test_secret'):
            processed_data = self.adapter.process_webhook(payload, signature)
            
            self.assertEqual(processed_data['provider_event_id'], 'event_123')
            self.assertEqual(processed_data['provider_transaction_id'], 'txn_456')
            self.assertEqual(processed_data['status'], 'completed')
    
    def test_process_webhook_invalid_signature(self):
        """Test Payme webhook processing with invalid signature."""
        payload = {'id': 'event_123', 'timestamp': int(timezone.now().timestamp())}
        
        with patch.object(self.adapter, 'secret_key', 'test_secret'):
            with self.assertRaises(SignatureValidationError):
                self.adapter.process_webhook(payload, 'invalid_signature')


class ClickAdapterTests(TestCase):
    """Tests for ClickAdapter."""
    
    def setUp(self):
        """Set up test data."""
        self.adapter = ClickAdapter()
    
    def test_adapter_initialization(self):
        """Test Click adapter initialization."""
        self.assertEqual(self.adapter.provider_name, 'click')
        self.assertIsNotNone(self.adapter.test_mode)
    
    def test_generate_click_signature(self):
        """Test Click-specific signature generation."""
        data = {'key1': 'value1', 'key2': 'value2'}
        secret_key = 'test_secret'
        
        signature = self.adapter._generate_click_signature(data, secret_key)
        
        self.assertIsInstance(signature, str)
        self.assertEqual(len(signature), 32)  # MD5 hex length
    
    def test_verify_webhook_signature(self):
        """Test Click webhook signature verification."""
        payload = {'key1': 'value1', 'key2': 'value2'}
        signature = self.adapter._generate_click_signature(payload, 'test_secret')
        
        with patch.object(self.adapter, 'secret_key', 'test_secret'):
            is_valid = self.adapter.verify_webhook_signature(payload, signature)
            self.assertTrue(is_valid)
    
    def test_verify_webhook_signature_invalid(self):
        """Test Click webhook signature verification with invalid signature."""
        payload = {'key1': 'value1', 'key2': 'value2'}
        
        with patch.object(self.adapter, 'secret_key', 'test_secret'):
            is_valid = self.adapter.verify_webhook_signature(payload, 'invalid_signature')
            self.assertFalse(is_valid)
    
    def test_process_webhook(self):
        """Test Click webhook processing."""
        payload = {
            'payment_id': 'payment_123',
            'transaction_id': 'txn_456',
            'status': 'completed',
            'amount': '300.00',
            'currency': 'USD',
            'timestamp': int(timezone.now().timestamp())
        }
        signature = self.adapter._generate_click_signature(payload, 'test_secret')
        
        with patch.object(self.adapter, 'secret_key', 'test_secret'):
            processed_data = self.adapter.process_webhook(payload, signature)
            
            self.assertEqual(processed_data['provider_event_id'], 'payment_123')
            self.assertEqual(processed_data['provider_transaction_id'], 'txn_456')
            self.assertEqual(processed_data['status'], 'completed')
    
    def test_process_webhook_invalid_signature(self):
        """Test Click webhook processing with invalid signature."""
        payload = {'payment_id': 'payment_123', 'timestamp': int(timezone.now().timestamp())}
        
        with patch.object(self.adapter, 'secret_key', 'test_secret'):
            with self.assertRaises(SignatureValidationError):
                self.adapter.process_webhook(payload, 'invalid_signature')


class VisaAdapterTests(TestCase):
    """Tests for VisaAdapter."""
    
    def setUp(self):
        """Set up test data."""
        self.adapter = VisaAdapter()
    
    def test_adapter_initialization(self):
        """Test Visa adapter initialization."""
        self.assertEqual(self.adapter.provider_name, 'visa')
        self.assertIsNotNone(self.adapter.test_mode)
    
    def test_initiate_payment_not_implemented(self):
        """Test Visa initiate payment raises NotImplementedError when not in test mode."""
        # Create a mock booking object
        mock_booking = MagicMock()
        mock_booking.id = 1
        
        # Disable test mode for this test
        with patch.object(self.adapter, 'test_mode', False):
            with self.assertRaises(NotImplementedError):
                self.adapter.initiate_payment(mock_booking, Decimal('100.00'), 'USD')
    
    def test_verify_webhook_signature_not_implemented(self):
        """Test Visa webhook signature verification raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.adapter.verify_webhook_signature({}, 'signature')
    
    def test_process_webhook_not_implemented(self):
        """Test Visa webhook processing raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.adapter.process_webhook({}, 'signature')


class GetPaymentAdapterTests(TestCase):
    """Tests for get_payment_adapter factory function."""
    
    def test_get_payme_adapter(self):
        """Test getting Payme adapter."""
        adapter = get_payment_adapter('payme')
        self.assertIsInstance(adapter, PaymeAdapter)
    
    def test_get_click_adapter(self):
        """Test getting Click adapter."""
        adapter = get_payment_adapter('click')
        self.assertIsInstance(adapter, ClickAdapter)
    
    def test_get_visa_adapter(self):
        """Test getting Visa adapter."""
        adapter = get_payment_adapter('visa')
        self.assertIsInstance(adapter, VisaAdapter)
    
    def test_get_adapter_case_insensitive(self):
        """Test adapter lookup is case-insensitive."""
        adapter1 = get_payment_adapter('PAYME')
        adapter2 = get_payment_adapter('payme')
        self.assertIsInstance(adapter1, PaymeAdapter)
        self.assertIsInstance(adapter2, PaymeAdapter)
    
    def test_get_adapter_invalid_provider(self):
        """Test getting adapter for invalid provider raises ValueError."""
        with self.assertRaises(ValueError):
            get_payment_adapter('invalid_provider')
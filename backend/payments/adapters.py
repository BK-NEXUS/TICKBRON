"""
Payment adapters for TICKBRON.

This module contains adapter implementations for different payment providers
with signature validation, secure communication, and test mode support.
"""
import hmac
import hashlib
import json
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PaymentAdapterError(Exception):
    """Base exception for payment adapter errors."""
    pass


class SignatureValidationError(PaymentAdapterError):
    """Exception raised when signature validation fails."""
    pass


class PaymentTestModeError(PaymentAdapterError):
    """Exception raised when test mode is enabled but should not be."""
    pass


class BasePaymentAdapter:
    """
    Base class for payment provider adapters.
    
    Provides common functionality for signature validation, test mode switching,
    and secure communication with payment providers.
    """
    
    def __init__(self):
        self.test_mode = getattr(settings, 'PAYMENT_TEST_MODE', True)
        self.provider_name = self.__class__.__name__.replace('Adapter', '').lower()
    
    def _is_test_mode(self) -> bool:
        """Check if payment test mode is enabled."""
        return self.test_mode
    
    def _log_test_mode_call(self, method_name: str, **kwargs):
        """Log a call that's being routed through test mode."""
        logger.info(
            f"[PAYMENT_TEST_MODE] {self.provider_name}.{method_name} called. "
            f"Parameters: {kwargs}"
        )
    
    def generate_signature(self, data: Dict[str, any], secret_key: str) -> str:
        """
        Generate HMAC signature for payment provider communication.
        
        Args:
            data: Dictionary of data to sign
            secret_key: Secret key for signature generation
        
        Returns:
            str: Hexadecimal signature
        """
        # Sort keys for deterministic signature generation
        sorted_data = dict(sorted(data.items()))
        
        # Convert to JSON string without spaces
        data_string = json.dumps(sorted_data, separators=(',', ':'), default=str)
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            secret_key.encode('utf-8'),
            data_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_signature(self, data: Dict[str, any], signature: str, secret_key: str) -> bool:
        """
        Verify HMAC signature from payment provider.
        
        Args:
            data: Dictionary of data that was signed
            signature: Signature to verify
            secret_key: Secret key for signature verification
        
        Returns:
            bool: True if signature is valid
        """
        try:
            expected_signature = self.generate_signature(data, secret_key)
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False
    
    def validate_timestamp(self, timestamp: datetime, max_age_seconds: int = 300) -> bool:
        """
        Validate webhook timestamp to prevent replay attacks.
        
        Args:
            timestamp: Timestamp from webhook
            max_age_seconds: Maximum age of timestamp in seconds (default: 5 minutes)
        
        Returns:
            bool: True if timestamp is valid
        """
        if not timestamp:
            return False
        
        # Convert to timezone-aware if needed
        if timestamp.tzinfo is None:
            timestamp = timezone.make_aware(timestamp)
        
        time_diff = timezone.now() - timestamp
        return abs(time_diff.total_seconds()) <= max_age_seconds
    
    def initiate_payment(self, booking, amount: Decimal, currency: str, 
                       payment_method_token: Optional[str] = None, 
                       **kwargs) -> Dict[str, any]:
        """
        Initiate a payment with the provider.
        
        Args:
            booking: Booking object
            amount: Payment amount
            currency: Currency code
            payment_method_token: Tokenized payment method (optional)
            **kwargs: Additional provider-specific parameters
        
        Returns:
            dict: Provider response with transaction details
        
        Raises:
            PaymentAdapterError: If payment initiation fails
        """
        if self._is_test_mode():
            self._log_test_mode_call('initiate_payment', booking_id=booking.id, 
                                    amount=str(amount), currency=currency)
            return self._mock_initiate_payment(booking, amount, currency, 
                                              payment_method_token, **kwargs)
        
        raise NotImplementedError("Subclasses must implement initiate_payment")
    
    def confirm_payment(self, provider_transaction_id: str, **kwargs) -> Dict[str, any]:
        """
        Confirm a payment with the provider.
        
        Args:
            provider_transaction_id: Transaction ID from provider
            **kwargs: Additional provider-specific parameters
        
        Returns:
            dict: Provider response with confirmation details
        
        Raises:
            PaymentAdapterError: If payment confirmation fails
        """
        if self._is_test_mode():
            self._log_test_mode_call('confirm_payment', 
                                    provider_transaction_id=provider_transaction_id)
            return self._mock_confirm_payment(provider_transaction_id, **kwargs)
        
        raise NotImplementedError("Subclasses must implement confirm_payment")
    
    def refund_payment(self, provider_transaction_id: str, amount: Optional[Decimal] = None,
                      **kwargs) -> Dict[str, any]:
        """
        Refund a payment with the provider.
        
        Args:
            provider_transaction_id: Transaction ID from provider
            amount: Amount to refund (None for full refund)
            **kwargs: Additional provider-specific parameters
        
        Returns:
            dict: Provider response with refund details
        
        Raises:
            PaymentAdapterError: If refund fails
        """
        if self._is_test_mode():
            self._log_test_mode_call('refund_payment', 
                                    provider_transaction_id=provider_transaction_id,
                                    amount=str(amount) if amount else 'full')
            return self._mock_refund_payment(provider_transaction_id, amount, **kwargs)
        
        raise NotImplementedError("Subclasses must implement refund_payment")
    
    def _mock_initiate_payment(self, booking, amount: Decimal, currency: str,
                              payment_method_token: Optional[str], 
                              **kwargs) -> Dict[str, any]:
        """Mock payment initiation for test mode."""
        import secrets
        return {
            'success': True,
            'provider_transaction_id': f"test_txn_{secrets.token_hex(16)}",
            'status': 'pending',
            'amount': str(amount),
            'currency': currency,
            'message': 'Test mode: Payment initiated successfully'
        }
    
    def _mock_confirm_payment(self, provider_transaction_id: str, 
                              **kwargs) -> Dict[str, any]:
        """Mock payment confirmation for test mode."""
        return {
            'success': True,
            'provider_transaction_id': provider_transaction_id,
            'status': 'completed',
            'message': 'Test mode: Payment confirmed successfully'
        }
    
    def _mock_refund_payment(self, provider_transaction_id: str, 
                            amount: Optional[Decimal], **kwargs) -> Dict[str, any]:
        """Mock payment refund for test mode."""
        return {
            'success': True,
            'provider_transaction_id': provider_transaction_id,
            'status': 'refunded',
            'amount': str(amount) if amount else 'full',
            'message': 'Test mode: Payment refunded successfully'
        }


class PaymeAdapter(BasePaymentAdapter):
    """
    Payme payment provider adapter.
    
    Implements Payme-specific signature validation and API communication.
    """
    
    def __init__(self):
        super().__init__()
        self.merchant_id = getattr(settings, 'PAYME_MERCHANT_ID', '')
        self.secret_key = getattr(settings, 'PAYME_SECRET_KEY', '')
    
    def initiate_payment(self, booking, amount: Decimal, currency: str,
                       payment_method_token: Optional[str] = None,
                       **kwargs) -> Dict[str, any]:
        """
        Initiate payment with Payme.
        
        Payme uses a specific API format with merchant ID and signature.
        """
        if self._is_test_mode():
            return super().initiate_payment(booking, amount, currency, 
                                          payment_method_token, **kwargs)
        
        # Prepare Payme-specific request
        request_data = {
            'merchant_id': self.merchant_id,
            'amount': int(amount * 100),  # Payme uses smallest currency unit
            'currency': currency,
            'booking_id': booking.id,
            'description': f"Booking {booking.confirmation_code}",
            'timestamp': int(timezone.now().timestamp()),
        }
        
        if payment_method_token:
            request_data['payment_method_token'] = payment_method_token
        
        # Generate signature
        signature = self.generate_signature(request_data, self.secret_key)
        request_data['signature'] = signature
        
        # In production, make actual API call to Payme
        # response = self._call_payme_api('create', request_data)
        # return response
        
        raise NotImplementedError("Production Payme API integration pending")
    
    def verify_webhook_signature(self, payload: Dict[str, any], 
                                signature: str) -> bool:
        """
        Verify Payme webhook signature.
        
        Payme webhooks include a signature that must be verified.
        """
        if not self.secret_key:
            logger.error("Payme secret key not configured")
            return False
        
        return self.verify_signature(payload, signature, self.secret_key)
    
    def process_webhook(self, payload: Dict[str, any], signature: str) -> Dict[str, any]:
        """
        Process Payme webhook.
        
        Args:
            payload: Webhook payload from Payme
            signature: Signature from Payme
        
        Returns:
            dict: Processed webhook data
        
        Raises:
            SignatureValidationError: If signature is invalid
        """
        # Verify signature
        if not self.verify_webhook_signature(payload, signature):
            raise SignatureValidationError("Invalid Payme webhook signature")
        
        # Validate timestamp if present
        if 'timestamp' in payload:
            timestamp = datetime.fromtimestamp(payload['timestamp'], tz=dt_timezone.utc)
            if not self.validate_timestamp(timestamp):
                raise SignatureValidationError("Webhook timestamp too old")
        
        # Extract relevant information
        processed_data = {
            'provider_event_id': payload.get('id'),
            'provider_transaction_id': payload.get('transaction_id'),
            'status': payload.get('status'),
            'amount': payload.get('amount'),
            'currency': payload.get('currency'),
            'timestamp': timestamp if 'timestamp' in payload else None,
        }
        
        return processed_data


class ClickAdapter(BasePaymentAdapter):
    """
    Click payment provider adapter.
    
    Implements Click-specific signature validation and API communication.
    """
    
    def __init__(self):
        super().__init__()
        self.service_id = getattr(settings, 'CLICK_SERVICE_ID', '')
        self.secret_key = getattr(settings, 'CLICK_SECRET_KEY', '')
        self.merchant_id = getattr(settings, 'CLICK_MERCHANT_ID', '')
    
    def initiate_payment(self, booking, amount: Decimal, currency: str,
                       payment_method_token: Optional[str] = None,
                       **kwargs) -> Dict[str, any]:
        """
        Initiate payment with Click.
        
        Click uses a different API format with service ID and merchant ID.
        """
        if self._is_test_mode():
            return super().initiate_payment(booking, amount, currency,
                                          payment_method_token, **kwargs)
        
        # Prepare Click-specific request
        request_data = {
            'service_id': self.service_id,
            'merchant_id': self.merchant_id,
            'amount': float(amount),
            'currency': currency,
            'booking_id': booking.id,
            'description': f"Booking {booking.confirmation_code}",
            'timestamp': int(timezone.now().timestamp()),
        }
        
        if payment_method_token:
            request_data['card_token'] = payment_method_token
        
        # Generate signature (Click uses MD5)
        signature = self._generate_click_signature(request_data, self.secret_key)
        request_data['sign'] = signature
        
        # In production, make actual API call to Click
        # response = self._call_click_api('create', request_data)
        # return response
        
        raise NotImplementedError("Production Click API integration pending")
    
    def _generate_click_signature(self, data: Dict[str, any], secret_key: str) -> str:
        """
        Generate Click-specific MD5 signature.
        
        Click uses a different signature algorithm than Payme.
        """
        # Click signature format: MD5(sorted_key1_value1|sorted_key2_value2|...|secret)
        sorted_items = sorted(data.items())
        signature_string = '|'.join([f"{k}={v}" for k, v in sorted_items])
        signature_string += f"|{secret_key}"
        
        return hashlib.md5(signature_string.encode('utf-8')).hexdigest()
    
    def verify_webhook_signature(self, payload: Dict[str, any], 
                                signature: str) -> bool:
        """
        Verify Click webhook signature.
        
        Click webhooks use MD5 signature.
        """
        if not self.secret_key:
            logger.error("Click secret key not configured")
            return False
        
        try:
            expected_signature = self._generate_click_signature(payload, self.secret_key)
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Click signature verification error: {e}")
            return False
    
    def process_webhook(self, payload: Dict[str, any], signature: str) -> Dict[str, any]:
        """
        Process Click webhook.
        
        Args:
            payload: Webhook payload from Click
            signature: Signature from Click
        
        Returns:
            dict: Processed webhook data
        
        Raises:
            SignatureValidationError: If signature is invalid
        """
        # Verify signature
        if not self.verify_webhook_signature(payload, signature):
            raise SignatureValidationError("Invalid Click webhook signature")
        
        # Validate timestamp if present
        if 'timestamp' in payload:
            timestamp = datetime.fromtimestamp(payload['timestamp'], tz=dt_timezone.utc)
            if not self.validate_timestamp(timestamp):
                raise SignatureValidationError("Webhook timestamp too old")
        
        # Extract relevant information
        processed_data = {
            'provider_event_id': payload.get('payment_id'),
            'provider_transaction_id': payload.get('transaction_id'),
            'status': payload.get('status'),
            'amount': payload.get('amount'),
            'currency': payload.get('currency'),
            'timestamp': timestamp if 'timestamp' in payload else None,
        }
        
        return processed_data


class VisaAdapter(BasePaymentAdapter):
    """
    Visa payment provider adapter (placeholder for future implementation).
    
    This adapter is a placeholder for future Visa integration.
    """
    
    def __init__(self):
        super().__init__()
        self.api_key = getattr(settings, 'VISA_API_KEY', '')
        self.secret_key = getattr(settings, 'VISA_SECRET_KEY', '')
    
    def initiate_payment(self, booking, amount: Decimal, currency: str,
                       payment_method_token: Optional[str] = None,
                       **kwargs) -> Dict[str, any]:
        """
        Placeholder for Visa payment initiation.
        """
        if self._is_test_mode():
            return super().initiate_payment(booking, amount, currency,
                                          payment_method_token, **kwargs)
        
        raise NotImplementedError("Visa adapter not yet implemented")
    
    def verify_webhook_signature(self, payload: Dict[str, any], 
                                signature: str) -> bool:
        """Placeholder for Visa webhook signature verification."""
        raise NotImplementedError("Visa adapter not yet implemented")
    
    def process_webhook(self, payload: Dict[str, any], signature: str) -> Dict[str, any]:
        """Placeholder for Visa webhook processing."""
        raise NotImplementedError("Visa adapter not yet implemented")


def get_payment_adapter(provider: str) -> BasePaymentAdapter:
    """
    Factory function to get the appropriate payment adapter.
    
    Args:
        provider: Payment provider name ('payme', 'click', 'visa')
    
    Returns:
        BasePaymentAdapter: Appropriate adapter instance
    
    Raises:
        ValueError: If provider is not supported
    """
    adapters = {
        'payme': PaymeAdapter,
        'click': ClickAdapter,
        'visa': VisaAdapter,
    }
    
    adapter_class = adapters.get(provider.lower())
    if not adapter_class:
        raise ValueError(f"Unsupported payment provider: {provider}")
    
    return adapter_class()
"""
Tests for OTP authentication functionality.
"""
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from users.models import User
from users.services import OTPService

User = get_user_model()


class TestOTPService(TestCase):
    """Test cases for OTPService."""
    
    def setUp(self):
        """Set up test data."""
        self.otp_service = OTPService()
        self.phone_number = '+1234567890'
    
    def test_send_otp_existing_user(self):
        """Test that sending OTP for existing user works."""
        # Create user first
        User.objects.create_user(
            email='test@example.com',
            phone_number=self.phone_number,
            full_name='Test User',
            password='testpass123'
        )
        
        result = self.otp_service.send_otp(self.phone_number)
        
        assert result['success'] is True
        assert 'otp_code' in result
        assert User.objects.filter(phone_number=self.phone_number).count() == 1
    
    def test_send_otp_user_not_found(self):
        """Unknown numbers get the generic response and no code (no enumeration)."""
        result = self.otp_service.send_otp(self.phone_number)
        
        assert result['success'] is True
        assert 'otp_code' not in result
        assert 'not found' not in result['message'].lower()
    
    def test_verify_otp_success(self):
        """Test successful OTP verification."""
        # Create user and generate OTP
        user = User.objects.create_user(
            email='test@example.com',
            phone_number=self.phone_number,
            full_name='Test User',
            password='testpass123'
        )
        otp_code = user.generate_otp()
        
        result = self.otp_service.verify_otp(self.phone_number, otp_code)
        
        assert result['success'] is True
        assert result['user_id'] == user.id
        user.refresh_from_db()
        assert user.phone_verified is True
    
    def test_verify_otp_invalid_code(self):
        """Test OTP verification with invalid code."""
        # Create user and generate OTP
        user = User.objects.create_user(
            email='test@example.com',
            phone_number=self.phone_number,
            full_name='Test User',
            password='testpass123'
        )
        user.generate_otp()
        
        result = self.otp_service.verify_otp(self.phone_number, '000000')

        assert result['success'] is False
        assert 'Invalid or expired OTP code' in result['message']

    def test_send_otp_internal_error_does_not_leak_details(self):
        """An unexpected internal error must not surface str(e) to the caller (audit #24)."""
        from unittest.mock import patch

        User.objects.create_user(
            email='test@example.com',
            phone_number=self.phone_number,
            full_name='Test User',
            password='testpass123'
        )
        secret = 'psycopg2.OperationalError: connection to server failed on internal-db-host'

        with patch('users.models.User.generate_otp', side_effect=Exception(secret)):
            result = self.otp_service.send_otp(self.phone_number)

        assert result['success'] is False
        assert secret not in result['message']

    def test_verify_otp_internal_error_does_not_leak_details(self):
        """An unexpected internal error must not surface str(e) to the caller (audit #24)."""
        from unittest.mock import patch

        user = User.objects.create_user(
            email='test@example.com',
            phone_number=self.phone_number,
            full_name='Test User',
            password='testpass123'
        )
        otp_code = user.generate_otp()
        secret = 'psycopg2.OperationalError: connection to server failed on internal-db-host'

        with patch('users.models.User.verify_otp', side_effect=Exception(secret)):
            result = self.otp_service.verify_otp(self.phone_number, otp_code)

        assert result['success'] is False
        assert secret not in result['message']
    
    def test_verify_otp_expired(self):
        """Test OTP verification with expired code."""
        # Create user and generate OTP
        user = User.objects.create_user(
            email='test@example.com',
            phone_number=self.phone_number,
            full_name='Test User',
            password='testpass123'
        )
        otp_code = user.generate_otp()
        
        # Manually expire the OTP
        from django.utils import timezone
        from datetime import timedelta
        user.otp_expires_at = timezone.now() - timedelta(minutes=10)
        user.save()
        
        result = self.otp_service.verify_otp(self.phone_number, otp_code)
        
        assert result['success'] is False
    
    def test_verify_otp_max_attempts(self):
        """Test OTP verification with max attempts exceeded."""
        # Create user and generate OTP
        user = User.objects.create_user(
            email='test@example.com',
            phone_number=self.phone_number,
            full_name='Test User',
            password='testpass123'
        )
        otp_code = user.generate_otp()
        
        # Use all attempts
        for _ in range(3):
            self.otp_service.verify_otp(self.phone_number, '000000')
        
        result = self.otp_service.verify_otp(self.phone_number, otp_code)
        
        assert result['success'] is False


class TestOTPViews(TestCase):
    """Test cases for OTP view endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.phone_number = '+1234567890'
    
    def test_request_otp_endpoint(self):
        """Test request OTP endpoint."""
        # Register user first
        self.client.post('/api/v1/auth/register/', {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'phone_number': self.phone_number,
            'password': 'SecureP@ssw0rd123',
            'password_confirm': 'SecureP@ssw0rd123'
        })
        
        response = self.client.post('/api/v1/auth/otp/request/', {
            'phone_number': self.phone_number
        })
        
        assert response.status_code == 200
        assert response.data['success'] is True
        assert 'otp_code' in response.data  # Available in test mode
    
    def test_request_otp_missing_phone_number(self):
        """Test request OTP with missing phone number."""
        response = self.client.post('/api/v1/auth/otp/request/', {})
        
        assert response.status_code == 400
        assert 'phone_number' in response.data
    
    def test_verify_otp_endpoint(self):
        """Test verify OTP endpoint."""
        # Register user first
        self.client.post('/api/v1/auth/register/', {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'phone_number': self.phone_number,
            'password': 'SecureP@ssw0rd123',
            'password_confirm': 'SecureP@ssw0rd123'
        })
        
        # Request OTP
        request_response = self.client.post('/api/v1/auth/otp/request/', {
            'phone_number': self.phone_number
        })
        otp_code = request_response.data['otp_code']
        
        # Verify OTP
        verify_response = self.client.post('/api/v1/auth/otp/verify/', {
            'phone_number': self.phone_number,
            'otp_code': otp_code
        })
        
        assert verify_response.status_code == 200
        assert verify_response.data['email'] is not None
        assert verify_response.data['phone_number'] == self.phone_number
    
    def test_verify_otp_invalid_code(self):
        """Test verify OTP with invalid code."""
        # Create user first
        User.objects.create_user(
            email='test@example.com',
            phone_number=self.phone_number,
            full_name='Test User',
            password='testpass123'
        )
        
        response = self.client.post('/api/v1/auth/otp/verify/', {
            'phone_number': self.phone_number,
            'otp_code': '000000'
        })
        
        assert response.status_code == 400
        assert response.data['success'] is False
    
    def test_verify_otp_missing_fields(self):
        """Test verify OTP with missing fields."""
        response = self.client.post('/api/v1/auth/otp/verify/', {
            'phone_number': self.phone_number
        })
        
        assert response.status_code == 400
        assert 'otp_code' in response.data
    
    def test_otp_login_establishes_session(self):
        """Test that OTP login establishes a session."""
        # Register user first
        self.client.post('/api/v1/auth/register/', {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'phone_number': self.phone_number,
            'password': 'SecureP@ssw0rd123',
            'password_confirm': 'SecureP@ssw0rd123'
        })
        
        # Request OTP
        request_response = self.client.post('/api/v1/auth/otp/request/', {
            'phone_number': self.phone_number
        })
        otp_code = request_response.data['otp_code']
        
        # Verify OTP
        verify_response = self.client.post('/api/v1/auth/otp/verify/', {
            'phone_number': self.phone_number,
            'otp_code': otp_code
        })
        
        assert verify_response.status_code == 200
        
        # Check session is established
        me_response = self.client.get('/api/v1/auth/me/')
        assert me_response.status_code == 200
        assert me_response.data['phone_number'] == self.phone_number

class TestOTPWithoutSMSTestMode(TestCase):
    """OTP behaviour when SMS test mode is off (the production default)."""

    def setUp(self):
        self.client = APIClient()
        self.phone_number = '+998901110001'
        User.objects.create_user(
            email='prod@example.com',
            phone_number=self.phone_number,
            password='testpass123'
        )

    def test_request_otp_returns_503_without_code(self):
        """Without an SMS provider the API returns 503 and never leaks the code."""
        with self.settings(SMS_TEST_MODE=False):
            response = self.client.post('/api/v1/auth/otp/request/', {
                'phone_number': self.phone_number
            })

        assert response.status_code == 503
        assert 'otp_code' not in response.content.decode()

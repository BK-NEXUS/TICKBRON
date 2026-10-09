"""
Tests for user models.
"""
import pytest
from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from users.models import User, UserManager

User = get_user_model()


class TestUserModel(TestCase):
    """Test cases for User model."""
    
    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.check_password('testpass123')
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.is_active is True
    
    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        
        assert user.email == 'admin@example.com'
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_active is True
    
    def test_user_email_normalized(self):
        """Test that email is normalized."""
        email = 'Test@Example.com'
        user = User.objects.create_user(
            email=email,
            password='testpass123'
        )
        
        # Superseded by SECURITY_REVIEW M-1: the whole address is lowercased
        assert user.email == 'test@example.com'
    
    def test_user_without_email_raises_error(self):
        """Test that creating user without email raises ValueError."""
        with pytest.raises(ValueError):
            User.objects.create_user(
                email=None,
                password='testpass123'
            )
    
    def test_user_str_representation(self):
        """Test string representation of User."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        assert str(user) == 'test@example.com'
    
    def test_get_full_name(self):
        """Test get_full_name method with full_name field."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='John Doe'
        )
        
        assert user.get_full_name() == 'John Doe'
    
    def test_get_full_name_from_first_last(self):
        """Test get_full_name method falling back to first_name/last_name."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        assert user.get_full_name() == 'John Doe'
    
    def test_get_full_name_empty(self):
        """Test get_full_name when all name fields are empty."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        assert user.get_full_name() == 'test@example.com'
    
    def test_get_short_name(self):
        """Test get_short_name method."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        assert user.get_short_name() == 'John'
    
    def test_user_email_unique(self):
        """Test that email field is unique."""
        User.objects.create_user(
            email='unique@example.com',
            password='testpass123'
        )
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email='unique@example.com',
                password='testpass123'
            )
    
    def test_user_inherits_base_model(self):
        """Test that User inherits from BaseModel."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Check BaseModel fields
        assert hasattr(user, 'created_at')
        assert hasattr(user, 'updated_at')
        assert hasattr(user, 'is_deleted')
        assert hasattr(user, 'deleted_at')
        assert hasattr(user, 'is_active')
        assert user.is_deleted is False
        assert user.is_active is True
    
    def test_generate_otp(self):
        """Test OTP generation."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            phone_number='+1234567890'
        )
        
        otp_code = user.generate_otp()
        
        assert otp_code is not None
        assert len(otp_code) == 6
        assert otp_code.isdigit()
        assert user.otp_code == otp_code
        assert user.otp_expires_at is not None
        assert user.otp_attempts == 0
    
    def test_verify_otp_success(self):
        """Test successful OTP verification."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            phone_number='+1234567890'
        )
        otp_code = user.generate_otp()
        
        result = user.verify_otp(otp_code)
        
        assert result is True
        user.refresh_from_db()
        assert user.phone_verified is True
        assert user.otp_code is None
        assert user.otp_expires_at is None
    
    def test_verify_otp_invalid(self):
        """Test OTP verification with invalid code."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            phone_number='+1234567890'
        )
        user.generate_otp()
        
        result = user.verify_otp('000000')
        
        assert result is False
        user.refresh_from_db()
        assert user.otp_attempts == 1
    
    def test_verify_otp_expired(self):
        """Test OTP verification with expired code."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            phone_number='+1234567890'
        )
        otp_code = user.generate_otp()
        
        # Manually expire the OTP
        from django.utils import timezone
        from datetime import timedelta
        user.otp_expires_at = timezone.now() - timedelta(minutes=10)
        user.save()
        
        result = user.verify_otp(otp_code)
        
        assert result is False
    
    def test_verify_otp_max_attempts(self):
        """Test OTP verification with max attempts exceeded."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            phone_number='+1234567890'
        )
        otp_code = user.generate_otp()
        
        # Use all attempts
        for _ in range(3):
            user.verify_otp('000000')
        
        result = user.verify_otp(otp_code)
        
        assert result is False
    
    def test_user_whatsapp_field(self):
        """Test whatsapp field can be set and retrieved."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            whatsapp='+1234567890'
        )
        
        assert user.whatsapp == '+1234567890'
    
    def test_user_telegram_field(self):
        """Test telegram field can be set and retrieved."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            telegram='@telegramuser'
        )
        
        assert user.telegram == '@telegramuser'
    
    def test_user_preferred_contact_method_default(self):
        """Test preferred_contact_method defaults to email."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        assert user.preferred_contact_method == 'email'
    
    def test_user_preferred_contact_method_choices(self):
        """Test preferred_contact_method accepts valid choices."""
        for method in ['phone', 'whatsapp', 'telegram', 'email']:
            user = User.objects.create_user(
                email=f'test{method}@example.com',
                password='testpass123',
                preferred_contact_method=method
            )
            assert user.preferred_contact_method == method
    
    def test_user_all_contact_fields(self):
        """Test user with all contact fields set."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            phone_number='+1234567890',
            whatsapp='+1234567890',
            telegram='@telegramuser',
            preferred_contact_method='whatsapp'
        )
        
        assert user.phone_number == '+1234567890'
        assert user.whatsapp == '+1234567890'
        assert user.telegram == '@telegramuser'
        assert user.preferred_contact_method == 'whatsapp'
"""
Tests for user serializers.
"""
import pytest
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from users.models import User
from users.services import register_account
from users.serializers import UserSerializer, UserRegistrationSerializer, UserLoginSerializer, RequestOTPSerializer, VerifyOTPSerializer, UserUpdateSerializer


class TestUserSerializer(TestCase):
    """Test cases for UserSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_user_serializer_basic(self):
        """Test basic UserSerializer functionality."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        assert data['email'] == 'test@example.com'
        assert data['first_name'] == 'Test'
        assert data['last_name'] == 'User'
        assert data['full_name'] == 'Test User'
        assert 'password' not in data  # Password should not be serialized
    
    def test_user_serializer_full_name_method(self):
        """Test get_full_name method in serializer."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        assert data['full_name'] == 'Test User'


class TestUserRegistrationSerializer(TestCase):
    """Test cases for UserRegistrationSerializer."""
    
    def test_valid_registration(self):
        """Test valid user registration with simplified fields."""
        data = {
            'email': 'newuser@example.com',
            'full_name': 'New User',
            'phone_number': '+998901234567',
            'password': 'SecureP@ssw0rd123',
            'password_confirm': 'SecureP@ssw0rd123'
        }
        
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()
        
        register_account(serializer.validated_data)
        user = User.objects.get(email=data['email'])
        assert user.email == 'newuser@example.com'
        assert user.full_name == 'New User'
        assert user.phone_number == '+998901234567'
        assert user.check_password('SecureP@ssw0rd123')
    
    def test_password_mismatch(self):
        """Test registration with mismatched passwords."""
        data = {
            'email': 'newuser@example.com',
            'full_name': 'New User',
            'phone_number': '+998901234567',
            'password': 'securepass123',
            'password_confirm': 'differentpass123'
        }
        
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors
    
    def test_password_too_short(self):
        """Test registration with short password (less than 12 characters)."""
        data = {
            'email': 'newuser@example.com',
            'full_name': 'New User',
            'phone_number': '+998901234567',
            'password': 'short',
            'password_confirm': 'short'
        }
        
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors
    
    def test_missing_required_fields(self):
        """Test registration with missing required fields (full_name and phone_number)."""
        data = {
            'email': 'newuser@example.com',
            'password': 'SecureP@ssw0rd123',
            'password_confirm': 'SecureP@ssw0rd123'
        }
        
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'full_name' in serializer.errors
        assert 'phone_number' in serializer.errors
    
    def test_missing_phone_number(self):
        """Test registration with missing phone_number."""
        data = {
            'email': 'newuser@example.com',
            'full_name': 'New User',
            'password': 'SecureP@ssw0rd123',
            'password_confirm': 'SecureP@ssw0rd123'
        }
        
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'phone_number' in serializer.errors
    
    def test_optional_first_name_last_name(self):
        """Test that first_name and last_name are optional."""
        data = {
            'email': 'newuser@example.com',
            'full_name': 'New User',
            'phone_number': '+998901234567',
            'password': 'SecureP@ssw0rd123',
            'password_confirm': 'SecureP@ssw0rd123'
        }
        
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()
        
        register_account(serializer.validated_data)
        user = User.objects.get(email=data['email'])
        assert user.full_name == 'New User'
        assert user.first_name is None
        assert user.last_name is None
    
    def test_registration_with_contact_fields(self):
        """Test registration with optional contact fields."""
        data = {
            'email': 'newuser@example.com',
            'full_name': 'New User',
            'phone_number': '+998901234567',
            'whatsapp': '+998901234567',
            'telegram': '@telegramuser',
            'preferred_contact_method': 'whatsapp',
            'password': 'SecureP@ssw0rd123',
            'password_confirm': 'SecureP@ssw0rd123'
        }
        
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()
        
        register_account(serializer.validated_data)
        user = User.objects.get(email=data['email'])
        assert user.whatsapp == '+998901234567'
        assert user.telegram == '@telegramuser'
        assert user.preferred_contact_method == 'whatsapp'
    
    def test_user_serializer_includes_contact_fields(self):
        """Test UserSerializer includes new contact fields."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            whatsapp='+998901234567',
            telegram='@telegramuser',
            preferred_contact_method='telegram'
        )
        
        serializer = UserSerializer(user)
        data = serializer.data
        
        assert 'whatsapp' in data
        assert 'telegram' in data
        assert 'preferred_contact_method' in data
        assert data['whatsapp'] == '+998901234567'
        assert data['telegram'] == '@telegramuser'
        assert data['preferred_contact_method'] == 'telegram'


class TestUserLoginSerializer(TestCase):
    """Test cases for UserLoginSerializer."""
    
    def test_valid_login_data(self):
        """Test valid login data."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        serializer = UserLoginSerializer(data=data)
        assert serializer.is_valid()
    
    def test_missing_email(self):
        """Test login with missing email."""
        data = {
            'password': 'testpass123'
        }
        
        serializer = UserLoginSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
    
    def test_missing_password(self):
        """Test login with missing password."""
        data = {
            'email': 'test@example.com'
        }
        
        serializer = UserLoginSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors
    
    def test_invalid_email_format(self):
        """Test login with invalid email format."""
        data = {
            'email': 'invalid-email',
            'password': 'testpass123'
        }
        
        serializer = UserLoginSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors


class TestRequestOTPSerializer(TestCase):
    """Test cases for RequestOTPSerializer."""
    
    def test_valid_phone_number(self):
        """Test valid phone number."""
        data = {
            'phone_number': '+998901234567'
        }
        
        serializer = RequestOTPSerializer(data=data)
        assert serializer.is_valid()
    
    def test_missing_phone_number(self):
        """Test missing phone number."""
        data = {}
        
        serializer = RequestOTPSerializer(data=data)
        assert not serializer.is_valid()
        assert 'phone_number' in serializer.errors
    
    def test_empty_phone_number(self):
        """Test empty phone number."""
        data = {
            'phone_number': ''
        }
        
        serializer = RequestOTPSerializer(data=data)
        assert not serializer.is_valid()
        assert 'phone_number' in serializer.errors


class TestVerifyOTPSerializer(TestCase):
    """Test cases for VerifyOTPSerializer."""
    
    def test_valid_otp_data(self):
        """Test valid OTP data."""
        data = {
            'phone_number': '+998901234567',
            'otp_code': '123456'
        }
        
        serializer = VerifyOTPSerializer(data=data)
        assert serializer.is_valid()
    
    def test_missing_phone_number(self):
        """Test missing phone number."""
        data = {
            'otp_code': '123456'
        }
        
        serializer = VerifyOTPSerializer(data=data)
        assert not serializer.is_valid()
        assert 'phone_number' in serializer.errors
    
    def test_missing_otp_code(self):
        """Test missing OTP code."""
        data = {
            'phone_number': '+998901234567'
        }
        
        serializer = VerifyOTPSerializer(data=data)
        assert not serializer.is_valid()
        assert 'otp_code' in serializer.errors
    
    def test_invalid_otp_code_format(self):
        """Test invalid OTP code format (not 6 digits)."""
        data = {
            'phone_number': '+998901234567',
            'otp_code': '12345'
        }
        
        serializer = VerifyOTPSerializer(data=data)
        assert not serializer.is_valid()
        assert 'otp_code' in serializer.errors
    
    def test_otp_code_with_letters(self):
        """Test OTP code with letters (should be digits only)."""
        data = {
            'phone_number': '+998901234567',
            'otp_code': 'ABCDEF'
        }
        
        serializer = VerifyOTPSerializer(data=data)
        assert not serializer.is_valid()
        assert 'otp_code' in serializer.errors


class TestUserUpdateSerializer(TestCase):
    """Test cases for UserUpdateSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User',
            phone_number='+998901234567'
        )
    
    def test_update_full_name(self):
        """Test updating full name."""
        data = {'full_name': 'Updated Name'}
        serializer = UserUpdateSerializer(self.user, data=data, partial=True)
        assert serializer.is_valid()
        
        updated_user = serializer.save()
        assert updated_user.full_name == 'Updated Name'
    
    def test_update_contact_fields(self):
        """Test updating contact fields."""
        data = {
            'whatsapp': '+998917654321',
            'telegram': '@newtelegram',
            'preferred_contact_method': 'whatsapp'
        }
        serializer = UserUpdateSerializer(self.user, data=data, partial=True)
        assert serializer.is_valid()
        
        updated_user = serializer.save()
        assert updated_user.whatsapp == '+998917654321'
        assert updated_user.telegram == '@newtelegram'
        assert updated_user.preferred_contact_method == 'whatsapp'
    
    def test_update_phone_number(self):
        """Test updating phone number."""
        data = {'phone_number': '+998917654321'}
        serializer = UserUpdateSerializer(self.user, data=data, partial=True)
        assert serializer.is_valid()
        
        updated_user = serializer.save()
        assert updated_user.phone_number == '+998917654321'
    
    def test_partial_update(self):
        """Test partial update (only some fields)."""
        data = {'whatsapp': '+998917654321'}
        serializer = UserUpdateSerializer(self.user, data=data, partial=True)
        assert serializer.is_valid()
        
        updated_user = serializer.save()
        assert updated_user.whatsapp == '+998917654321'
        assert updated_user.full_name == 'Test User'  # Unchanged
        assert updated_user.phone_number == '+998901234567'  # Unchanged
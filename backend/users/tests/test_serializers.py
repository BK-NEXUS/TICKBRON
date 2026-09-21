"""
Tests for user serializers.
"""
import pytest
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from users.models import User
from users.serializers import UserSerializer, UserRegistrationSerializer, UserLoginSerializer, RequestOTPSerializer, VerifyOTPSerializer


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
            'phone_number': '+1234567890',
            'password': 'SecureP@ssw0rd123',
            'password_confirm': 'SecureP@ssw0rd123'
        }
        
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()
        
        user = serializer.save()
        assert user.email == 'newuser@example.com'
        assert user.full_name == 'New User'
        assert user.phone_number == '+1234567890'
        assert user.check_password('SecureP@ssw0rd123')
    
    def test_password_mismatch(self):
        """Test registration with mismatched passwords."""
        data = {
            'email': 'newuser@example.com',
            'full_name': 'New User',
            'phone_number': '+1234567890',
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
            'phone_number': '+1234567890',
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
            'phone_number': '+1234567890',
            'password': 'SecureP@ssw0rd123',
            'password_confirm': 'SecureP@ssw0rd123'
        }
        
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()
        
        user = serializer.save()
        assert user.full_name == 'New User'
        assert user.first_name is None
        assert user.last_name is None


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
            'phone_number': '+1234567890'
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
            'phone_number': '+1234567890',
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
            'phone_number': '+1234567890'
        }
        
        serializer = VerifyOTPSerializer(data=data)
        assert not serializer.is_valid()
        assert 'otp_code' in serializer.errors
    
    def test_invalid_otp_code_format(self):
        """Test invalid OTP code format (not 6 digits)."""
        data = {
            'phone_number': '+1234567890',
            'otp_code': '12345'
        }
        
        serializer = VerifyOTPSerializer(data=data)
        assert not serializer.is_valid()
        assert 'otp_code' in serializer.errors
    
    def test_otp_code_with_letters(self):
        """Test OTP code with letters (should be digits only)."""
        data = {
            'phone_number': '+1234567890',
            'otp_code': 'ABCDEF'
        }
        
        serializer = VerifyOTPSerializer(data=data)
        assert not serializer.is_valid()
        assert 'otp_code' in serializer.errors
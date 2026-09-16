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
        
        # Django's normalize_email only lowercases the domain part
        assert user.email == 'Test@example.com'
    
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
        """Test get_full_name method."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        assert user.get_full_name() == 'John Doe'
    
    def test_get_full_name_empty(self):
        """Test get_full_name when names are empty."""
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
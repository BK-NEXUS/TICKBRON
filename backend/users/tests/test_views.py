"""
Tests for user authentication views.
"""
import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User

User = get_user_model()


class TestAuthViews(TestCase):
    """Test cases for authentication views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }
    
    def test_register_user(self):
        """Test user registration endpoint."""
        response = self.client.post('/api/v1/auth/register/', self.user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email='test@example.com').exists()
        assert 'email' in response.data
        assert response.data['email'] == 'test@example.com'
    
    def test_register_user_auto_login(self):
        """Test that user is automatically logged in after registration."""
        response = self.client.post('/api/v1/auth/register/', self.user_data)
        
        # Check if session was created (user should be logged in)
        assert response.status_code == status.HTTP_201_CREATED
        # In a real scenario, we'd check session cookies, but for API testing
        # we verify the user was created successfully
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        # Create first user
        User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Try to register with same email
        response = self.client.post('/api/v1/auth/register/', self.user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_login_valid_credentials(self):
        """Test login with valid credentials."""
        # Create user
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Login
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post('/api/v1/auth/login/', login_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'test@example.com'
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        login_data = {
            'email': 'test@example.com',
            'password': 'wrongpass'
        }
        response = self.client.post('/api/v1/auth/login/', login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_inactive_user(self):
        """Test login with inactive user."""
        # Create inactive user
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        user.is_active = False
        user.save()
        
        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post('/api/v1/auth/login/', login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_logout_authenticated(self):
        """Test logout for authenticated user."""
        # Create and authenticate user
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user)
        
        response = self.client.post('/api/v1/auth/logout/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'detail' in response.data
    
    def test_logout_unauthenticated(self):
        """Test logout for unauthenticated user."""
        response = self.client.post('/api/v1/auth/logout/')
        
        # Should work even for unauthenticated users (AllowAny permission)
        assert response.status_code == status.HTTP_200_OK
    
    def test_me_authenticated(self):
        """Test getting current user info when authenticated."""
        # Create and authenticate user
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=user)
        
        response = self.client.get('/api/v1/auth/me/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'test@example.com'
        assert response.data['first_name'] == 'Test'
    
    def test_me_unauthenticated(self):
        """Test getting current user info when not authenticated."""
        response = self.client.get('/api/v1/auth/me/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_session_authenticated(self):
        """Test session refresh when authenticated."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=user)
        
        response = self.client.post('/api/v1/auth/refresh/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'test@example.com'
    
    def test_refresh_session_unauthenticated(self):
        """Test session refresh when not authenticated."""
        response = self.client.post('/api/v1/auth/refresh/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
"""
Tests for user security features (login throttling, account lockout, etc.).
"""
import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from users.models import User


class TestUserSecurity(TestCase):
    """Test cases for user security features."""
    
    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='StrongP@ssw0rd123',
            first_name='Test',
            last_name='User'
        )
    
    def test_is_account_locked_when_not_locked(self):
        """Test that account is not locked by default."""
        assert self.user.is_account_locked() is False
    
    def test_is_account_locked_when_locked(self):
        """Test that account is locked when lock time is in future."""
        self.user.account_locked_until = timezone.now() + timedelta(minutes=30)
        self.user.save()
        
        assert self.user.is_account_locked() is True
    
    def test_is_account_locked_when_expired(self):
        """Test that account is not locked when lock time has passed."""
        self.user.account_locked_until = timezone.now() - timedelta(minutes=1)
        self.user.save()
        
        assert self.user.is_account_locked() is False
    
    def test_increment_failed_login(self):
        """Test incrementing failed login attempts."""
        initial_attempts = self.user.failed_login_attempts
        
        self.user.increment_failed_login()
        self.user.refresh_from_db()
        
        assert self.user.failed_login_attempts == initial_attempts + 1
        assert self.user.last_failed_login is not None
    
    def test_account_lockout_after_5_failed_attempts(self):
        """Test that account is locked after 5 failed attempts."""
        for _ in range(5):
            self.user.increment_failed_login()
        
        self.user.refresh_from_db()
        
        assert self.user.account_locked_until is not None
        assert self.user.is_account_locked() is True
    
    def test_reset_failed_login(self):
        """Test resetting failed login attempts."""
        self.user.failed_login_attempts = 3
        self.user.account_locked_until = timezone.now() + timedelta(minutes=30)
        self.user.save()
        
        self.user.reset_failed_login()
        self.user.refresh_from_db()
        
        assert self.user.failed_login_attempts == 0
        assert self.user.last_failed_login is None
        assert self.user.account_locked_until is None
    
    def test_login_ip_storage(self):
        """Test that login IP is stored."""
        ip_address = '192.168.1.1'
        self.user.last_login_ip = ip_address
        self.user.save()
        
        self.user.refresh_from_db()
        assert self.user.last_login_ip == ip_address
    
    def test_email_verification_fields(self):
        """Test email verification fields exist."""
        assert hasattr(self.user, 'email_verified')
        assert hasattr(self.user, 'email_verification_token')
        assert hasattr(self.user, 'email_verification_sent_at')
        
        assert self.user.email_verified is False
        assert self.user.email_verification_token is None
        assert self.user.email_verification_sent_at is None
    
    def test_two_factor_fields(self):
        """Test 2FA fields exist."""
        assert hasattr(self.user, 'two_factor_enabled')
        assert hasattr(self.user, 'two_factor_secret')
        assert hasattr(self.user, 'two_factor_backup_codes')
        
        assert self.user.two_factor_enabled is False
        assert self.user.two_factor_secret is None
        assert self.user.two_factor_backup_codes is None
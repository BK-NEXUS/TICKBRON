"""
User models for TICKBRON.

This module contains the custom User model and related user management models.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from common.models import BaseModel


class UserManager(BaseUserManager):
    """
    Custom user manager for email-based authentication.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Custom User model for TICKBRON.
    
    Uses email as the username field and includes additional fields
    for user management and profile information.
    """
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=300, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Security and verification fields
    failed_login_attempts = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    
    # 2FA foundation fields
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=255, blank=True, null=True)
    two_factor_backup_codes = models.TextField(blank=True, null=True)
    
    # Phone OTP authentication fields
    phone_verified = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_expires_at = models.DateTimeField(null=True, blank=True)
    otp_attempts = models.IntegerField(default=0)
    
    # Contact method preferences
    whatsapp = models.CharField(max_length=20, blank=True, null=True)
    telegram = models.CharField(max_length=50, blank=True, null=True)
    PREFERRED_CONTACT_CHOICES = [
        ('phone', 'Phone'),
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('email', 'Email'),
    ]
    preferred_contact_method = models.CharField(
        max_length=10,
        choices=PREFERRED_CONTACT_CHOICES,
        default='email',
        blank=True,
        null=True
    )
    
    # Role foundation (for RBAC)
    role = models.ForeignKey('permissions.Role', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """
        Return the full_name if set, otherwise first_name plus last_name, with a space in between.
        """
        if self.full_name:
            return self.full_name
        full_name = f'{self.first_name or ""} {self.last_name or ""}'.strip()
        return full_name if full_name else self.email
    
    def get_short_name(self):
        """
        Return the short name for the user.
        """
        return self.first_name
    
    def is_account_locked(self):
        """
        Check if the account is currently locked due to failed login attempts.
        """
        if self.account_locked_until and self.account_locked_until > timezone.now():
            return True
        return False
    
    def increment_failed_login(self):
        """
        Increment failed login attempts and lock account if threshold reached.
        """
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            from datetime import timedelta
            self.account_locked_until = timezone.now() + timedelta(minutes=30)
        
        self.save()
    
    def reset_failed_login(self):
        """
        Reset failed login attempts after successful login.
        """
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.account_locked_until = None
        self.save()
    
    def generate_otp(self):
        """
        Generate a 6-digit OTP code for phone verification.
        """
        import random
        from datetime import timedelta
        
        self.otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.otp_expires_at = timezone.now() + timedelta(minutes=5)
        self.otp_attempts = 0
        self.save()
        return self.otp_code
    
    def verify_otp(self, code):
        """
        Verify the OTP code.
        
        Returns True if valid, False otherwise.
        """
        if not self.otp_code or not self.otp_expires_at:
            return False
        
        if timezone.now() > self.otp_expires_at:
            return False
        
        if self.otp_attempts >= 3:
            return False
        
        self.otp_attempts += 1
        self.save()
        
        if self.otp_code == code:
            self.otp_code = None
            self.otp_expires_at = None
            self.otp_attempts = 0
            self.phone_verified = True
            self.save()
            return True
        
        return False

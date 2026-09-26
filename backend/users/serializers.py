"""
Serializers for user models.

This module contains serializers for the User model to be used in API endpoints.
"""
from rest_framework import serializers
from users.models import User
from users.validators import EmailFormatValidator


def validate_unique_phone_number(value, instance=None):
    """
    Check phone number uniqueness after normalization.

    The model's UniqueValidator runs on the raw input, so a number with extra
    whitespace would slip past it and fail at the database instead.
    """
    users = User.objects.filter(phone_number=value)
    if instance is not None:
        users = users.exclude(pk=instance.pk)
    if users.exists():
        raise serializers.ValidationError("A user with this phone number already exists.")
    return value


class UserSerializer(serializers.ModelSerializer):
    """
    Base serializer for User model.
    """
    full_name = serializers.SerializerMethodField()
    # Role name ('hotel-owner') or None. Only a super-admin assigns roles, so it is read-only
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name',
                  'phone_number', 'whatsapp', 'telegram', 'preferred_contact_method',
                  'is_active', 'date_joined', 'last_login',
                  'email_verified', 'two_factor_enabled', 'is_staff', 'is_superuser', 'role']
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_staff', 'is_superuser']

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_role(self, obj):
        return obj.role.name if obj.role else None


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, min_length=12)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone_number', 'whatsapp', 'telegram', 
                  'preferred_contact_method', 'password', 'password_confirm']
        extra_kwargs = {
            'full_name': {'required': True},
            'phone_number': {'required': True},
        }
    
    def validate_email(self, value):
        """Validate email format."""
        validator = EmailFormatValidator()
        validator.validate(value)
        return value
    
    def validate_phone_number(self, value):
        """Validate phone number format and uniqueness."""
        if not value or not value.strip():
            raise serializers.ValidationError("Phone number is required.")
        return validate_unique_phone_number(value.strip())
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate_email(self, value):
        """Validate email format."""
        validator = EmailFormatValidator()
        validator.validate(value)
        return value


class RequestOTPSerializer(serializers.Serializer):
    """
    Serializer for requesting OTP code.
    """
    phone_number = serializers.CharField()
    
    def validate_phone_number(self, value):
        """Validate phone number format."""
        if not value or not value.strip():
            raise serializers.ValidationError("Phone number is required.")
        return value.strip()


class VerifyOTPSerializer(serializers.Serializer):
    """
    Serializer for verifying OTP code.
    """
    phone_number = serializers.CharField()
    otp_code = serializers.CharField(max_length=6)
    
    def validate_phone_number(self, value):
        """Validate phone number format."""
        if not value or not value.strip():
            raise serializers.ValidationError("Phone number is required.")
        return value.strip()
    
    def validate_otp_code(self, value):
        """Validate OTP code format."""
        if not value or not value.strip():
            raise serializers.ValidationError("OTP code is required.")
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("OTP code must be 6 digits.")
        return value.strip()


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """
    class Meta:
        model = User
        fields = ['full_name', 'first_name', 'last_name', 'phone_number', 
                  'whatsapp', 'telegram', 'preferred_contact_method']
        extra_kwargs = {
            'full_name': {'required': False},
            'phone_number': {'required': False},
        }
    
    def validate_phone_number(self, value):
        """Normalize and check uniqueness; blank clears the number."""
        value = (value or '').strip() or None
        if value is None:
            return None
        return validate_unique_phone_number(value, instance=self.instance)
    
    def update(self, instance, validated_data):
        # A changed number has not been verified by OTP yet
        if 'phone_number' in validated_data and validated_data['phone_number'] != instance.phone_number:
            instance.phone_verified = False
        return super().update(instance, validated_data)

"""
Serializers for user models.

This module contains serializers for the User model to be used in API endpoints.
"""
from rest_framework import serializers
from users.models import User
from users.validators import EmailFormatValidator


class UserSerializer(serializers.ModelSerializer):
    """
    Base serializer for User model.
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 
                  'phone_number', 'is_active', 'date_joined', 'last_login',
                  'email_verified', 'two_factor_enabled']
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, min_length=12)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone_number', 
                  'password', 'password_confirm']
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
        """Validate phone number format."""
        if not value or not value.strip():
            raise serializers.ValidationError("Phone number is required.")
        return value.strip()
    
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

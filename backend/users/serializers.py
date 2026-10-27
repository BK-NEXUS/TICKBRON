"""
Serializers for user models.

This module contains serializers for the User model to be used in API endpoints.
"""
from common.validators import validate_person_name
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from users.models import User
from users.validators import EmailFormatValidator, PHONE_NUMBER_ERROR, parse_phone_number


class LowercaseEmailField(serializers.EmailField):
    """An address typed with any capitals is the same address: it is lower-cased before it is checked and stored."""

    def to_internal_value(self, data):
        return super().to_internal_value(data).strip().lower()


def unique_email_field():
    """The e-mail field of a form that makes an account: lower case, and not taken by another account."""
    return LowercaseEmailField(validators=[UniqueValidator(
        queryset=User.objects.all(), message='User with this email already exists.')])


def validate_new_password(attrs):
    """
    Run AUTH_PASSWORD_VALIDATORS on attrs['password'] and raise a 400 under 'password'.

    The other attrs (email, names) feed the similarity check, through an unsaved user.
    """
    user = User(**{
        field: attrs[field] for field in ('email', 'full_name', 'first_name', 'last_name')
        if attrs.get(field)
    })
    try:
        validate_password(attrs['password'], user=user)
    except DjangoValidationError as e:
        raise serializers.ValidationError({'password': list(e.messages)})


def validate_phone_number_format(value):
    """Return the E.164 form of the number or raise a 400 with one clear message."""
    normalized = parse_phone_number(value)
    if normalized is None:
        raise serializers.ValidationError(PHONE_NUMBER_ERROR)
    return normalized


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
        # phone_number is legacy data: shown, never written
        read_only_fields = ['id', 'phone_number', 'date_joined', 'last_login', 'is_staff', 'is_superuser']

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_role(self, obj):
        return obj.role.name if obj.role else None


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    email = unique_email_field()
    password = serializers.CharField(write_only=True, min_length=12)
    password_confirm = serializers.CharField(write_only=True)
    # Stored only (no SMS, no code); several accounts may share a number
    phone_number = serializers.CharField(max_length=30)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone_number', 'whatsapp', 'telegram',
                  'preferred_contact_method', 'password', 'password_confirm']
        extra_kwargs = {'full_name': {'required': True, 'validators': [validate_person_name]}}
    
    def validate_email(self, value):
        """Validate email format."""
        validator = EmailFormatValidator()
        validator.validate(value)
        return value

    def validate_phone_number(self, value):
        return validate_phone_number_format(value)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        validate_new_password(attrs)
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
    email = LowercaseEmailField()
    password = serializers.CharField()
    
    def validate_email(self, value):
        """Validate email format."""
        validator = EmailFormatValidator()
        validator.validate(value)
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """The address a reset link is requested for."""
    email = LowercaseEmailField()


class NewPasswordSerializer(serializers.Serializer):
    """A new password typed twice. Its strength is checked by validate_new_password, which needs the user."""
    password = serializers.CharField(max_length=128)
    password_confirm = serializers.CharField(max_length=128)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': "Password fields didn't match."})
        return attrs


class PasswordResetConfirmSerializer(NewPasswordSerializer):
    """The link's uid and token, and the new password."""
    uid = serializers.CharField(max_length=64)
    token = serializers.CharField(max_length=128)


class PasswordChangeSerializer(NewPasswordSerializer):
    """The current password proves the person at the keyboard knows it."""
    current_password = serializers.CharField(max_length=128)


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile. The phone number can be changed but never blanked.
    """
    phone_number = serializers.CharField(required=False, max_length=30)

    class Meta:
        model = User
        fields = ['full_name', 'first_name', 'last_name', 'phone_number', 'whatsapp', 'telegram', 'preferred_contact_method']
        extra_kwargs = {
            'full_name': {'required': False, 'validators': [validate_person_name]},
            'first_name': {'validators': [validate_person_name]},
            'last_name': {'validators': [validate_person_name]},
        }

    def validate_phone_number(self, value):
        return validate_phone_number_format(value)


"""
Paydalanıwshı model leri ushın serializer ler.

Bul modul API endpoint lerinde paydalanıw ushın User modeli serializer lerin óz ishine aladı.
"""
from common.validators import validate_person_name
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from users import two_factor
from users.models import User
from users.validators import EmailFormatValidator, PHONE_NUMBER_ERROR, parse_phone_number
from django.utils.translation import gettext as _


class LowercaseEmailField(serializers.EmailField):
    """Qálegen úlken háripler menen terilgen mánzil birdey mánzil: ol tekserilmesten hám saqlanbastan aldın kishi háripke
    ótkiziledi."""

    def to_internal_value(self, data):
        return super().to_internal_value(data).strip().lower()


def unique_email_field():
    """Akkaunt jaratatuǵın formanıń e-mail maydanı: kishi háripte hám basqa akkaunt tárepinen alınbaǵan."""
    return LowercaseEmailField(validators=[UniqueValidator(
        queryset=User.objects.all(), message='User with this email already exists.')])


def validate_new_password(attrs):
    """
    attrs['password'] ge AUTH_PASSWORD_VALIDATORS di isletip, 'password' astında 400 kóteriw.

    Basqa attrs (email, atlar) saqlanbaǵan paydalanıwshı arqalı uqsaslıq tekseriwin bekkemleydi.
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
    """Nomerdiń E.164 formasın qaytarıw yamasa bir anıq xabar menen 400 kóteriw."""
    normalized = parse_phone_number(value)
    if normalized is None:
        raise serializers.ValidationError(PHONE_NUMBER_ERROR)
    return normalized


class UserSerializer(serializers.ModelSerializer):
    """
    User modeli ushın tiykarǵı serializer.
    """
    full_name = serializers.SerializerMethodField()
    # Rol atı ('hotel-owner') yamasa None. Rollardı tek super-admin beredi, sol sebepli tek oqıw
    role = serializers.SerializerMethodField()
    # Eki basqıshlı kirisiwdi sazlawı kerek hám sazlamaǵan administrator ushın True: sayt sazlaw ekranın kórsetedi
    two_factor_setup_required = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name',
                  'phone_number', 'whatsapp', 'telegram', 'preferred_contact_method',
                  'is_active', 'date_joined', 'last_login',
                  'email_verified', 'two_factor_enabled', 'two_factor_setup_required', 'is_staff', 'is_superuser', 'role']
        # phone_number eski maǵlıwmat: kórsetiledi, hesh qashan jazılmaydı
        read_only_fields = ['id', 'phone_number', 'date_joined', 'last_login', 'is_staff', 'is_superuser']

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_role(self, obj):
        return obj.role.name if obj.role else None

    def get_two_factor_setup_required(self, obj):
        return two_factor.needs_setup(obj)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Paydalanıwshı dizimnen ótiwi ushın serializer.
    """
    email = unique_email_field()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    # Tek saqlanadı (SMS joq, kod joq); bir neshe akkaunt nomerdi bóliwi múmkin
    phone_number = serializers.CharField(max_length=30)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone_number', 'whatsapp', 'telegram',
                  'preferred_contact_method', 'password', 'password_confirm']
        extra_kwargs = {'full_name': {'required': True, 'allow_blank': False, 'validators': [validate_person_name]}}

    def validate_email(self, value):
        """E-mail formatın tekseriw."""
        validator = EmailFormatValidator()
        validator.validate(value)
        return value

    def validate_phone_number(self, value):
        return validate_phone_number_format(value)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": _("Password fields didn't match.")})
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
    Paydalanıwshı kirisiwi ushın serializer.
    """
    email = LowercaseEmailField()
    password = serializers.CharField()

    def validate_email(self, value):
        """E-mail formatın tekseriw."""
        validator = EmailFormatValidator()
        validator.validate(value)
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """Tiklew siltemesi soralatuǵın mánzil."""
    email = LowercaseEmailField()


class NewPasswordSerializer(serializers.Serializer):
    """Eki ret terilgen jańa parol. Onıń kúshi validate_new_password penen tekseriledi, ol paydalanıwshını talap etedi."""
    password = serializers.CharField(max_length=128)
    password_confirm = serializers.CharField(max_length=128)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': _("Password fields didn't match.")})
        return attrs


class PasswordResetConfirmSerializer(NewPasswordSerializer):
    """Siltemeniń uid hám token i, hám jańa parol."""
    uid = serializers.CharField(max_length=64)
    token = serializers.CharField(max_length=128)


class PasswordChangeSerializer(NewPasswordSerializer):
    """Házirgi parol klaviatura artındaǵı adamnıń onı biletuǵının dálillaydı."""
    current_password = serializers.CharField(max_length=128)


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Paydalanıwshı profilin jańalaw ushın serializer. Telefon nomerin ózgertiw múmkin, biraq hesh qashan bosatıp bolmaydı.
    """
    phone_number = serializers.CharField(required=False, max_length=30)

    class Meta:
        model = User
        fields = ['full_name', 'first_name', 'last_name', 'phone_number', 'whatsapp', 'telegram',
                  'preferred_contact_method']
        extra_kwargs = {
            'full_name': {'required': False, 'validators': [validate_person_name]},
            'first_name': {'validators': [validate_person_name]},
            'last_name': {'validators': [validate_person_name]},
        }

    def validate_phone_number(self, value):
        return validate_phone_number_format(value)

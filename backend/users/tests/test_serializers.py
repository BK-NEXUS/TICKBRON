"""
Paydalanıwshı serializer leri ushın testler.
"""
from django.test import TestCase
from users.models import User
from users.serializers import UserSerializer, UserRegistrationSerializer, UserLoginSerializer, UserUpdateSerializer


class TestUserSerializer(TestCase):
    """UserSerializer ushın test jaǵdayları."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_user_serializer_basic(self):
        """Ápiwayı UserSerializer funkciyasın testlew."""
        serializer = UserSerializer(self.user)
        data = serializer.data

        assert data['email'] == 'test@example.com'
        assert data['first_name'] == 'Test'
        assert data['last_name'] == 'User'
        assert data['full_name'] == 'Test User'
        assert 'password' not in data  # Parol serializaciya etilmewi kerek

    def test_user_serializer_full_name_method(self):
        """Serializer degi get_full_name metodın testlew."""
        serializer = UserSerializer(self.user)
        data = serializer.data

        assert data['full_name'] == 'Test User'


class TestUserRegistrationSerializer(TestCase):
    """UserRegistrationSerializer ushın test jaǵdayları."""

    def test_valid_registration(self):
        """Ápiwayılastırılǵan maydanlar menen jaramlı paydalanıwshı dizimin testlew."""
        data = {
            'email': 'newuser@example.com',
            'full_name': 'New User',
            'password': 'SecureP@ssw0rd123',
            'password_confirm': 'SecureP@ssw0rd123',
            'phone_number': '+998901234567',
        }

        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()

        user = serializer.save()
        assert user.email == 'newuser@example.com'
        assert user.full_name == 'New User'
        assert user.phone_number == '+998901234567'  # E.164 formatında saqlanadı (burın saqlanbaytuǵın edi)
        assert user.check_password('SecureP@ssw0rd123')

    def test_password_mismatch(self):
        """Parollar sáykes kelmegen dizimdi testlew."""
        data = {
            'email': 'newuser@example.com',
            'full_name': 'New User',
            'password': 'securepass123',
            'password_confirm': 'differentpass123',
            'phone_number': '+998901234567',
        }

        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

    def test_password_too_short(self):
        """Qısqa parol (8 belgiden kem) menen dizimdi testlew."""
        data = {
            'email': 'newuser@example.com',
            'full_name': 'New User',
            'password': 'short',
            'password_confirm': 'short'
        }

        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

    def test_missing_required_fields(self):
        """Májbúriy maydanlar (full_name) joq dizimdi testlew."""
        data = {
            'email': 'newuser@example.com',
            'password': 'SecureP@ssw0rd123',
            'password_confirm': 'SecureP@ssw0rd123',
            'phone_number': '+998901234567',
        }

        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'full_name' in serializer.errors

    def test_optional_first_name_last_name(self):
        """first_name hám last_name ıqtıyarıy ekenin testlew."""
        data = {
            'email': 'newuser@example.com',
            'full_name': 'New User',
            'password': 'SecureP@ssw0rd123',
            'password_confirm': 'SecureP@ssw0rd123',
            'phone_number': '+998901234567',
        }

        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()

        user = serializer.save()
        assert user.full_name == 'New User'
        assert user.first_name is None
        assert user.last_name is None

    def test_registration_with_contact_fields(self):
        """Iqtıyarıy baylanıs maydanları menen dizimdi testlew."""
        data = {
            'email': 'newuser@example.com',
            'full_name': 'New User',
            'whatsapp': '+998901234567',
            'telegram': '@telegramuser',
            'preferred_contact_method': 'whatsapp',
            'password': 'SecureP@ssw0rd123',
            'password_confirm': 'SecureP@ssw0rd123',
            'phone_number': '+998901234567',
        }

        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()

        user = serializer.save()
        assert user.whatsapp == '+998901234567'
        assert user.telegram == '@telegramuser'
        assert user.preferred_contact_method == 'whatsapp'

    def test_user_serializer_includes_contact_fields(self):
        """UserSerializer jańa baylanıs maydanların óz ishine alatuǵının testlew."""
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
    """UserLoginSerializer ushın test jaǵdayları."""

    def test_valid_login_data(self):
        """Jaramlı kiriw maǵlıwmatın testlew."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }

        serializer = UserLoginSerializer(data=data)
        assert serializer.is_valid()

    def test_missing_email(self):
        """Email joq kiriwdi testlew."""
        data = {
            'password': 'testpass123'
        }

        serializer = UserLoginSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_missing_password(self):
        """Parol joq kiriwdi testlew."""
        data = {
            'email': 'test@example.com'
        }

        serializer = UserLoginSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

    def test_invalid_email_format(self):
        """Jaramsız email formatı menen kiriwdi testlew."""
        data = {
            'email': 'invalid-email',
            'password': 'testpass123'
        }

        serializer = UserLoginSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors


class TestUserUpdateSerializer(TestCase):
    """UserUpdateSerializer ushın test jaǵdayları."""

    def setUp(self):
        """Test maǵlıwmatın tayarlaw."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User',
            phone_number='+998901234567'
        )

    def test_update_full_name(self):
        """Tolıq atın jańalawdı testlew."""
        data = {'full_name': 'Updated Name'}
        serializer = UserUpdateSerializer(self.user, data=data, partial=True)
        assert serializer.is_valid()

        updated_user = serializer.save()
        assert updated_user.full_name == 'Updated Name'

    def test_update_contact_fields(self):
        """Baylanıs maydanların jańalawdı testlew."""
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

    def test_partial_update(self):
        """Bólekshe jańalawdı (tek keybir maydanlar) testlew."""
        data = {'whatsapp': '+998917654321'}
        serializer = UserUpdateSerializer(self.user, data=data, partial=True)
        assert serializer.is_valid()

        updated_user = serializer.save()
        assert updated_user.whatsapp == '+998917654321'
        assert updated_user.full_name == 'Test User'  # Ózgermegen
        assert updated_user.phone_number == '+998901234567'  # Ózgermegen

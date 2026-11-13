"""
Paydalanıwshı model leri ushın testler.
"""
import pytest
from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from users.models import User

User = get_user_model()


class TestUserModel(TestCase):
    """User modeli ushın test jaǵdayları."""

    def test_create_user(self):
        """Ápiwayı paydalanıwshı jaratıwdı testlew."""
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
        """Superuser jaratıwdı testlew."""
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
        """Email normalizaciya etilgenin testlew."""
        email = 'Test@Example.com'
        user = User.objects.create_user(
            email=email,
            password='testpass123'
        )

        # Pútkil mánzil kishi háripke ótkeriledi (users/tests/test_email_case.py ge qarań)
        assert user.email == 'test@example.com'

    def test_user_without_email_raises_error(self):
        """Email siz paydalanıwshı jaratıw ValueError shıǵaratuǵının testlew."""
        with pytest.raises(ValueError):
            User.objects.create_user(
                email=None,
                password='testpass123'
            )

    def test_user_str_representation(self):
        """User diń tekst kórinisin testlew."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

        assert str(user) == 'test@example.com'

    def test_get_full_name(self):
        """full_name maydanı menen get_full_name metodın testlew."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='John Doe'
        )

        assert user.get_full_name() == 'John Doe'

    def test_get_full_name_from_first_last(self):
        """first_name/last_name ge qaytıp túsetuǵın get_full_name metodın testlew."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )

        assert user.get_full_name() == 'John Doe'

    def test_get_full_name_empty(self):
        """Barlıq at maydanları bos bolǵanda get_full_name di testlew."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

        assert user.get_full_name() == 'test@example.com'

    def test_get_short_name(self):
        """get_short_name metodın testlew."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )

        assert user.get_short_name() == 'John'

    def test_user_email_unique(self):
        """Email maydanı unikal ekenin testlew."""
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
        """User BaseModel den miras alatuǵının testlew."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

        # BaseModel maydanların tekseriw
        assert hasattr(user, 'created_at')
        assert hasattr(user, 'updated_at')
        assert hasattr(user, 'is_deleted')
        assert hasattr(user, 'deleted_at')
        assert hasattr(user, 'is_active')
        assert user.is_deleted is False
        assert user.is_active is True

    def test_user_whatsapp_field(self):
        """whatsapp maydanı qoyılıp, qayta oqıla alatuǵının testlew."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            whatsapp='+1234567890'
        )

        assert user.whatsapp == '+1234567890'

    def test_user_telegram_field(self):
        """telegram maydanı qoyılıp, qayta oqıla alatuǵının testlew."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            telegram='@telegramuser'
        )

        assert user.telegram == '@telegramuser'

    def test_user_preferred_contact_method_default(self):
        """preferred_contact_method ádetde email ekenin testlew."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

        assert user.preferred_contact_method == 'email'

    def test_user_preferred_contact_method_choices(self):
        """preferred_contact_method jaramlı tańlawlardı qabıllaytuǵının testlew."""
        for method in ['phone', 'whatsapp', 'telegram', 'email']:
            user = User.objects.create_user(
                email=f'test{method}@example.com',
                password='testpass123',
                preferred_contact_method=method
            )
            assert user.preferred_contact_method == method

    def test_user_all_contact_fields(self):
        """Barlıq baylanıs maydanları qoyılǵan paydalanıwshını testlew."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            phone_number='+1234567890',
            whatsapp='+1234567890',
            telegram='@telegramuser',
            preferred_contact_method='whatsapp'
        )

        assert user.phone_number == '+1234567890'
        assert user.whatsapp == '+1234567890'
        assert user.telegram == '@telegramuser'
        assert user.preferred_contact_method == 'whatsapp'

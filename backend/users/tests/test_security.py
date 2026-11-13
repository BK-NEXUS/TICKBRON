"""
Paydalanıwshı qáwipsizlik funkciyaları ushın testler (kiriwdi tezlikti sheklew, akkauntti bloklaw h.t.b.).
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from users.models import User


class TestUserSecurity(TestCase):
    """Paydalanıwshı qáwipsizlik funkciyaları ushın test jaǵdayları."""

    def setUp(self):
        """Test paydalanıwshısın tayarlaw."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='StrongP@ssw0rd123',
            first_name='Test',
            last_name='User'
        )

    def test_is_account_locked_when_not_locked(self):
        """Akkaunt ádetde bloklanbaǵanın testlew."""
        assert self.user.is_account_locked() is False

    def test_is_account_locked_when_locked(self):
        """Bloklaw waqtı keleshekte bolsa akkaunt bloklanǵanın testlew."""
        self.user.account_locked_until = timezone.now() + timedelta(minutes=30)
        self.user.save()

        assert self.user.is_account_locked() is True

    def test_is_account_locked_when_expired(self):
        """Bloklaw waqtı ótip ketken bolsa akkaunt bloklanbaǵanın testlew."""
        self.user.account_locked_until = timezone.now() - timedelta(minutes=1)
        self.user.save()

        assert self.user.is_account_locked() is False

    def test_increment_failed_login(self):
        """Sátsiz kiriw urınıwları sanın arttırıwdı testlew."""
        initial_attempts = self.user.failed_login_attempts

        self.user.increment_failed_login()
        self.user.refresh_from_db()

        assert self.user.failed_login_attempts == initial_attempts + 1
        assert self.user.last_failed_login is not None

    def test_account_lockout_after_account_failure_limit(self):
        """Pútkil akkaunt boyınsha bloklawǵa kóp sátsizlik kerek (qalǵanın hár IP boyınsha bloklaw isleydi)."""
        for _ in range(User.ACCOUNT_FAILURE_LIMIT - 1):
            self.user.increment_failed_login()
        self.user.refresh_from_db()
        assert self.user.is_account_locked() is False

        self.user.increment_failed_login()
        self.user.refresh_from_db()

        assert self.user.account_locked_until is not None
        assert self.user.is_account_locked() is True

    def test_reset_failed_login(self):
        """Sátsiz kiriw urınıwların nolge túsiriwdi testlew."""
        self.user.failed_login_attempts = 3
        self.user.account_locked_until = timezone.now() + timedelta(minutes=30)
        self.user.save()

        self.user.reset_failed_login()
        self.user.refresh_from_db()

        assert self.user.failed_login_attempts == 0
        assert self.user.last_failed_login is None
        assert self.user.account_locked_until is None

    def test_login_ip_storage(self):
        """Kiriw IP si saqlanatuǵının testlew."""
        ip_address = '192.168.1.1'
        self.user.last_login_ip = ip_address
        self.user.save()

        self.user.refresh_from_db()
        assert self.user.last_login_ip == ip_address

    def test_email_verification_fields(self):
        """Email tastıyıqlaw maydanları barlıǵın testlew."""
        assert hasattr(self.user, 'email_verified')
        assert hasattr(self.user, 'email_verification_token')
        assert hasattr(self.user, 'email_verification_sent_at')

        assert self.user.email_verified is False
        assert self.user.email_verification_token is None
        assert self.user.email_verification_sent_at is None

    def test_two_factor_fields(self):
        """2FA maydanları barlıǵın testlew."""
        assert hasattr(self.user, 'two_factor_enabled')
        assert hasattr(self.user, 'two_factor_secret')
        assert hasattr(self.user, 'two_factor_backup_codes')

        assert self.user.two_factor_enabled is False
        assert self.user.two_factor_secret is None
        assert self.user.two_factor_backup_codes is None

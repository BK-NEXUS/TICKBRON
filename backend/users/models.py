"""
TICKBRON ushın User model leri.

Bul modul óz User modelin hám paydalanıwshını basqarıwǵa baylanıslı model lerdi óz ishine aladı.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone
from common.models import BaseModel


class UserManager(BaseUserManager):
    """
    E-mail tiykarındaǵı autentifikaciya ushın óz paydalanıwshı manager i.

    Mánzil úlken háripleri qanday bolsa da birdey mánzil: ol kishi háripte saqlanadı hám sol usılda izlenedi.
    """

    @classmethod
    def normalize_email(cls, email):
        return (email or '').strip().lower()

    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: self.normalize_email(username)})

    def create_user(self, email, password=None, **extra_fields):
        """
        Berilgen e-mail hám parol menen ápiwayı paydalanıwshı jaratıw hám saqlaw.
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
        Berilgen e-mail hám parol menen superuser jaratıw hám saqlaw.
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
    TICKBRON ushın óz User modeli.

    E-mail di username maydanı retinde paydalanadı hám paydalanıwshını basqarıw hám profil maǵlıwmatı
    ushın qosımsha maydanlardı óz ishine aladı.
    """
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=300, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    # Eski, tek oqıw: ilovada hesh nárse endi nomerdi jıynamaydı yamasa tekspeydi (akkauntlar
    # tek e-mail). Bos NULL retinde saqlanadı; unikal emes, eski akkauntlar nomerdi bólisiwi múmkin.
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    # Qáwipsizlik hám tekseriw maydanları
    failed_login_attempts = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)

    # 2FA tiykar maydanları
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=255, blank=True, null=True)
    two_factor_backup_codes = models.TextField(blank=True, null=True)
    # Eń sońǵı qabıllanǵan kodtıń 30 sekundlıq qádemi, sol sebepli kodtı eki ret paydalanıp bolmaydı (users/two_factor.py)
    two_factor_last_step = models.BigIntegerField(null=True, blank=True)

    # Baylanıs usılı qálewleri
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

    # Rol tiykarı (RBAC ushın)
    role = models.ForeignKey('permissions.Role', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        constraints = [
            # Hár poshta qutısına bir akkaunt, úlken háripleri qanday bolsa da (saqlanǵan mánis aldınan kishi háripte)
            models.UniqueConstraint(Lower('email'), name='users_email_lower_unique'),
        ]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Joq telefon nomerin NULL retinde saqlaw, sonda unikal constraint kóplerine ruxsat beredi
        if self.phone_number is not None:
            self.phone_number = self.phone_number.strip() or None
        super().save(*args, **kwargs)

    def get_full_name(self):
        """
        full_name belgilengen bolsa, onı, bolmasa first_name hám last_name di aralarında bos orın penen qaytarıw.
        """
        if self.full_name:
            return self.full_name
        full_name = f'{self.first_name or ""} {self.last_name or ""}'.strip()
        return full_name if full_name else self.email

    def get_short_name(self):
        """
        Paydalanıwshı ushın qısqa atın qaytarıw.
        """
        return self.first_name

    def is_account_locked(self):
        """
        Akkauntiń sátsiz kirisiw urınıwları sebepli házir bloklanǵanın tekseriw.
        """
        if self.account_locked_until and self.account_locked_until > timezone.now():
            return True
        return False

    # Akkaunt dárejesindegi lockout (barlıq IP birge); IP boyınsha lockout users.lockout ta
    ACCOUNT_FAILURE_LIMIT = 20
    ACCOUNT_FAILURE_WINDOW_MINUTES = 30
    ACCOUNT_LOCK_MINUTES = 15

    def increment_failed_login(self):
        """
        Sátsiz kirisiw urınıwların kóbeytiw hám shek jetse akkaunttı bloklaw.

        Oynadan eski qátelikler endi esaplanbaydı, sol sebepli waqıt-waqıtı menen bolǵan
        jazıw qátelikleri hesh qashan blokqa jıynalmaydı. Shek ataylap joqarı: tómen
        akkaunt dárejesindegi limit qálegen adamǵa qálegen paydalanıwshını bloklawǵa múmkinshilik beredi (qarań
        users.lockout).
        """
        from datetime import timedelta
        now = timezone.now()
        window_start = now - timedelta(minutes=self.ACCOUNT_FAILURE_WINDOW_MINUTES)
        if self.last_failed_login is None or self.last_failed_login < window_start:
            self.failed_login_attempts = 0

        self.failed_login_attempts += 1
        self.last_failed_login = now

        if self.failed_login_attempts >= self.ACCOUNT_FAILURE_LIMIT:
            self.account_locked_until = now + timedelta(minutes=self.ACCOUNT_LOCK_MINUTES)

        # Tek usı maydanlar: eskirgen jaddaǵı paydalanıwshı basqalardı (mısalı usı arada ózgertilgen paroldi) qayta jazbawı
        # kerek
        self.save(update_fields=['failed_login_attempts', 'last_failed_login', 'account_locked_until'])

    def reset_failed_login(self):
        """
        Tabıslı kirisiwden keyin sátsiz kirisiw urınıwların qayta ornatıw.
        """
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.account_locked_until = None
        self.save(update_fields=['failed_login_attempts', 'last_failed_login', 'account_locked_until'])

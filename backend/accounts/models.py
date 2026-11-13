"""
accounts app ınıń model leri.

Bul modul favorit ler, sharhlar, bildiriwler hám akkaunt tariyxı model lerin óz ishine aladı.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class Favorite(BaseModel):
    """
    Paydalanıwshınıń favorit mehmanxanaları.

    Paydalanıwshıǵa qızıqqan mehmanxanalardı tez ashıw ushın saqlaw imkaniyatın beredi.
    """
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='favorites')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='favorited_by')
    notes = models.TextField(blank=True, null=True, help_text="User notes about this favorite")

    class Meta:
        db_table = 'favorites'
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'
        unique_together = ['user', 'property']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['property', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.property.city}"


class Review(BaseModel):
    """
    Paydalanıwshılardıń mehmanxanalar haqqındaǵı sharhları.

    Paydalanıwshılar tek bronlaǵan hám turǵan mehmanxanalarına sharh jaza aladı.
    Sharhta hár túrli kategoriyalar boyınsha bahalar hám ulıwma baha boladı.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='reviews')
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='reviews')
    booking = models.ForeignKey('bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')

    # Ulıwma baha
    overall_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Overall rating from 1 to 5"
    )

    # Kategoriyalar boyınsha bahalar
    cleanliness_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Cleanliness rating from 1 to 5"
    )
    location_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Location rating from 1 to 5"
    )
    value_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Value for money rating from 1 to 5"
    )
    amenities_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Amenities rating from 1 to 5"
    )
    service_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Service rating from 1 to 5"
    )

    # Sharh mazmunı
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField(blank=True)

    # Sharh statusı
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Mehmanxana iyesiniń sharhqa ashıq juwabı (bos: ele juwap joq)
    owner_reply = models.TextField(blank=True, default='')
    replied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'reviews'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        unique_together = ['user', 'booking']  # Hár bron ushın bir sharh
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['property', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['overall_rating']),
            # Bir mehmanxananıń ashıq sharhları, eń jańası birinshi
            models.Index(fields=['property', 'status', 'created_at'], name='review_prop_status_idx'),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.property.city} ({self.overall_rating}/5)"

    def save(self, *args, **kwargs):
        if not self.reviewed_at and self.status == 'approved':
            self.reviewed_at = timezone.now()
        super().save(*args, **kwargs)


class Notification(BaseModel):
    """
    Paydalanıwshı bildiriwleri.

    Bronlar, tólemler hám basqa waqıyalar haqqında sistema bildiriwleri.
    """
    TYPE_CHOICES = [
        ('booking', 'Booking'),
        ('payment', 'Payment'),
        ('review', 'Review'),
        ('promotion', 'Promotion'),
        ('system', 'System'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')

    title = models.CharField(max_length=200)
    message = models.TextField()

    # R12: mashinanıń oqıytuǵın kodı + params (tek id, summa, sana; qarań: accounts.notifications).
    # title/message bul inglizsha zapas (fallback) tekst. R12 den aldın jaratılǵan bildiriwlerde Null.
    code = models.CharField(max_length=64, null=True, blank=True)
    params = models.JSONField(null=True, blank=True)

    # Iqtıyarıy baylanıslı obyektler
    booking = models.ForeignKey('bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    property = models.ForeignKey('properties.Property', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')

    # Bildiriwdi jetkiziw
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_via_email = models.BooleanField(default=False)
    sent_via_sms = models.BooleanField(default=False)

    # Háreket siltemesi (ıqtıyarıy)
    action_url = models.URLField(blank=True, null=True)
    action_label = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['user', 'notification_type', 'created_at']),
            models.Index(fields=['priority', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title}"

    def mark_as_read(self):
        """Bildiriwdi oqılǵan dep belgilew."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class AccountHistory(BaseModel):
    """
    Paydalanıwshı akkaunt tariyxı hám háreketler logı.

    Akkauntta bolǵan áhmiyetli háreket hám ózgerislerdi audit ushın jazıp baradı.
    """
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('email_change', 'Email Change'),
        ('profile_update', 'Profile Update'),
        ('account_created', 'Account Created'),
        ('account_deleted', 'Account Deleted'),
        ('booking_created', 'Booking Created'),
        ('booking_cancelled', 'Booking Cancelled'),
        ('payment_completed', 'Payment Completed'),
        ('review_submitted', 'Review Submitted'),
        ('favorite_added', 'Favorite Added'),
        ('favorite_removed', 'Favorite Removed'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='account_history')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)

    # Háreket haqqında tolıq maǵlıwmat
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Baylanıslı obyektler (ıqtıyarıy)
    booking = models.ForeignKey('bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='history_entries')
    property = models.ForeignKey('properties.Property', on_delete=models.SET_NULL, null=True, blank=True, related_name='history_entries')

    # Qosımsha kontekst (iyilgish maǵlıwmat ushın JSON maydanı)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'account_history'
        verbose_name = 'Account History'
        verbose_name_plural = 'Account History'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['user', 'action', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.created_at}"

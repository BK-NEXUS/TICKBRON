"""
Property models for TICKBRON.

This module contains models for properties, translations, policies, and related structures.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from common.models import BaseModel


class PropertyType(BaseModel):
    """
    Property type model (e.g., apartment, house, villa, studio).
    
    Categorizes properties by their type for filtering and display.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # Icon class or emoji
    
    class Meta:
        db_table = 'property_types'
        verbose_name = 'Property Type'
        verbose_name_plural = 'Property Types'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Property(BaseModel):
    """
    Core Property model for TICKBRON.
    
    Represents a property available for booking with all essential information.
    """
    # Ownership
    owner = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='properties',
        db_index=True
    )
    
    # Property classification
    property_type = models.ForeignKey(
        PropertyType,
        on_delete=models.PROTECT,
        related_name='properties',
        db_index=True
    )
    
    # Status
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending_approval', _('Pending Approval')),
        ('active', _('Active')),
        ('suspended', _('Suspended')),
        ('rejected', _('Rejected')),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )
    
    # Capacity
    max_guests = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        help_text=_('Maximum number of guests allowed')
    )
    bedrooms = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        help_text=_('Number of bedrooms')
    )
    bathrooms = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        help_text=_('Number of bathrooms')
    )
    
    # Location
    address_line1 = models.CharField(max_length=255, db_index=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, db_index=True)
    
    # Geolocation
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )
    
    # Pricing
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default='USD')  # ISO 4217 currency code
    
    # Additional info
    total_area = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Total area in square meters')
    )
    floor_number = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Floor number (if applicable)')
    )
    has_elevator = models.BooleanField(default=False)
    has_parking = models.BooleanField(default=False)
    has_wifi = models.BooleanField(default=False)
    has_ac = models.BooleanField(default=False)
    has_heating = models.BooleanField(default=False)
    
    # Approval tracking
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_properties'
    )
    rejection_reason = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'properties'
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['city', 'country']),
            models.Index(fields=['base_price']),
        ]
    
    def __str__(self):
        return f"Property {self.id} - {self.city}, {self.country}"
    
    def get_full_address(self):
        """Return the full address as a string."""
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        parts.append(self.country)
        return ', '.join(parts)


class PropertyTranslation(BaseModel):
    """
    Property translation model for multilingual support.
    
    Stores translated property information for different languages.
    """
    LANGUAGE_CHOICES = [
        ('en', _('English')),
        ('ru', _('Russian')),
        ('uz', _('Uzbek')),
    ]
    
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='translations',
        db_index=True
    )
    language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        db_index=True
    )
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'property_translations'
        verbose_name = 'Property Translation'
        verbose_name_plural = 'Property Translations'
        unique_together = ('property', 'language')
        ordering = ['property', 'language']
    
    def __str__(self):
        return f"{self.property.id} - {self.language}: {self.name}"


class PropertyPolicy(BaseModel):
    """
    Property policy model for property-level policies.
    
    Stores various policies like check-in/check-out, cancellation, etc.
    """
    POLICY_TYPE_CHOICES = [
        ('check_in', _('Check-in Policy')),
        ('check_out', _('Check-out Policy')),
        ('cancellation', _('Cancellation Policy')),
        ('children', _('Children Policy')),
        ('pets', _('Pets Policy')),
        ('smoking', _('Smoking Policy')),
        ('age_restriction', _('Age Restriction')),
        ('payment', _('Payment Policy')),
        ('house_rules', _('House Rules')),
    ]
    
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='policies',
        db_index=True
    )
    policy_type = models.CharField(
        max_length=50,
        choices=POLICY_TYPE_CHOICES,
        db_index=True
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    is_strict = models.BooleanField(
        default=False,
        help_text=_('Whether this policy is strictly enforced')
    )
    
    class Meta:
        db_table = 'property_policies'
        verbose_name = 'Property Policy'
        verbose_name_plural = 'Property Policies'
        unique_together = ('property', 'policy_type')
        ordering = ['property', 'policy_type']
    
    def __str__(self):
        return f"{self.property.id} - {self.get_policy_type_display()}"

"""
Property models for TICKBRON.

This module contains models for properties, translations, policies, and related structures.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from common.models import BaseModel
from common.storage import get_media_upload_path, validate_image_file


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


class AmenityCategory(BaseModel):
    """
    Amenity category model for organizing amenities into groups.
    
    Examples: Kitchen, Bathroom, Entertainment, Safety, etc.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # Icon class or emoji
    sort_order = models.PositiveIntegerField(default=0, help_text=_('Display order'))
    
    class Meta:
        db_table = 'amenity_categories'
        verbose_name = 'Amenity Category'
        verbose_name_plural = 'Amenity Categories'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['sort_order', 'name']),
        ]
    
    def __str__(self):
        return self.name


class AmenityCategoryTranslation(BaseModel):
    """
    Amenity category translation model for multilingual support.
    
    Stores translated amenity category information for different languages.
    """
    LANGUAGE_CHOICES = [
        ('en', _('English')),
        ('ru', _('Russian')),
        ('uz', _('Uzbek')),
    ]
    
    category = models.ForeignKey(
        AmenityCategory,
        on_delete=models.CASCADE,
        related_name='translations',
        db_index=True
    )
    language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        db_index=True
    )
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'amenity_category_translations'
        verbose_name = 'Amenity Category Translation'
        verbose_name_plural = 'Amenity Category Translations'
        unique_together = ('category', 'language')
        ordering = ['category', 'language']
    
    def __str__(self):
        return f"{self.category.name} - {self.language}: {self.name}"


class Amenity(BaseModel):
    """
    Amenity model for individual property amenities.
    
    Examples: WiFi, Air Conditioning, Swimming Pool, Kitchen, etc.
    """
    category = models.ForeignKey(
        AmenityCategory,
        on_delete=models.PROTECT,
        related_name='amenities',
        db_index=True
    )
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # Icon class or emoji
    is_searchable = models.BooleanField(
        default=True,
        help_text=_('Whether this amenity can be used in search filters')
    )
    sort_order = models.PositiveIntegerField(default=0, help_text=_('Display order'))
    
    class Meta:
        db_table = 'amenities'
        verbose_name = 'Amenity'
        verbose_name_plural = 'Amenities'
        ordering = ['category', 'sort_order', 'name']
        indexes = [
            models.Index(fields=['category', 'sort_order', 'name']),
            models.Index(fields=['is_searchable']),
        ]
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class AmenityTranslation(BaseModel):
    """
    Amenity translation model for multilingual support.
    
    Stores translated amenity information for different languages.
    """
    LANGUAGE_CHOICES = [
        ('en', _('English')),
        ('ru', _('Russian')),
        ('uz', _('Uzbek')),
    ]
    
    amenity = models.ForeignKey(
        Amenity,
        on_delete=models.CASCADE,
        related_name='translations',
        db_index=True
    )
    language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        db_index=True
    )
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'amenity_translations'
        verbose_name = 'Amenity Translation'
        verbose_name_plural = 'Amenity Translations'
        unique_together = ('amenity', 'language')
        ordering = ['amenity', 'language']
    
    def __str__(self):
        return f"{self.amenity.name} - {self.language}: {self.name}"


class PropertyAmenity(BaseModel):
    """
    Property amenity relation model.
    
    Links properties to their available amenities with optional additional information.
    """
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='property_amenities',
        db_index=True
    )
    amenity = models.ForeignKey(
        Amenity,
        on_delete=models.CASCADE,
        related_name='property_amenities',
        db_index=True
    )
    is_available = models.BooleanField(
        default=True,
        help_text=_('Whether this amenity is currently available at the property')
    )
    notes = models.TextField(blank=True, null=True, help_text=_('Additional notes about this amenity'))
    
    class Meta:
        db_table = 'property_amenities'
        verbose_name = 'Property Amenity'
        verbose_name_plural = 'Property Amenities'
        unique_together = ('property', 'amenity')
        ordering = ['property', 'amenity']
        indexes = [
            models.Index(fields=['property', 'amenity']),
            models.Index(fields=['is_available']),
        ]
    
    def __str__(self):
        availability = "Available" if self.is_available else "Not Available"
        return f"{self.property.id} - {self.amenity.name} ({availability})"


class PropertyPhoto(BaseModel):
    """
    Property photo model for handling property images.
    
    Stores property photos with metadata, ordering, and storage abstraction.
    """
    PHOTO_TYPE_CHOICES = [
        ('exterior', _('Exterior')),
        ('interior', _('Interior')),
        ('amenity', _('Amenity')),
        ('room', _('Room')),
        ('other', _('Other')),
    ]
    
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='photos',
        db_index=True
    )
    photo = models.ImageField(
        upload_to=get_media_upload_path,
        help_text=_('Property photo image')
    )
    photo_type = models.CharField(
        max_length=20,
        choices=PHOTO_TYPE_CHOICES,
        default='other',
        db_index=True,
        help_text=_('Type of photo')
    )
    caption = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Photo caption or description')
    )
    is_primary = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_('Whether this is the primary/cover photo for the property')
    )
    display_order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text=_('Display order for photos')
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Alt text for accessibility')
    )
    
    class Meta:
        db_table = 'property_photos'
        verbose_name = 'Property Photo'
        verbose_name_plural = 'Property Photos'
        ordering = ['property', 'display_order', 'created_at']
        indexes = [
            models.Index(fields=['property', 'display_order']),
            models.Index(fields=['is_primary']),
            models.Index(fields=['photo_type']),
        ]
    
    def __str__(self):
        return f"Photo {self.id} - Property {self.property.id} ({self.get_photo_type_display()})"
    
    def clean(self):
        """Validate the photo file."""
        super().clean()
        
        if self.photo:
            # Validate the image file
            is_valid, error_message = validate_image_file(self.photo)
            if not is_valid:
                raise ValidationError({'photo': error_message})
            
            # Ensure only one primary photo per property
            if self.is_primary:
                existing_primary = PropertyPhoto.objects.filter(
                    property=self.property,
                    is_primary=True
                ).exclude(id=self.id)
                
                if existing_primary.exists():
                    raise ValidationError({
                        'is_primary': _('Only one primary photo is allowed per property')
                    })
    
    def save(self, *args, **kwargs):
        """Override save to enforce single primary photo constraint."""
        if self.is_primary:
            # Set all other photos for this property to non-primary
            PropertyPhoto.objects.filter(
                property=self.property,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Get the absolute URL for the photo."""
        return self.photo.url if self.photo else None


class RoomType(BaseModel):
    """
    Room type model for classifying rooms within properties.
    
    Examples: Standard Room, Suite, Deluxe Room, Studio, Penthouse.
    """
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='room_types',
        db_index=True
    )
    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=100, db_index=True)
    description = models.TextField(blank=True, null=True)
    base_occupancy = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        help_text=_('Standard number of guests this room can accommodate')
    )
    max_occupancy = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        help_text=_('Maximum number of guests this room can accommodate')
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Base price per night for this room type')
    )
    currency = models.CharField(max_length=3, default='USD')  # ISO 4217 currency code
    total_rooms = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=1,
        help_text=_('Total number of rooms of this type')
    )
    bed_configuration = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Bed configuration, e.g., "1 King Bed, 1 Queen Bed"')
    )
    room_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Room size in square meters')
    )
    
    class Meta:
        db_table = 'room_types'
        verbose_name = 'Room Type'
        verbose_name_plural = 'Room Types'
        unique_together = ('property', 'slug')
        ordering = ['property', 'name']
        indexes = [
            models.Index(fields=['property', 'name']),
            models.Index(fields=['base_price']),
        ]
    
    def __str__(self):
        return f"{self.property.id} - {self.name}"
    
    def clean(self):
        """Validate room type data."""
        super().clean()
        
        if self.max_occupancy < self.base_occupancy:
            raise ValidationError({
                'max_occupancy': _('Maximum occupancy cannot be less than base occupancy')
            })


class RoomPhoto(BaseModel):
    """
    Room photo model for handling room images.
    
    Stores room photos with metadata, ordering, and storage abstraction.
    """
    PHOTO_TYPE_CHOICES = [
        ('bedroom', _('Bedroom')),
        ('bathroom', _('Bathroom')),
        ('living_area', _('Living Area')),
        ('kitchen', _('Kitchen')),
        ('view', _('View')),
        ('other', _('Other')),
    ]
    
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        related_name='photos',
        db_index=True
    )
    photo = models.ImageField(
        upload_to=get_media_upload_path,
        help_text=_('Room photo image')
    )
    photo_type = models.CharField(
        max_length=20,
        choices=PHOTO_TYPE_CHOICES,
        default='other',
        db_index=True,
        help_text=_('Type of photo')
    )
    caption = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Photo caption or description')
    )
    is_primary = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_('Whether this is the primary photo for the room type')
    )
    display_order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text=_('Display order for photos')
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Alt text for accessibility')
    )
    
    class Meta:
        db_table = 'room_photos'
        verbose_name = 'Room Photo'
        verbose_name_plural = 'Room Photos'
        ordering = ['room_type', 'display_order', 'created_at']
        indexes = [
            models.Index(fields=['room_type', 'display_order']),
            models.Index(fields=['is_primary']),
            models.Index(fields=['photo_type']),
        ]
    
    def __str__(self):
        return f"Photo {self.id} - {self.room_type.name} ({self.get_photo_type_display()})"
    
    def clean(self):
        """Validate the photo file."""
        super().clean()
        
        if self.photo:
            # Validate the image file
            is_valid, error_message = validate_image_file(self.photo)
            if not is_valid:
                raise ValidationError({'photo': error_message})
            
            # Ensure only one primary photo per room type
            if self.is_primary:
                existing_primary = RoomPhoto.objects.filter(
                    room_type=self.room_type,
                    is_primary=True
                ).exclude(id=self.id)
                
                if existing_primary.exists():
                    raise ValidationError({
                        'is_primary': _('Only one primary photo is allowed per room type')
                    })
    
    def save(self, *args, **kwargs):
        """Override save to enforce single primary photo constraint."""
        if self.is_primary:
            # Set all other photos for this room type to non-primary
            RoomPhoto.objects.filter(
                room_type=self.room_type,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Get the absolute URL for the photo."""
        return self.photo.url if self.photo else None


class RoomAmenity(BaseModel):
    """
    Room amenity relation model.
    
    Links room types to their available amenities with optional additional information.
    """
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        related_name='room_amenities',
        db_index=True
    )
    amenity = models.ForeignKey(
        Amenity,
        on_delete=models.CASCADE,
        related_name='room_amenities',
        db_index=True
    )
    is_available = models.BooleanField(
        default=True,
        help_text=_('Whether this amenity is currently available in this room type')
    )
    notes = models.TextField(blank=True, null=True, help_text=_('Additional notes about this amenity'))
    
    class Meta:
        db_table = 'room_amenities'
        verbose_name = 'Room Amenity'
        verbose_name_plural = 'Room Amenities'
        unique_together = ('room_type', 'amenity')
        ordering = ['room_type', 'amenity']
        indexes = [
            models.Index(fields=['room_type', 'amenity']),
            models.Index(fields=['is_available']),
        ]
    
    def __str__(self):
        availability = "Available" if self.is_available else "Not Available"
        return f"{self.room_type.name} - {self.amenity.name} ({availability})"


class RatePlan(BaseModel):
    """
    Rate plan model for pricing strategies.
    
    Defines different pricing plans (e.g., Standard, Non-refundable, Early Bird).
    """
    RATE_TYPE_CHOICES = [
        ('standard', _('Standard Rate')),
        ('non_refundable', _('Non-refundable Rate')),
        ('early_bird', _('Early Bird Rate')),
        ('last_minute', _('Last Minute Rate')),
        ('long_stay', _('Long Stay Rate')),
        ('seasonal', _('Seasonal Rate')),
        ('corporate', _('Corporate Rate')),
        ('promo', _('Promotional Rate')),
    ]
    
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        related_name='rate_plans',
        db_index=True
    )
    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=100, db_index=True)
    rate_type = models.CharField(
        max_length=20,
        choices=RATE_TYPE_CHOICES,
        default='standard',
        db_index=True
    )
    description = models.TextField(blank=True, null=True)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Base price per night for this rate plan')
    )
    currency = models.CharField(max_length=3, default='USD')  # ISO 4217 currency code
    min_nights = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        help_text=_('Minimum nights required for this rate plan')
    )
    max_nights = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Maximum nights allowed for this rate plan (null for unlimited)')
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_('Whether this rate plan is currently active')
    )
    cancellation_policy = models.TextField(
        blank=True,
        null=True,
        help_text=_('Cancellation policy for this rate plan')
    )
    deposit_required = models.BooleanField(
        default=False,
        help_text=_('Whether a deposit is required for this rate plan')
    )
    deposit_percentage = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Deposit percentage (0-100)')
    )
    advance_booking_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Days in advance required for booking (null for no restriction)')
    )
    
    class Meta:
        db_table = 'rate_plans'
        verbose_name = 'Rate Plan'
        verbose_name_plural = 'Rate Plans'
        unique_together = ('room_type', 'slug')
        ordering = ['room_type', 'name']
        indexes = [
            models.Index(fields=['room_type', 'name']),
            models.Index(fields=['rate_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['base_price']),
        ]
    
    def __str__(self):
        return f"{self.room_type.name} - {self.name}"
    
    def clean(self):
        """Validate rate plan data."""
        super().clean()
        
        if self.max_nights and self.max_nights < self.min_nights:
            raise ValidationError({
                'max_nights': _('Maximum nights cannot be less than minimum nights')
            })
        
        if self.deposit_required and (self.deposit_percentage is None or self.deposit_percentage == 0):
            raise ValidationError({
                'deposit_percentage': _('Deposit percentage is required when deposit is required')
            })
        
        if not self.deposit_required and self.deposit_percentage:
            raise ValidationError({
                'deposit_percentage': _('Deposit percentage should not be set when deposit is not required')
            })


class DateInventory(BaseModel):
    """
    Date inventory model for tracking availability and pricing over time.
    
    Stores day-by-day inventory data including availability status and pricing adjustments.
    """
    rate_plan = models.ForeignKey(
        RatePlan,
        on_delete=models.CASCADE,
        related_name='date_inventory',
        db_index=True
    )
    date = models.DateField(db_index=True)
    available_rooms = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        help_text=_('Number of rooms available for this date')
    )
    booked_rooms = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        help_text=_('Number of rooms booked for this date')
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text=_('Price for this specific date (overrides rate plan base price if set)')
    )
    currency = models.CharField(max_length=3, default='USD')  # ISO 4217 currency code
    is_available = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_('Whether this date is available for booking')
    )
    minimum_stay = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Minimum stay requirement for this specific date')
    )
    maximum_stay = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Maximum stay requirement for this specific date')
    )
    notes = models.TextField(blank=True, null=True, help_text=_('Notes for this specific date'))
    
    class Meta:
        db_table = 'date_inventory'
        verbose_name = 'Date Inventory'
        verbose_name_plural = 'Date Inventory'
        unique_together = ('rate_plan', 'date')
        ordering = ['rate_plan', 'date']
        indexes = [
            models.Index(fields=['rate_plan', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['is_available']),
            models.Index(fields=['available_rooms']),
        ]
    
    def __str__(self):
        return f"{self.rate_plan.name} - {self.date} ({self.available_rooms} available)"
    
    def clean(self):
        """Validate date inventory data."""
        super().clean()
        
        if self.booked_rooms > self.available_rooms:
            raise ValidationError({
                'booked_rooms': _('Booked rooms cannot exceed available rooms')
            })
        
        if self.minimum_stay and self.maximum_stay and self.maximum_stay < self.minimum_stay:
            raise ValidationError({
                'maximum_stay': _('Maximum stay cannot be less than minimum stay')
            })
    
    @property
    def remaining_rooms(self):
        """Calculate remaining available rooms."""
        return max(0, self.available_rooms - self.booked_rooms)
    
    def is_available_for_booking(self, nights=1):
        """Check if this date is available for booking with the specified number of nights."""
        if not self.is_available:
            return False
        
        if self.remaining_rooms < 1:
            return False
        
        if self.minimum_stay and nights < self.minimum_stay:
            return False
        
        if self.maximum_stay and nights > self.maximum_stay:
            return False
        
        return True

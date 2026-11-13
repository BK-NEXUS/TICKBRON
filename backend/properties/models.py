"""
TICKBRON ushın Property model leri.

Bul modul mehmanxanalar, awdarmalar, siyasatlar hám olarǵa baylanıslı dúzilislerdiń model lerin óz ishine aladı.
"""
from datetime import timedelta
from django.db import models, transaction, IntegrityError
from django.db.models import F
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from common.models import BaseModel
from common.storage import get_media_upload_path, validate_image_file


class PropertyType(BaseModel):
    """
    Mehmanxana túri modeli (mısalı apartment, house, villa, studio).

    Mehmanxanalardı túri boyınsha filterlew hám kórsetiw ushın toparlaydı.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # Ikonka klası yamasa emoji

    class Meta:
        db_table = 'property_types'
        verbose_name = 'Property Type'
        verbose_name_plural = 'Property Types'
        ordering = ['name']

    def __str__(self):
        return self.name


class Property(BaseModel):
    """
    TICKBRON ushın tiykarǵı Property modeli.

    Barlıq tiykarǵı maǵlıwmatı menen bronlawǵa bar mehmanxananı kórsetedi.
    """
    # Iyelik
    owner = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='properties',
        db_index=True
    )

    # Mehmanxana klassifikaciyası
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

    # Sıyımlılıq
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

    # Jaylasıw
    address_line1 = models.CharField(max_length=255, db_index=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, db_index=True)

    # Geografiya sózligi. Belgilengende save() olardıń inglizsha atların joqarıdaǵı tekst
    # maydanlar country, state hám city ge kóshiredi (city kóshirmesi regionnıń atı: regiondan tómen qala yamasa tuman joq),
    # sonda olardı ele oqıytuǵın kod islewin dawam etedi.
    country_ref = models.ForeignKey(
        'geography.Country', on_delete=models.PROTECT, null=True, blank=True, related_name='properties')
    region_ref = models.ForeignKey(
        'geography.Region', on_delete=models.PROTECT, null=True, blank=True, related_name='properties')

    # Geojaylasıw
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

    # Bahalaw
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default='USD')  # ISO 4217 valyuta kodı

    # Qosımsha maǵlıwmat
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

    # Tastıyıqlawdı baqlaw
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
            # Status bólimleri: mámleket > region (state) tereńlew
            models.Index(fields=['country', 'state'], name='property_country_state_idx'),
            models.Index(fields=['base_price']),
        ]

    def __str__(self):
        return f"Property {self.id} - {self.city}, {self.country}"

    def save(self, *args, **kwargs):
        # Eski tekst jaylasıwdı Geography ref leri (inglizsha atlar) menen sáykes saqlaw
        if self.country_ref_id:
            self.country = self.country_ref.name_en
        if self.region_ref_id:
            self.state = self.region_ref.name_en
            self.city = self.region_ref.name_en
        update_fields = kwargs.get('update_fields')
        if update_fields is not None and {'country_ref', 'region_ref'} & set(update_fields):
            kwargs['update_fields'] = set(update_fields) | {'country', 'state', 'city'}
        super().save(*args, **kwargs)

    def display_name(self, language='en'):
        """
        Adamlarǵa kórsetiletuǵın at: `language` degi awdarma, bolmasa qálegen awdarma,
        bolmasa mánzil. Bar bolsa aldınan júklengen awdarmalardı paydalanadı.
        """
        translations = [t for t in self.translations.all() if not t.is_deleted and t.name]
        for translation in translations:
            if translation.language == language:
                return translation.name
        if translations:
            return translations[0].name
        return self.get_full_address()

    def get_full_address(self):
        """Tolıq mánzildi qatar retinde qaytarıw."""
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        parts.append(self.country)
        return ', '.join(self._without_repeats(parts))

    @staticmethod
    def _without_repeats(parts):
        """Qala hám onıń regionı kóbinese birdey atqa iye (Tashkent, Tashkent); hár atın bir márte jazıń."""
        seen, kept = set(), []
        for part in parts:
            if part.casefold() not in seen:
                seen.add(part.casefold())
                kept.append(part)
        return kept


class PropertyTranslation(BaseModel):
    """
    Kóp tillilikti qollaw ushın mehmanxana awdarması modeli.

    Mehmanxana maǵlıwmatınıń túrli tillerdegi awdarmaların saqlaydı.
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
    Mehmanxana dárejesindegi siyasatlar ushın mehmanxana siyasatı modeli.

    Kiriw/shıǵıw, biykar etiw hám t.b. túrli siyasatlardı saqlaydı.
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
    Amenity lerdi toparlarǵa shólkemlestiriw ushın amenity kategoriyası modeli.

    Mısallar: Asxana, Hammam, Oyın-kúlki, Qáwipsizlik hám t.b.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # Ikonka klası yamasa emoji
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
    Kóp tillilikti qollaw ushın amenity kategoriyası awdarması modeli.

    Amenity kategoriyası maǵlıwmatınıń túrli tillerdegi awdarmaların saqlaydı.
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
    Jeke mehmanxana amenity leri ushın amenity modeli.

    Mısallar: WiFi, kondicioner, basseyn, asxana hám t.b.
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
    icon = models.CharField(max_length=50, blank=True, null=True)  # Ikonka klası yamasa emoji
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
    Kóp tillilikti qollaw ushın amenity awdarması modeli.

    Amenity maǵlıwmatınıń túrli tillerdegi awdarmaların saqlaydı.
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
    Mehmanxana amenity baylanıs modeli.

    Mehmanxanalardı olardıń bar amenity lerine ıqtıyarıy qosımsha maǵlıwmat penen baylanıstıradı.
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
    Mehmanxana súwretlerin islew ushın mehmanxana súwreti modeli.

    Mehmanxana súwretlerin metadata, tártip hám storage abstrakciyası menen saqlaydı.
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
        """Súwret fayldı tekseriw."""
        super().clean()

        if self.photo:
            # Súwret fayldı tekseriw
            is_valid, error_message = validate_image_file(self.photo)
            if not is_valid:
                raise ValidationError({'photo': error_message})

            # Hár mehmanxanaǵa tek bir tiykarǵı súwret bolıwın támiyinlew
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
        """Jalǵız tiykarǵı súwret qısıwın májbúrlew ushın save di qayta anıqlaw."""
        if self.is_primary:
            # Usı mehmanxananıń barlıq basqa súwretlerin tiykarǵı emes etip belgilew
            PropertyPhoto.objects.filter(
                property=self.property,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)

        super().save(*args, **kwargs)

    def remove(self):
        """Usı súwretti soft-delete etiw; muqaba bolsa, qalǵan birinshi súwret muqaba boladı."""
        was_cover = self.is_primary
        self.is_primary = False
        self.soft_delete()
        if was_cover:
            successor = PropertyPhoto.objects.filter(property=self.property, is_deleted=False).first()
            if successor is not None:
                successor.is_primary = True
                successor.save()

    def get_absolute_url(self):
        """Súwret ushın absolyut URL di alıw."""
        return self.photo.url if self.photo else None


class RoomType(BaseModel):
    """
    Mehmanxanalar ishindegi xonalardı klassifikaciyalaw ushın xona túri modeli.

    Mısallar: Standard xona, Suite, Deluxe xona, Studio, Penthouse.
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
    currency = models.CharField(max_length=3, default='USD')  # ISO 4217 valyuta kodı
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

    # R9: mehmanxana iyesi óz qálewi boyınsha belgileydi, tastıyıqlaw joq (.ai/PLAN_R9_VIP.md v2); VIP xonalar birinshi
    # dizimlenedi
    is_vip = models.BooleanField(
        default=False,
        help_text=_('A VIP room: shown first and with a badge')
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
        """Xona túri maǵlıwmatın tekseriw."""
        super().clean()

        if self.max_occupancy < self.base_occupancy:
            raise ValidationError({
                'max_occupancy': _('Maximum occupancy cannot be less than base occupancy')
            })


class RoomPhoto(BaseModel):
    """
    Xona súwretlerin islew ushın xona súwreti modeli.

    Xona súwretlerin metadata, tártip hám storage abstrakciyası menen saqlaydı.
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
        """Súwret fayldı tekseriw."""
        super().clean()

        if self.photo:
            # Súwret fayldı tekseriw
            is_valid, error_message = validate_image_file(self.photo)
            if not is_valid:
                raise ValidationError({'photo': error_message})

            # Hár xona túrine tek bir tiykarǵı súwret bolıwın támiyinlew
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
        """Jalǵız tiykarǵı súwret qısıwın májbúrlew ushın save di qayta anıqlaw."""
        if self.is_primary:
            # Usı xona túriniń barlıq basqa súwretlerin tiykarǵı emes etip belgilew
            RoomPhoto.objects.filter(
                room_type=self.room_type,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)

        super().save(*args, **kwargs)

    def remove(self):
        """Usı súwretti soft-delete etiw; muqaba bolsa, qalǵan birinshi súwret muqaba boladı."""
        was_cover = self.is_primary
        self.is_primary = False
        self.soft_delete()
        if was_cover:
            successor = RoomPhoto.objects.filter(room_type=self.room_type, is_deleted=False).first()
            if successor is not None:
                successor.is_primary = True
                successor.save()

    def get_absolute_url(self):
        """Súwret ushın absolyut URL di alıw."""
        return self.photo.url if self.photo else None


class RoomAmenity(BaseModel):
    """
    Xona amenity baylanıs modeli.

    Xona túrlerin olardıń bar amenity lerine ıqtıyarıy qosımsha maǵlıwmat penen baylanıstıradı.
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
    Baha strategiyaları ushın rate plan modeli.

    Túrli baha rejelerin anıqlaydı (mısalı Standard, Qaytarılmaytuǵın, Early Bird).
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
    currency = models.CharField(max_length=3, default='USD')  # ISO 4217 valyuta kodı
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
    # R11 tegin biykar etiw (.ai/PLAN_R11_CANCELLATION.md); bron jaratılǵanda oǵan kóshiriledi
    free_cancel_hours = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MaxValueValidator(8760)],
        help_text=_('Guests cancelling at least this many hours before the check-in day get everything back (empty = no free window)')
    )
    cancel_refund_percent = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MaxValueValidator(100)],
        help_text=_('Percent refunded when cancelling after the free window, 0 = non-refundable (empty = the platform percent)')
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
        """Rate plan maǵlıwmatın tekseriw."""
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


def _check_bulk_range(date_from, date_to):
    """Kóp ózgertiwler hár kúnge bir qatar jazadı: aralıqtı turıw sıyaqlı shekle (R4 qáwipsizlik tekseriwi)."""
    from bookings.pricing import MAX_STAY_NIGHTS
    if (date_to - date_from).days > MAX_STAY_NIGHTS:
        raise ValidationError({'date_to': _('The range can be at most %(days)d days') % {'days': MAX_STAY_NIGHTS}})


class RatePlanPrice(models.Model):
    """
    R16: mehmanxana iyesiniń rate plan nıń taǵı bir valyutadaǵı (USD, UZS, KZT, RUB) óz bahası.

    Plannıń tiykarǵı bahası `RatePlan.base_price` + `currency` (mehmanxananıń valyutası) de qaladı;
    bul jerdegi hár qatar iye basqa valyutada kirgizgen sol túngi baha, sebebi
    valyuta kursları ózgeredi. Qatarı joq valyuta CBU kursı boyınsha konvertaciyalanıp kórsetiledi ("shama menen").
    """
    rate_plan = models.ForeignKey(RatePlan, on_delete=models.CASCADE, related_name='prices')
    currency = models.CharField(max_length=3)
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rate_plan_prices'
        constraints = [
            models.UniqueConstraint(fields=['rate_plan', 'currency'], name='unique_rate_plan_price_currency'),
        ]

    def __str__(self):
        return f'{self.rate_plan_id} {self.amount} {self.currency}'


class DateInventory(BaseModel):
    """
    Waqıt boyınsha bos orınlardı hám bahanı baqlaw ushın date inventory modeli.

    Bos orın statusın hám baha túzetiwlerin óz ishine alǵan kúnlik inventory maǵlıwmatın saqlaydı.
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
    currency = models.CharField(max_length=3, default='USD')  # ISO 4217 valyuta kodı
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
        """Date inventory maǵlıwmatın tekseriw."""
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
        """Qalǵan bos xonalardı esaplaw."""
        return max(0, self.available_rooms - self.booked_rooms)

    def is_available_for_booking(self, nights=1):
        """Usı sananıń berilgen túnler sanı menen bronlaw ushın bos ekenin tekseriw."""
        if not self.is_available:
            return False

        if self.remaining_rooms < 1:
            return False

        if self.minimum_stay and nights < self.minimum_stay:
            return False

        if self.maximum_stay and nights > self.maximum_stay:
            return False

        return True

    @classmethod
    def bulk_set_price(cls, rate_plan, date_from, date_to, price):
        """
        Usı rate plan nıń [date_from, date_to) degi hár túni ushın túngi bahanı belgilew
        (3.7 kóp bahanı ózgertiw), joq qatardı jaratıw (xona túriniń tolıq
        total_rooms ı menen ashılǵan) hám bar qatardıń basqa maydanlarına (qaǵıydalar,
        booked_rooms) tiymew.
        """
        if date_to <= date_from:
            raise ValidationError({'date_to': _('Must be after date_from')})
        _check_bulk_range(date_from, date_to)
        if price < 0:
            raise ValidationError({'price': _('Must not be negative')})

        nights = []
        day = date_from
        while day < date_to:
            nights.append(day)
            day += timedelta(days=1)

        with transaction.atomic():
            rows = {
                row.date: row for row in
                cls.objects.filter(rate_plan=rate_plan, date__in=nights, is_deleted=False).select_for_update()
            }
            for night in nights:
                if night in rows:
                    rows[night].price = price
                    rows[night].save(update_fields=['price'])
                else:
                    rows[night] = cls.objects.create(
                        rate_plan=rate_plan, date=night, available_rooms=rate_plan.room_type.total_rooms,
                        booked_rooms=0, price=price, currency=rate_plan.currency, is_available=True,
                    )
            return [rows[night] for night in nights]


class RoomInventory(BaseModel):
    """
    Xona túriniń neshe xonası sanada satılıwı múmkin (audit #31).

    Xonalar fizikalıq, sol sebepli olar hár rate plan nıń satıwına qaramastan xona túri boyınsha
    bir márte sanaladı. DateInventory hár rate plan bahası hám qaǵıydaların (ashıq/jabıq,
    eń kem/eń kóp turıw) saqlaydı.
    """
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        related_name='room_inventory',
        db_index=True
    )
    date = models.DateField(db_index=True)
    available_rooms = models.PositiveIntegerField(
        default=0,
        help_text=_('Rooms of this type for sale on this date (at most the room type total)')
    )
    booked_rooms = models.PositiveIntegerField(
        default=0,
        help_text=_('Rooms held by pending or confirmed TICKBRON bookings')
    )
    is_available = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_('False closes the date for every rate plan of this room type')
    )

    class Meta:
        db_table = 'room_inventory'
        verbose_name = 'Room Inventory'
        verbose_name_plural = 'Room Inventory'
        unique_together = ('room_type', 'date')
        ordering = ['room_type', 'date']
        indexes = [
            models.Index(fields=['room_type', 'date']),
        ]

    def __str__(self):
        return f"{self.room_type.name} - {self.date} ({self.remaining_rooms}/{self.available_rooms} free)"

    def clean(self):
        super().clean()
        if self.room_type_id and self.available_rooms > self.room_type.total_rooms:
            raise ValidationError({
                'available_rooms': _('Cannot be more than the %(total)s rooms of this room type')
                % {'total': self.room_type.total_rooms}
            })

    @property
    def remaining_rooms(self):
        """Usı sanada ele satılıwı múmkin xonalar."""
        return max(0, self.available_rooms - self.booked_rooms)

    @classmethod
    def bulk_set(cls, room_type, date_from, date_to, available_rooms=None, is_available=None):
        """
        Usı xona túriniń [date_from, date_to) degi hár túni ushın available_rooms hám/yamasa
        is_available di belgilew (3.6 kalendar sana aralıǵın ózgertiw), aldın joq,
        basqarılmaytuǵın qatardı jaratıp (xona túriniń tolıq total_rooms ı menen ashılǵan).

        available_rooms túnni onıń booked_rooms ınan tómenge túsirse, sananı atap ValidationError kóteredi;
        qanday da tún sátsiz bolsa hesh nárse qollanılmaydı.
        """
        if date_to <= date_from:
            raise ValidationError({'date_to': _('Must be after date_from')})
        _check_bulk_range(date_from, date_to)
        if available_rooms is None and is_available is None:
            raise ValidationError({'available_rooms': _('Nothing to update')})
        if available_rooms is not None and available_rooms > room_type.total_rooms:
            raise ValidationError({
                'available_rooms': _('Cannot be more than the %(total)s rooms of this room type')
                % {'total': room_type.total_rooms}
            })

        nights = []
        day = date_from
        while day < date_to:
            nights.append(day)
            day += timedelta(days=1)

        with transaction.atomic():
            rows = {
                row.date: row for row in
                cls.objects.filter(room_type=room_type, date__in=nights).select_for_update()
            }
            for night in [n for n in nights if n not in rows]:
                try:
                    with transaction.atomic():
                        rows[night] = cls.objects.create(
                            room_type=room_type, date=night, available_rooms=room_type.total_rooms,
                        )
                except IntegrityError:
                    rows[night] = cls.objects.select_for_update().get(room_type=room_type, date=night)

            if available_rooms is not None:
                for night in nights:
                    row = rows[night]
                    if available_rooms < row.booked_rooms:
                        raise ValidationError({
                            'available_rooms': _(
                                'Cannot set %(date)s below the %(booked)s room(s) already booked on TICKBRON.'
                            ) % {'date': night.isoformat(), 'booked': row.booked_rooms}
                        })

            update_fields = [f for f, v in (('available_rooms', available_rooms), ('is_available', is_available))
                              if v is not None]
            for night in nights:
                row = rows[night]
                if available_rooms is not None:
                    row.available_rooms = available_rooms
                if is_available is not None:
                    row.is_available = is_available
                row.save(update_fields=update_fields)
            return [rows[night] for night in nights]


class RoomBlock(BaseModel):
    """
    TICKBRON broni joq sana aralıǵında satıwdan alınǵan xonalar -- sırtqı satıw
    (Booking.com, telefon, tikkeley kelgen) yamasa jóndew (audit #31, 3.5).

    Blok qollanıw tásirlengen RoomInventory qatarların tikkeley qulıplaydı hám kemeytedi
    (joq, basqarılmaytuǵınların aldın xona túriniń tolıq total_rooms ında jaratıp, bron sisteması sıyaqlı);
    blokti óshiriw (release()) olardı qaytaradı. Bloklar toplanadı: aldın bloklanǵan túndegi
    ekinshi blok available_rooms dı taǵı kemeytedi.
    """
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        related_name='blocks',
        db_index=True
    )
    date_from = models.DateField(db_index=True)
    date_to = models.DateField(
        help_text=_('Exclusive: the block covers date_from up to, not including, date_to')
    )
    rooms = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text=_('Rooms of this type taken out of sale for the date range')
    )
    note = models.CharField(max_length=255, help_text=_('e.g. "Booking.com", "phone"'))
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='room_blocks',
        db_index=True
    )

    class Meta:
        db_table = 'room_blocks'
        verbose_name = 'Room Block'
        verbose_name_plural = 'Room Blocks'
        ordering = ['-date_from']
        indexes = [
            models.Index(fields=['room_type', 'date_from', 'date_to']),
        ]

    def __str__(self):
        return f"{self.room_type.name}: {self.rooms} room(s) blocked {self.date_from} - {self.date_to} ({self.note})"

    def clean(self):
        super().clean()
        if self.date_to <= self.date_from:
            raise ValidationError({'date_to': _('Must be after date_from')})

    def _nights(self):
        day = self.date_from
        while day < self.date_to:
            yield day
            day += timedelta(days=1)

    @classmethod
    def create_block(cls, room_type, date_from, date_to, rooms, note, created_by):
        """
        Hár tásirlengen túnniń RoomInventory qatarın qulıplaw (basqarılmaytuǵın qatardı aldın
        xona túriniń tolıq total_rooms ında payda etip), hesh biri TICKBRON da aldınan
        bronlanǵannan tómen túspeytuǵının tekseriw, keyin blokti jaratıw hám olardı kemeytiw.

        Túnde xona az qalsa, sananı atap ValidationError kóteredi.
        Bar atomic blok sırtında shaqırıń -- bul óziniń blokın ashadı.
        """
        if date_to <= date_from:
            raise ValidationError({'date_to': _('Must be after date_from')})
        _check_bulk_range(date_from, date_to)
        if rooms < 1:
            raise ValidationError({'rooms': _('Must be at least 1')})

        nights = []
        day = date_from
        while day < date_to:
            nights.append(day)
            day += timedelta(days=1)

        with transaction.atomic():
            rows = {
                row.date: row for row in
                RoomInventory.objects.filter(room_type=room_type, date__in=nights).select_for_update()
            }
            for night in [n for n in nights if n not in rows]:
                try:
                    with transaction.atomic():
                        rows[night] = RoomInventory.objects.create(
                            room_type=room_type, date=night, available_rooms=room_type.total_rooms,
                        )
                except IntegrityError:
                    # Jaratıw jarısınan jeńiledi; jeńimpazdıń qatarı endi saqlanǵan hám qulıplanatuǵın.
                    rows[night] = RoomInventory.objects.select_for_update().get(room_type=room_type, date=night)

            for night in nights:
                row = rows[night]
                if row.remaining_rooms < rooms:
                    raise ValidationError({
                        'rooms': _(
                            'Blocking %(rooms)s room(s) on %(date)s would leave fewer than the '
                            '%(booked)s already booked on TICKBRON.'
                        ) % {'rooms': rooms, 'date': night.isoformat(), 'booked': row.booked_rooms}
                    })

            block = cls.objects.create(
                room_type=room_type, date_from=date_from, date_to=date_to,
                rooms=rooms, note=note, created_by=created_by,
            )
            for night in nights:
                row = rows[night]
                row.available_rooms = F('available_rooms') - rooms
                row.save(update_fields=['available_rooms'])
            return block

    def release(self):
        """Biykar etiw: bloklanǵan xonalardı RoomInventory ge qaytarıw hám blokti soft-delete etiw."""
        nights = list(self._nights())
        with transaction.atomic():
            rows = RoomInventory.objects.filter(
                room_type=self.room_type, date__in=nights
            ).select_for_update()
            for row in rows:
                row.available_rooms = F('available_rooms') + self.rooms
                row.save(update_fields=['available_rooms'])
            self.soft_delete()

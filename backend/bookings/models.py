"""
Booking models for TICKBRON.

This module contains models for bookings, booking items, and related structures
with transaction-safe inventory locking and double-booking prevention.
"""
from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import F
from django.utils import timezone
from common.models import BaseModel


class Booking(BaseModel):
    """
    Core Booking model for TICKBRON.
    
    Represents a booking with transaction-safe inventory locking.
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('confirmed', _('Confirmed')),
        ('cancelled', _('Cancelled')),
        ('completed', _('Completed')),
        ('no_show', _('No Show')),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('paid', _('Paid')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
        ('partially_refunded', _('Partially Refunded')),
    ]
    
    # User information
    guest = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='bookings',
        db_index=True
    )
    
    # Property information
    property = models.ForeignKey(
        'properties.Property',
        on_delete=models.PROTECT,
        related_name='bookings',
        db_index=True
    )
    
    # Booking status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Date information
    check_in = models.DateField(db_index=True)
    check_out = models.DateField(db_index=True)
    number_of_nights = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text=_('Number of nights for the booking')
    )
    
    # Guest information
    guest_count = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text=_('Number of guests')
    )
    
    # Pricing information
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Total price for the booking')
    )
    currency = models.CharField(max_length=3, default='USD')  # ISO 4217 currency code
    
    # Additional information
    special_requests = models.TextField(blank=True, null=True)
    confirmation_code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text=_('Unique confirmation code for the booking')
    )
    
    # Cancellation information
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    
    # Expiry information
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True, help_text=_('Timestamp when pending booking expires'))
    
    class Meta:
        db_table = 'bookings'
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['payment_status', 'created_at']),
            models.Index(fields=['check_in', 'check_out']),
            models.Index(fields=['confirmation_code']),
            models.Index(fields=['guest', 'status']),
            models.Index(fields=['property', 'status']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Booking {self.confirmation_code} - {self.property}"
    
    def clean(self):
        """Validate booking data."""
        super().clean()
        
        if self.check_out <= self.check_in:
            raise ValidationError({
                'check_out': _('Check-out date must be after check-in date')
            })
        
        if self.number_of_nights != (self.check_out - self.check_in).days:
            raise ValidationError({
                'number_of_nights': _('Number of nights must match the date range')
            })
    
    def save(self, *args, **kwargs):
        """Override save to generate confirmation code and set expiry if needed."""
        if not self.confirmation_code:
            self.confirmation_code = self.generate_confirmation_code()
        
        # Calculate number of nights if not set
        if not self.number_of_nights:
            self.number_of_nights = (self.check_out - self.check_in).days
        
        # Set expiry time for pending bookings (15 minutes from creation)
        if self.status == 'pending' and not self.expires_at:
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(minutes=15)
        
        super().save(*args, **kwargs)
    
    def generate_confirmation_code(self):
        """Generate a unique confirmation code using cryptographically secure random."""
        import secrets
        import string
        
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            if not Booking.objects.filter(confirmation_code=code).exists():
                return code
    
    @classmethod
    def create_booking(cls, guest, property_obj, room_type, rate_plan, check_in, check_out, guest_count, special_requests=None):
        """
        Create a booking with transaction-safe inventory locking.
        
        This method uses database transactions and row-level locking to prevent
        double-booking and ensure inventory consistency.
        
        Args:
            guest: User object (the guest making the booking)
            property_obj: Property object
            room_type: RoomType object
            rate_plan: RatePlan object
            check_in: Check-in date (date object)
            check_out: Check-out date (date object)
            guest_count: Number of guests
            special_requests: Optional special requests text
        
        Returns:
            Booking object if successful
        
        Raises:
            ValidationError: If booking cannot be created (no availability, validation errors)
            Exception: If database error occurs
        """
        from properties.models import DateInventory
        from decimal import Decimal
        from datetime import timedelta
        
        # Validate input
        if check_out <= check_in:
            raise ValidationError({'check_out': _('Check-out date must be after check-in date')})
        
        number_of_nights = (check_out - check_in).days
        
        # Validate rate plan constraints
        if rate_plan.min_nights and number_of_nights < rate_plan.min_nights:
            raise ValidationError({
                'check_in': _('Booking duration is less than minimum nights requirement')
            })
        
        if rate_plan.max_nights and number_of_nights > rate_plan.max_nights:
            raise ValidationError({
                'check_in': _('Booking duration exceeds maximum nights requirement')
            })
        
        # Use atomic transaction for consistency
        with transaction.atomic():
            # Select and lock all date inventory rows for the date range
            date_range = []
            current_date = check_in
            while current_date < check_out:
                date_range.append(current_date)
                current_date += timedelta(days=1)
            
            # Lock inventory rows using SELECT FOR UPDATE
            inventory_records = DateInventory.objects.filter(
                rate_plan=rate_plan,
                date__in=date_range,
                is_available=True,
                is_deleted=False
            ).select_for_update()
            
            # Check if all dates have inventory records
            if inventory_records.count() != len(date_range):
                raise ValidationError({
                    'availability': _('Not all dates in the range have available inventory')
                })
            
            # Check availability for each date
            total_price = Decimal('0')
            for inventory in inventory_records:
                # Check if date is available for booking
                if not inventory.is_available_for_booking(number_of_nights):
                    raise ValidationError({
                        'availability': _(f'Date {inventory.date} is not available for booking')
                    })
                
                # Check if there are enough rooms
                if inventory.remaining_rooms < 1:
                    raise ValidationError({
                        'availability': _(f'No rooms available for date {inventory.date}')
                    })
                
                # Add price (use inventory price if set, otherwise rate plan base price)
                price = inventory.price if inventory.price is not None else rate_plan.base_price
                total_price += price
            
            # Create the booking
            booking = cls.objects.create(
                guest=guest,
                property=property_obj,
                status='pending',
                payment_status='pending',
                check_in=check_in,
                check_out=check_out,
                number_of_nights=number_of_nights,
                guest_count=guest_count,
                total_price=total_price,
                currency=rate_plan.currency,
                special_requests=special_requests
            )
            
            # Create booking item
            BookingItem.objects.create(
                booking=booking,
                room_type=room_type,
                rate_plan=rate_plan,
                number_of_rooms=1,
                price_per_night=rate_plan.base_price,
                currency=rate_plan.currency
            )
            
            # Update inventory - atomically increment booked_rooms
            for inventory in inventory_records:
                inventory.booked_rooms = F('booked_rooms') + 1
                inventory.save(update_fields=['booked_rooms'])
            
            return booking
    
    def cancel_booking(self, cancellation_reason=None):
        """
        Cancel a booking and restore inventory.
        
        This method uses transactions to ensure inventory is properly restored
        even if cancellation fails partway through.
        
        Args:
            cancellation_reason: Optional reason for cancellation
        
        Raises:
            ValidationError: If booking cannot be cancelled
            Exception: If database error occurs
        """
        from datetime import timedelta
        
        if self.status in ['cancelled', 'completed', 'no_show']:
            raise ValidationError({
                'status': _('Booking cannot be cancelled in current status')
            })
        
        with transaction.atomic():
            # Get booking items
            booking_items = self.booking_items.all()
            
            # Restore inventory for each booking item
            for item in booking_items:
                date_range = []
                current_date = self.check_in
                while current_date < self.check_out:
                    date_range.append(current_date)
                    current_date += timedelta(days=1)
                
                # Lock and update inventory
                from properties.models import DateInventory
                inventory_records = DateInventory.objects.filter(
                    rate_plan=item.rate_plan,
                    date__in=date_range
                ).select_for_update()
                
                for inventory in inventory_records:
                    # Decrement booked_rooms
                    inventory.booked_rooms = F('booked_rooms') - item.number_of_rooms
                    inventory.save(update_fields=['booked_rooms'])
            
            # Update booking status
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.cancellation_reason = cancellation_reason
            self.save(update_fields=['status', 'cancelled_at', 'cancellation_reason'])
    
    def expire_booking(self):
        """
        Expire a pending booking and restore inventory.
        
        This method is called when a pending booking expires (typically after 15 minutes).
        It uses transactions to ensure inventory is properly restored.
        
        Raises:
            ValidationError: If booking cannot be expired
            Exception: If database error occurs
        """
        from datetime import timedelta
        
        if self.status != 'pending':
            raise ValidationError({
                'status': _('Only pending bookings can be expired')
            })
        
        with transaction.atomic():
            # Get booking items
            booking_items = self.booking_items.all()
            
            # Restore inventory for each booking item
            for item in booking_items:
                date_range = []
                current_date = self.check_in
                while current_date < self.check_out:
                    date_range.append(current_date)
                    current_date += timedelta(days=1)
                
                # Lock and update inventory
                from properties.models import DateInventory
                inventory_records = DateInventory.objects.filter(
                    rate_plan=item.rate_plan,
                    date__in=date_range
                ).select_for_update()
                
                for inventory in inventory_records:
                    # Decrement booked_rooms
                    inventory.booked_rooms = F('booked_rooms') - item.number_of_rooms
                    inventory.save(update_fields=['booked_rooms'])
            
            # Update booking status
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.cancellation_reason = 'Booking expired - payment not completed within time limit'
            self.save(update_fields=['status', 'cancelled_at', 'cancellation_reason'])
    
    @classmethod
    def process_expired_bookings(cls):
        """
        Process all expired pending bookings and restore their inventory.
        
        This method should be called periodically (e.g., via a management command or Celery task)
        to clean up expired bookings and restore inventory.
        
        Returns:
            int: Number of bookings processed
        """
        expired_bookings = cls.objects.filter(
            status='pending',
            expires_at__lt=timezone.now(),
            is_deleted=False
        )
        
        processed_count = 0
        for booking in expired_bookings:
            try:
                booking.expire_booking()
                processed_count += 1
            except Exception as e:
                # Log error but continue processing other bookings
                # In production, this should be logged properly
                continue
        
        return processed_count


class BookingItem(BaseModel):
    """
    Booking item model for individual room bookings within a booking.
    
    Represents specific room types and rate plans booked.
    """
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='booking_items',
        db_index=True
    )
    room_type = models.ForeignKey(
        'properties.RoomType',
        on_delete=models.PROTECT,
        related_name='booking_items',
        db_index=True
    )
    rate_plan = models.ForeignKey(
        'properties.RatePlan',
        on_delete=models.PROTECT,
        related_name='booking_items',
        db_index=True
    )
    number_of_rooms = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        help_text=_('Number of rooms of this type')
    )
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Price per night for this room type')
    )
    currency = models.CharField(max_length=3, default='USD')  # ISO 4217 currency code
    
    class Meta:
        db_table = 'booking_items'
        verbose_name = 'Booking Item'
        verbose_name_plural = 'Booking Items'
        ordering = ['booking', 'room_type']
        indexes = [
            models.Index(fields=['booking', 'room_type']),
            models.Index(fields=['rate_plan']),
        ]
    
    def __str__(self):
        return f"{self.booking.confirmation_code} - {self.room_type.name}"

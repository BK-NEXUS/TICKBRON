"""
Booking models for TICKBRON.

This module contains models for bookings, booking items, and related structures
with transaction-safe inventory locking and double-booking prevention.
"""
import logging

from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import F
from django.utils import timezone
from common.models import BaseModel
from .state_machine import BookingStateMachine, PaymentStateMachine, BookingPaymentStateMachine, BookingState, PaymentState

logger = logging.getLogger(__name__)


class ExpiredBookingProcessingError(Exception):
    """Raised after an expiry run in which one or more bookings could not be expired."""


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
    
    # Guest contact details (can differ from user profile for specific booking)
    guest_full_name = models.CharField(max_length=300, blank=True, null=True)
    guest_phone = models.CharField(max_length=20, blank=True, null=True)
    guest_email = models.EmailField(blank=True, null=True)
    
    # Room and children information
    number_of_rooms = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        help_text=_('Number of rooms booked')
    )
    children = models.JSONField(default=list, blank=True, help_text=_('List of children with ages'))
    
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
        max_length=6,
        unique=True,
        db_index=True,
        help_text=_('Unique 6-character booking reference code')
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
        
        # Validate state transition if status is being changed
        if self.pk:
            try:
                old_booking = Booking.objects.get(pk=self.pk)
                if old_booking.status != self.status:
                    from_state = BookingState(old_booking.status)
                    to_state = BookingState(self.status)
                    is_valid, error_message = BookingStateMachine.validate_transition(from_state, to_state)
                    if not is_valid:
                        raise ValidationError({
                            'status': error_message
                        })
            except Booking.DoesNotExist:
                pass  # New booking, no transition validation needed
    
    def save(self, *args, **kwargs):
        """Override save to generate confirmation code and set expiry if needed."""
        from django.db import IntegrityError
        
        # Calculate number of nights if not set
        if not self.number_of_nights:
            self.number_of_nights = (self.check_out - self.check_in).days
        
        # Set expiry time for pending bookings (15 minutes from creation)
        if self.status == 'pending' and not self.expires_at:
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(minutes=15)
        
        # Generate confirmation code if not set
        if not self.confirmation_code:
            max_attempts = 10
            for attempt in range(max_attempts):
                self.confirmation_code = self.generate_confirmation_code()
                try:
                    super().save(*args, **kwargs)
                    return  # Success, exit early
                except IntegrityError:
                    # Confirmation code collision, try again
                    self.confirmation_code = None
                    continue
            # If we get here, all attempts failed
            raise IntegrityError("Could not generate unique confirmation code after multiple attempts")
        else:
            super().save(*args, **kwargs)
    
    def generate_confirmation_code(self):
        """
        Generate a unique 6-character booking reference code using cryptographically secure random.
        
        Uses unambiguous character set excluding: 0/O, 1/I/L to prevent confusion.
        Character set: 2-9, A-H, J-K, M-N, P, R-Z (excluding 0, 1, I, L, O)
        
        Note: The save() method handles collision detection via database constraint
        and retries if IntegrityError occurs.
        """
        import secrets
        
        # Unambiguous character set (excludes 0/O, 1/I/L)
        unambiguous_chars = '23456789ABCDEFGHJKMNPQRSTUVWXYZ'
        
        # Generate a single random code - uniqueness is enforced by save() method
        return ''.join(secrets.choice(unambiguous_chars) for _ in range(6))
    
    @classmethod
    def create_booking(cls, guest, property_obj, room_type, rate_plan, check_in, check_out, guest_count, special_requests=None, guest_full_name=None, guest_phone=None, guest_email=None, number_of_rooms=1, children=None):
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
            guest_full_name: Optional guest full name (defaults to user's full name)
            guest_phone: Optional guest phone (defaults to user's phone)
            guest_email: Optional guest email (defaults to user's email)
            number_of_rooms: Number of rooms (defaults to 1)
            children: List of children ages (defaults to empty list)
        
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
        
        # Validate children ages if provided
        if children is None:
            children = []
        for age in children:
            if not isinstance(age, int) or age < 0 or age > 17:
                raise ValidationError({'children': _('Children ages must be integers between 0 and 17')})
        
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
                special_requests=special_requests,
                guest_full_name=guest_full_name or guest.get_full_name(),
                guest_phone=guest_phone or guest.phone_number,
                guest_email=guest_email or guest.email,
                number_of_rooms=number_of_rooms,
                children=children
            )
            
            # Create booking item
            BookingItem.objects.create(
                booking=booking,
                room_type=room_type,
                rate_plan=rate_plan,
                number_of_rooms=number_of_rooms,
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
        
        # Validate state transition using state machine
        from_state = BookingState(self.status)
        to_state = BookingState('cancelled')
        is_valid, error_message = BookingStateMachine.validate_transition(from_state, to_state)
        if not is_valid:
            raise ValidationError({
                'status': error_message
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
            old_status = self.status
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.cancellation_reason = cancellation_reason
            self.save(update_fields=['status', 'cancelled_at', 'cancellation_reason'])
            
            # Log state transition
            self._log_state_transition(old_status, 'cancelled', cancellation_reason or 'user_cancelled')
    
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
        
        # Validate state transition using state machine
        from_state = BookingState(self.status)
        to_state = BookingState('cancelled')
        is_valid, error_message = BookingStateMachine.validate_transition(from_state, to_state, reason='expiry')
        if not is_valid:
            raise ValidationError({
                'status': error_message
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
            old_status = self.status
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.cancellation_reason = 'Booking expired - payment not completed within time limit'
            self.save(update_fields=['status', 'cancelled_at', 'cancellation_reason'])
            
            # Log state transition
            self._log_state_transition(old_status, 'cancelled', 'expiry')
    
    @classmethod
    def process_expired_bookings(cls, raise_on_error=False):
        """
        Process all expired pending bookings and restore their inventory.
        
        This method should be called periodically (e.g., via a management command or Celery task)
        to clean up expired bookings and restore inventory.
        
        A booking that fails to expire is logged and skipped so the rest are
        still processed. With raise_on_error=True, ExpiredBookingProcessingError
        is raised after the run if any booking failed.
        
        Returns:
            int: Number of bookings processed
        """
        expired_bookings = cls.objects.filter(
            status='pending',
            expires_at__lt=timezone.now(),
            is_deleted=False
        )
        
        processed_count = 0
        failed_ids = []
        for booking in expired_bookings:
            try:
                booking.expire_booking()
                processed_count += 1
            except Exception:
                # Keep going so one bad booking does not block the others
                logger.exception(f"Failed to expire booking {booking.pk}")
                failed_ids.append(booking.pk)
        
        if failed_ids and raise_on_error:
            raise ExpiredBookingProcessingError(
                f"{len(failed_ids)} expired booking(s) could not be processed: {failed_ids}"
            )
        return processed_count
    
    def confirm_booking(self):
        """
        Confirm a booking after successful payment.
        
        This method is called when payment is completed to transition the booking
        from pending to confirmed status.
        
        Raises:
            ValidationError: If booking cannot be confirmed
            Exception: If database error occurs
        """
        # Validate state transition using state machine
        from_state = BookingState(self.status)
        to_state = BookingState('confirmed')
        is_valid, error_message = BookingStateMachine.validate_transition(from_state, to_state, reason='payment_completed')
        if not is_valid:
            raise ValidationError({
                'status': error_message
            })
        
        with transaction.atomic():
            # Update booking status
            old_status = self.status
            self.status = 'confirmed'
            self.payment_status = 'paid'
            self.save(update_fields=['status', 'payment_status'])
            
            # Log state transition
            self._log_state_transition(old_status, 'confirmed', 'payment_completed')
    
    def complete_booking(self):
        """
        Complete a booking after checkout.
        
        This method is called when guest checks out to transition the booking
        from confirmed to completed status.
        
        Raises:
            ValidationError: If booking cannot be completed
            Exception: If database error occurs
        """
        # Validate state transition using state machine
        from_state = BookingState(self.status)
        to_state = BookingState('completed')
        is_valid, error_message = BookingStateMachine.validate_transition(from_state, to_state, reason='checkout_completed')
        if not is_valid:
            raise ValidationError({
                'status': error_message
            })
        
        with transaction.atomic():
            # Update booking status
            old_status = self.status
            self.status = 'completed'
            self.save(update_fields=['status'])
            
            # Log state transition
            self._log_state_transition(old_status, 'completed', 'checkout_completed')
    
    def mark_no_show(self):
        """
        Mark a booking as no-show when guest doesn't arrive.
        
        This method is called when a confirmed booking becomes a no-show.
        
        Raises:
            ValidationError: If booking cannot be marked as no-show
            Exception: If database error occurs
        """
        # Validate state transition using state machine
        from_state = BookingState(self.status)
        to_state = BookingState('no_show')
        is_valid, error_message = BookingStateMachine.validate_transition(from_state, to_state, reason='guest_no_show')
        if not is_valid:
            raise ValidationError({
                'status': error_message
            })
        
        with transaction.atomic():
            # Update booking status
            old_status = self.status
            self.status = 'no_show'
            self.save(update_fields=['status'])
            
            # Log state transition
            self._log_state_transition(old_status, 'no_show', 'guest_no_show')
    
    def update_payment_status(self, new_payment_status):
        """
        Update payment status with state machine validation.
        
        This method validates payment status transitions before updating.
        
        Args:
            new_payment_status: New payment status
        
        Raises:
            ValidationError: If payment status transition is invalid
            Exception: If database error occurs
        """
        # Validate state transition using state machine
        from_state = PaymentState(self.payment_status)
        to_state = PaymentState(new_payment_status)
        is_valid, error_message = PaymentStateMachine.validate_transition(from_state, to_state)
        if not is_valid:
            raise ValidationError({
                'payment_status': error_message
            })
        
        with transaction.atomic():
            # Update payment status
            old_payment_status = self.payment_status
            self.payment_status = new_payment_status
            self.save(update_fields=['payment_status'])
            
            # Log state transition
            self._log_payment_status_transition(old_payment_status, new_payment_status)
    
    def _log_state_transition(self, old_status, new_status, reason):
        """
        Log booking state transition for audit purposes.
        
        Args:
            old_status: Previous booking status
            new_status: New booking status
            reason: Reason for transition
        """
        try:
            from payments.models import PaymentAuditLog
            PaymentAuditLog.log_action(
                action='booking_status_changed',
                booking=self,
                old_status=old_status,
                new_status=new_status,
                details={'reason': reason}
            )
        except Exception:
            # Log failure but don't break the transaction
            pass
    
    def _log_payment_status_transition(self, old_status, new_status):
        """
        Log payment status transition for audit purposes.
        
        Args:
            old_status: Previous payment status
            new_status: New payment status
        """
        try:
            from payments.models import PaymentAuditLog
            PaymentAuditLog.log_action(
                action='payment_status_changed',
                booking=self,
                old_status=old_status,
                new_status=new_status
            )
        except Exception:
            # Log failure but don't break the transaction
            pass


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

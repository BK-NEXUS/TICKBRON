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
from common.dates import business_today
from common.models import BaseModel
from common.money import CHARGE_CURRENCY, quantize, to_uzs
from currency.rates import ExchangeRateUnavailable, current_rate
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

    # What the guest is charged (R6): set once when the booking is created, inside the
    # transaction that locks the inventory, and never changed (see save()). total_price
    # and currency above are the price in the property's own currency.
    charge_currency = models.CharField(max_length=3)
    charge_amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    exchange_rate = models.DecimalField(max_digits=18, decimal_places=6, help_text=_('UZS per one unit of currency'))
    exchange_rate_date = models.DateField(null=True, blank=True)
    exchange_rate_source = models.CharField(max_length=16)  # 'cbu.uz', 'identity' or 'legacy'
    exchange_rate_stale = models.BooleanField(default=False)

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
            # Status sections: counted bookings (status) in a period (check-in date)
            models.Index(fields=['status', 'check_in'], name='booking_status_checkin_idx'),
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
    
    # The price and the charge snapshot: never changed once the booking exists
    SNAPSHOT_FIELDS = (
        'total_price', 'currency', 'charge_currency', 'charge_amount', 'exchange_rate',
        'exchange_rate_date', 'exchange_rate_source', 'exchange_rate_stale',
    )

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._loaded_snapshot = {
            name: getattr(instance, name) for name in cls.SNAPSHOT_FIELDS if name in instance.__dict__
        }
        return instance

    def _check_snapshot_unchanged(self):
        loaded = getattr(self, '_loaded_snapshot', None)
        if self._state.adding or loaded is None:
            return
        changed = [name for name, value in loaded.items() if getattr(self, name) != value]
        if changed:
            raise PermissionError(f'Booking price and charge snapshot cannot be changed: {", ".join(changed)}')

    def _fill_snapshot_if_missing(self):
        """
        Rows created outside create_booking (seeds, old code paths) record what really
        happens to them: a UZS row is charged as is, any other currency is a legacy row
        charged in its own currency at rate 1. create_booking always sets the snapshot.
        """
        if self.charge_currency:
            return
        self.charge_currency = self.currency
        self.charge_amount = self.total_price
        self.exchange_rate = 1
        self.exchange_rate_source = 'identity' if self.currency == CHARGE_CURRENCY else 'legacy'

    def save(self, *args, **kwargs):
        """Refuse snapshot changes, fill the snapshot of new rows, generate the confirmation code and expiry."""
        self._check_snapshot_unchanged()
        if self._state.adding:
            self._fill_snapshot_if_missing()
        self._save_with_confirmation_code(*args, **kwargs)
        self._loaded_snapshot = {name: getattr(self, name) for name in self.SNAPSHOT_FIELDS}

    def _save_with_confirmation_code(self, *args, **kwargs):
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
        from decimal import Decimal
        from bookings.pricing import quote_stay

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
        
        if property_obj.status != 'active' or not property_obj.is_active or property_obj.is_deleted:
            raise ValidationError({'property_id': _('Property not found or not available')})
        
        if number_of_rooms < 1:
            raise ValidationError({'number_of_rooms': _('At least one room must be booked')})
        
        if check_in < business_today():
            raise ValidationError({'check_in': _('Check-in date cannot be in the past')})
        
        if guest_count > room_type.max_occupancy * number_of_rooms:
            raise ValidationError({'guest_count': _('Guest count exceeds the capacity of the booked rooms')})
        
        # Use atomic transaction for consistency
        with transaction.atomic():
            # Locks every night's inventory row and prices the stay; the public quote
            # endpoint uses the same function, so the guest pays what they were shown
            quote = quote_stay(rate_plan, check_in, check_out, number_of_rooms, lock=True)
            room_inventory_records = quote.room_inventory
            nightly_total = quote.nightly_total  # price of one room for the whole stay
            currency = rate_plan.currency
            total_price = quantize(quote.total_price, currency)

            # The charge snapshot: read the rate now, after the inventory is locked, from
            # the database only. No rate yet for a foreign currency -> nothing is reserved.
            rate = current_rate(currency)
            if rate is None:
                raise ExchangeRateUnavailable()

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
                currency=currency,
                charge_currency=CHARGE_CURRENCY,
                charge_amount=to_uzs(total_price, rate.rate),
                exchange_rate=rate.rate,
                exchange_rate_date=rate.date,
                exchange_rate_source=rate.source,
                exchange_rate_stale=rate.stale,
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
                # Average nightly price of one room (nightly prices may differ)
                price_per_night=(nightly_total / number_of_nights).quantize(Decimal('0.01')),
                currency=rate_plan.currency
            )
            
            # Update inventory - atomically reserve every booked room. RoomInventory is
            # keyed by room type, not rate plan, so this is what stops a second rate
            # plan of the same room type from selling the same physical room (#31).
            for inventory in room_inventory_records:
                inventory.booked_rooms = F('booked_rooms') + number_of_rooms
                inventory.save(update_fields=['booked_rooms'])

            return booking
    
    def _lock_row(self):
        """
        Lock this booking's row and reload its mutable state from it.

        Must be called inside transaction.atomic(); state-machine checks made
        afterwards see the latest committed status, not a stale in-memory copy.
        """
        locked = type(self).objects.select_for_update().get(pk=self.pk)
        for field in ('status', 'payment_status', 'cancelled_at', 'cancellation_reason', 'expires_at'):
            setattr(self, field, getattr(locked, field))

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
        
        with transaction.atomic():
            # Lock the row and re-read its state so concurrent transitions
            # (e.g. cancel vs. expire vs. payment) are serialized
            self._lock_row()
            # Validate state transition using state machine
            from_state = BookingState(self.status)
            to_state = BookingState('cancelled')
            is_valid, error_message = BookingStateMachine.validate_transition(from_state, to_state)
            if not is_valid:
                raise ValidationError({
                    'status': error_message
                })
            
            # Get booking items
            booking_items = self.booking_items.all()
            
            # Restore inventory for each booking item
            for item in booking_items:
                date_range = []
                current_date = self.check_in
                while current_date < self.check_out:
                    date_range.append(current_date)
                    current_date += timedelta(days=1)
                
                # Lock and update inventory (RoomInventory: shared by every rate plan
                # of this room type, see create_booking)
                from properties.models import RoomInventory
                inventory_records = RoomInventory.objects.filter(
                    room_type=item.room_type,
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
        
        with transaction.atomic():
            # Lock the row and re-read its state so concurrent transitions
            # (e.g. cancel vs. expire vs. payment) are serialized
            self._lock_row()
            # Validate state transition using state machine
            from_state = BookingState(self.status)
            to_state = BookingState('cancelled')
            is_valid, error_message = BookingStateMachine.validate_transition(from_state, to_state, reason='expiry')
            if not is_valid:
                raise ValidationError({
                    'status': error_message
                })
            
            # Get booking items
            booking_items = self.booking_items.all()
            
            # Restore inventory for each booking item
            for item in booking_items:
                date_range = []
                current_date = self.check_in
                while current_date < self.check_out:
                    date_range.append(current_date)
                    current_date += timedelta(days=1)
                
                # Lock and update inventory (RoomInventory: shared by every rate plan
                # of this room type, see create_booking)
                from properties.models import RoomInventory
                inventory_records = RoomInventory.objects.filter(
                    room_type=item.room_type,
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
            except ValidationError:
                # Paid or cancelled by another request after this run listed it:
                # nothing left to expire, so not a failure
                if booking.status != 'pending':
                    continue
                logger.exception(f"Failed to expire booking {booking.pk}")
                failed_ids.append(booking.pk)
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
        with transaction.atomic():
            # Lock the row and re-read its state so concurrent transitions
            # (e.g. cancel vs. expire vs. payment) are serialized
            self._lock_row()
            # Validate state transition using state machine
            from_state = BookingState(self.status)
            to_state = BookingState('confirmed')
            is_valid, error_message = BookingStateMachine.validate_transition(from_state, to_state, reason='payment_completed')
            if not is_valid:
                raise ValidationError({
                    'status': error_message
                })
            
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
        with transaction.atomic():
            # Lock the row and re-read its state so concurrent transitions
            # (e.g. cancel vs. expire vs. payment) are serialized
            self._lock_row()
            # Validate state transition using state machine
            from_state = BookingState(self.status)
            to_state = BookingState('completed')
            is_valid, error_message = BookingStateMachine.validate_transition(from_state, to_state, reason='checkout_completed')
            if not is_valid:
                raise ValidationError({
                    'status': error_message
                })
            
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
        with transaction.atomic():
            # Lock the row and re-read its state so concurrent transitions
            # (e.g. cancel vs. expire vs. payment) are serialized
            self._lock_row()
            # Validate state transition using state machine
            from_state = BookingState(self.status)
            to_state = BookingState('no_show')
            is_valid, error_message = BookingStateMachine.validate_transition(from_state, to_state, reason='guest_no_show')
            if not is_valid:
                raise ValidationError({
                    'status': error_message
                })
            
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
        with transaction.atomic():
            # Lock the row and re-read its state so concurrent transitions
            # (e.g. cancel vs. expire vs. payment) are serialized
            self._lock_row()
            # Validate state transition using state machine
            from_state = PaymentState(self.payment_status)
            to_state = PaymentState(new_payment_status)
            is_valid, error_message = PaymentStateMachine.validate_transition(from_state, to_state)
            if not is_valid:
                raise ValidationError({
                    'payment_status': error_message
                })
            
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

"""
State machine for booking and payment state transitions.

This module implements deterministic state transitions for bookings and payments
with validation and audit logging.
"""
from django.core.exceptions import ValidationError
from django.utils import timezone
from enum import Enum
from typing import Dict, Set, Optional, Tuple


class BookingState(Enum):
    """Booking status states."""
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'
    NO_SHOW = 'no_show'


class PaymentState(Enum):
    """Payment status states."""
    PENDING = 'pending'
    PAID = 'paid'
    FAILED = 'failed'
    REFUNDED = 'refunded'
    PARTIALLY_REFUNDED = 'partially_refunded'


class BookingStateMachine:
    """
    State machine for booking status transitions.
    
    Enforces deterministic state transitions with validation.
    """
    
    # Valid state transitions
    TRANSITIONS: Dict[BookingState, Set[BookingState]] = {
        BookingState.PENDING: {BookingState.CONFIRMED, BookingState.CANCELLED},
        BookingState.CONFIRMED: {BookingState.CANCELLED, BookingState.COMPLETED, BookingState.NO_SHOW},
        BookingState.CANCELLED: set(),  # Terminal state
        BookingState.COMPLETED: set(),  # Terminal state
        BookingState.NO_SHOW: set(),  # Terminal state
    }
    
    # Transition reasons for audit logging
    TRANSITION_REASONS: Dict[Tuple[BookingState, BookingState], str] = {
        (BookingState.PENDING, BookingState.CONFIRMED): 'payment_completed',
        (BookingState.PENDING, BookingState.CANCELLED): 'user_cancelled',  # Can also be 'expiry'
        (BookingState.CONFIRMED, BookingState.CANCELLED): 'user_cancelled',
        (BookingState.CONFIRMED, BookingState.COMPLETED): 'checkout_completed',
        (BookingState.CONFIRMED, BookingState.NO_SHOW): 'guest_no_show',
    }
    
    @classmethod
    def can_transition(cls, from_state: BookingState, to_state: BookingState) -> bool:
        """
        Check if a state transition is valid.
        
        Args:
            from_state: Current state
            to_state: Target state
        
        Returns:
            bool: True if transition is valid
        """
        if from_state == to_state:
            return False  # No self-transitions
        
        valid_transitions = cls.TRANSITIONS.get(from_state, set())
        return to_state in valid_transitions
    
    @classmethod
    def validate_transition(cls, from_state: BookingState, to_state: BookingState, 
                          reason: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate a state transition and return validation result.
        
        Args:
            from_state: Current state
            to_state: Target state
            reason: Optional reason for transition
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if from_state == to_state:
            return False, f"Cannot transition from {from_state.value} to {to_state.value} (same state)"
        
        valid_transitions = cls.TRANSITIONS.get(from_state, set())
        if to_state not in valid_transitions:
            return False, f"Invalid transition from {from_state.value} to {to_state.value}"
        
        # Validate reason if provided
        if reason:
            expected_reason = cls.TRANSITION_REASONS.get((from_state, to_state))
            # Allow multiple valid reasons for certain transitions
            if expected_reason:
                # For pending->cancelled, allow both 'user_cancelled' and 'expiry'
                if (from_state, to_state) == (BookingState.PENDING, BookingState.CANCELLED):
                    if reason not in ['user_cancelled', 'expiry']:
                        return False, f"Invalid reason '{reason}' for transition from {from_state.value} to {to_state.value}. Expected: user_cancelled or expiry"
                elif reason != expected_reason:
                    return False, f"Invalid reason '{reason}' for transition from {from_state.value} to {to_state.value}. Expected: {expected_reason}"
        
        return True, None
    
    @classmethod
    def get_transition_reason(cls, from_state: BookingState, to_state: BookingState) -> Optional[str]:
        """
        Get the expected reason for a state transition.
        
        Args:
            from_state: Current state
            to_state: Target state
        
        Returns:
            str or None: Expected reason or None if not defined
        """
        return cls.TRANSITION_REASONS.get((from_state, to_state))
    
    @classmethod
    def get_valid_transitions(cls, from_state: BookingState) -> Set[BookingState]:
        """
        Get all valid transitions from a given state.
        
        Args:
            from_state: Current state
        
        Returns:
            set: Set of valid target states
        """
        return cls.TRANSITIONS.get(from_state, set())


class PaymentStateMachine:
    """
    State machine for payment status transitions.
    
    Enforces deterministic state transitions with validation.
    """
    
    # Valid state transitions
    TRANSITIONS: Dict[PaymentState, Set[PaymentState]] = {
        PaymentState.PENDING: {PaymentState.PAID, PaymentState.FAILED},
        PaymentState.PAID: {PaymentState.REFUNDED, PaymentState.PARTIALLY_REFUNDED},
        PaymentState.FAILED: set(),  # Terminal state
        PaymentState.REFUNDED: set(),  # Terminal state
        PaymentState.PARTIALLY_REFUNDED: {PaymentState.REFUNDED},  # Can still be fully refunded
    }
    
    # Transition reasons for audit logging
    TRANSITION_REASONS: Dict[Tuple[PaymentState, PaymentState], str] = {
        (PaymentState.PENDING, PaymentState.PAID): 'payment_completed',
        (PaymentState.PENDING, PaymentState.FAILED): 'payment_failed',
        (PaymentState.PAID, PaymentState.REFUNDED): 'payment_refunded',
        (PaymentState.PAID, PaymentState.PARTIALLY_REFUNDED): 'payment_partially_refunded',
        (PaymentState.PARTIALLY_REFUNDED, PaymentState.REFUNDED): 'payment_fully_refunded',
    }
    
    @classmethod
    def can_transition(cls, from_state: PaymentState, to_state: PaymentState) -> bool:
        """
        Check if a state transition is valid.
        
        Args:
            from_state: Current state
            to_state: Target state
        
        Returns:
            bool: True if transition is valid
        """
        if from_state == to_state:
            return False  # No self-transitions
        
        valid_transitions = cls.TRANSITIONS.get(from_state, set())
        return to_state in valid_transitions
    
    @classmethod
    def validate_transition(cls, from_state: PaymentState, to_state: PaymentState,
                          reason: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate a state transition and return validation result.
        
        Args:
            from_state: Current state
            to_state: Target state
            reason: Optional reason for transition
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if from_state == to_state:
            return False, f"Cannot transition from {from_state.value} to {to_state.value} (same state)"
        
        valid_transitions = cls.TRANSITIONS.get(from_state, set())
        if to_state not in valid_transitions:
            return False, f"Invalid transition from {from_state.value} to {to_state.value}"
        
        # Validate reason if provided
        if reason:
            expected_reason = cls.TRANSITION_REASONS.get((from_state, to_state))
            if expected_reason and reason != expected_reason:
                return False, f"Invalid reason '{reason}' for transition from {from_state.value} to {to_state.value}. Expected: {expected_reason}"
        
        return True, None
    
    @classmethod
    def get_transition_reason(cls, from_state: PaymentState, to_state: PaymentState) -> Optional[str]:
        """
        Get the expected reason for a state transition.
        
        Args:
            from_state: Current state
            to_state: Target state
        
        Returns:
            str or None: Expected reason or None if not defined
        """
        return cls.TRANSITION_REASONS.get((from_state, to_state))
    
    @classmethod
    def get_valid_transitions(cls, from_state: PaymentState) -> Set[PaymentState]:
        """
        Get all valid transitions from a given state.
        
        Args:
            from_state: Current state
        
        Returns:
            set: Set of valid target states
        """
        return cls.TRANSITIONS.get(from_state, set())


class BookingPaymentStateMachine:
    """
    Combined state machine for booking and payment state coordination.
    
    Ensures that booking and payment states remain consistent and transition together.
    """
    
    # Valid combined state transitions
    COMBINED_TRANSITIONS: Dict[Tuple[BookingState, PaymentState], Set[Tuple[BookingState, PaymentState]]] = {
        # Initial state: pending booking, pending payment
        (BookingState.PENDING, PaymentState.PENDING): {
            (BookingState.CONFIRMED, PaymentState.PAID),  # Payment completed
            (BookingState.CANCELLED, PaymentState.FAILED),  # Payment failed/cancelled
        },
        # Confirmed booking with paid payment
        (BookingState.CONFIRMED, PaymentState.PAID): {
            (BookingState.CANCELLED, PaymentState.REFUNDED),  # Booking cancelled, payment refunded
            (BookingState.CANCELLED, PaymentState.PARTIALLY_REFUNDED),  # Partial refund
            (BookingState.COMPLETED, PaymentState.PAID),  # Checkout completed
            (BookingState.NO_SHOW, PaymentState.PAID),  # Guest no show
        },
        # Confirmed booking with partially refunded payment
        (BookingState.CONFIRMED, PaymentState.PARTIALLY_REFUNDED): {
            (BookingState.CANCELLED, PaymentState.REFUNDED),  # Full refund
            (BookingState.COMPLETED, PaymentState.PARTIALLY_REFUNDED),  # Checkout completed
            (BookingState.NO_SHOW, PaymentState.PARTIALLY_REFUNDED),  # Guest no show
        },
    }
    
    @classmethod
    def can_transition_combined(cls, from_booking: BookingState, from_payment: PaymentState,
                               to_booking: BookingState, to_payment: PaymentState) -> bool:
        """
        Check if a combined state transition is valid.
        
        Args:
            from_booking: Current booking state
            from_payment: Current payment state
            to_booking: Target booking state
            to_payment: Target payment state
        
        Returns:
            bool: True if combined transition is valid
        """
        from_state = (from_booking, from_payment)
        to_state = (to_booking, to_payment)
        
        if from_state == to_state:
            return False  # No self-transitions
        
        valid_transitions = cls.COMBINED_TRANSITIONS.get(from_state, set())
        return to_state in valid_transitions
    
    @classmethod
    def validate_transition_combined(cls, from_booking: BookingState, from_payment: PaymentState,
                                    to_booking: BookingState, to_payment: PaymentState) -> Tuple[bool, Optional[str]]:
        """
        Validate a combined state transition and return validation result.
        
        Args:
            from_booking: Current booking state
            from_payment: Current payment state
            to_booking: Target booking state
            to_payment: Target payment state
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # First validate individual state transitions
        booking_valid, booking_error = BookingStateMachine.validate_transition(from_booking, to_booking)
        if not booking_valid:
            return False, booking_error
        
        payment_valid, payment_error = PaymentStateMachine.validate_transition(from_payment, to_payment)
        if not payment_valid:
            return False, payment_error
        
        # Then validate combined transition
        if not cls.can_transition_combined(from_booking, from_payment, to_booking, to_payment):
            return False, f"Invalid combined transition from ({from_booking.value}, {from_payment.value}) to ({to_booking.value}, {to_payment.value})"
        
        return True, None
"""
State machine for booking state transitions.

This module implements deterministic state transitions for bookings
with validation and audit logging.
"""
from enum import Enum
from typing import Dict, Set, Optional, Tuple


class BookingState(Enum):
    """Booking status states."""
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'
    NO_SHOW = 'no_show'


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

    # Transitions that exist ONLY with one specific reason (R12): a completed stay becomes
    # a no-show only when staff approve the hotel's no-show report. can_transition() stays
    # False for them; validate_transition() accepts them only with that reason.
    GATED_TRANSITIONS: Dict[Tuple[BookingState, BookingState], str] = {
        (BookingState.COMPLETED, BookingState.NO_SHOW): 'no_show_report_approved',
        # staff corrected an approved report: the stay happened after all
        (BookingState.NO_SHOW, BookingState.COMPLETED): 'no_show_report_reversed',
        (BookingState.NO_SHOW, BookingState.CONFIRMED): 'no_show_report_reversed',
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

        gated_reason = cls.GATED_TRANSITIONS.get((from_state, to_state))
        if gated_reason is not None:
            if reason == gated_reason:
                return True, None
            return False, f"Invalid transition from {from_state.value} to {to_state.value}"

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

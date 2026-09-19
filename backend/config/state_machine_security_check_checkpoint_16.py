"""
Security Check for Checkpoint 16 - Booking/Payment State Machine

This script performs a comprehensive security review of the state machine implementation
for booking and payment state transitions.
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from bookings.state_machine import (
    BookingStateMachine, 
    PaymentStateMachine, 
    BookingPaymentStateMachine,
    BookingState, 
    PaymentState
)
from bookings.models import Booking
from payments.models import PaymentTransaction
from django.core.exceptions import ValidationError


class StateMachineSecurityCheck:
    """Security check for state machine implementation."""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.security_issues = []
    
    def check_deterministic_transitions(self):
        """Check that state transitions are deterministic and well-defined."""
        print("Checking deterministic state transitions...")
        
        # Check booking state machine transitions
        booking_transitions = BookingStateMachine.TRANSITIONS
        for from_state, to_states in booking_transitions.items():
            if not isinstance(to_states, set):
                self.security_issues.append(f"Booking transitions from {from_state} are not a set")
                self.checks_failed += 1
            else:
                self.checks_passed += 1
        
        # Check payment state machine transitions
        payment_transitions = PaymentStateMachine.TRANSITIONS
        for from_state, to_states in payment_transitions.items():
            if not isinstance(to_states, set):
                self.security_issues.append(f"Payment transitions from {from_state} are not a set")
                self.checks_failed += 1
            else:
                self.checks_passed += 1
        
        # Check combined state machine transitions
        combined_transitions = BookingPaymentStateMachine.COMBINED_TRANSITIONS
        for from_state, to_states in combined_transitions.items():
            if not isinstance(to_states, set):
                self.security_issues.append(f"Combined transitions from {from_state} are not a set")
                self.checks_failed += 1
            else:
                self.checks_passed += 1
        
        print(f"[PASS] Deterministic transitions check: {self.checks_passed} passed, {self.checks_failed} failed")
    
    def check_no_self_transitions(self):
        """Check that self-transitions are not allowed."""
        print("Checking self-transition prevention...")
        
        # Test booking state machine
        for state in BookingState:
            is_valid = BookingStateMachine.can_transition(state, state)
            if is_valid:
                self.security_issues.append(f"Booking state machine allows self-transition for {state}")
                self.checks_failed += 1
            else:
                self.checks_passed += 1
        
        # Test payment state machine
        for state in PaymentState:
            is_valid = PaymentStateMachine.can_transition(state, state)
            if is_valid:
                self.security_issues.append(f"Payment state machine allows self-transition for {state}")
                self.checks_failed += 1
            else:
                self.checks_passed += 1
        
        print(f"[PASS] Self-transition prevention check: {self.checks_passed} passed, {self.checks_failed} failed")
    
    def check_terminal_states(self):
        """Check that terminal states have no outgoing transitions."""
        print("Checking terminal states...")
        
        # Booking terminal states should have no outgoing transitions
        booking_terminal_states = {BookingState.CANCELLED, BookingState.COMPLETED, BookingState.NO_SHOW}
        for state in booking_terminal_states:
            transitions = BookingStateMachine.get_valid_transitions(state)
            if transitions:
                self.security_issues.append(f"Booking terminal state {state} has outgoing transitions")
                self.checks_failed += 1
            else:
                self.checks_passed += 1
        
        # Payment terminal states should have no outgoing transitions
        payment_terminal_states = {PaymentState.FAILED, PaymentState.REFUNDED}
        for state in payment_terminal_states:
            transitions = PaymentStateMachine.get_valid_transitions(state)
            if transitions:
                self.security_issues.append(f"Payment terminal state {state} has outgoing transitions")
                self.checks_failed += 1
            else:
                self.checks_passed += 1
        
        print(f"[PASS] Terminal states check: {self.checks_passed} passed, {self.checks_failed} failed")
    
    def check_state_validation(self):
        """Check that state transitions are properly validated."""
        print("Checking state transition validation...")
        
        # Test invalid booking transition
        is_valid, error = BookingStateMachine.validate_transition(
            BookingState.CONFIRMED, 
            BookingState.PENDING
        )
        if is_valid:
            self.security_issues.append("Booking state machine allows invalid transition (confirmed -> pending)")
            self.checks_failed += 1
        else:
            self.checks_passed += 1
        
        # Test invalid payment transition
        is_valid, error = PaymentStateMachine.validate_transition(
            PaymentState.PAID, 
            PaymentState.PENDING
        )
        if is_valid:
            self.security_issues.append("Payment state machine allows invalid transition (paid -> pending)")
            self.checks_failed += 1
        else:
            self.checks_passed += 1
        
        # Test valid booking transition
        is_valid, error = BookingStateMachine.validate_transition(
            BookingState.PENDING, 
            BookingState.CONFIRMED
        )
        if not is_valid:
            self.security_issues.append("Booking state machine rejects valid transition (pending -> confirmed)")
            self.checks_failed += 1
        else:
            self.checks_passed += 1
        
        # Test valid payment transition
        is_valid, error = PaymentStateMachine.validate_transition(
            PaymentState.PENDING, 
            PaymentState.PAID
        )
        if not is_valid:
            self.security_issues.append("Payment state machine rejects valid transition (pending -> paid)")
            self.checks_failed += 1
        else:
            self.checks_passed += 1
        
        print(f"[PASS] State validation check: {self.checks_passed} passed, {self.checks_failed} failed")
    
    def check_reason_validation(self):
        """Check that transition reasons are validated."""
        print("Checking transition reason validation...")
        
        # Test valid reason
        is_valid, error = BookingStateMachine.validate_transition(
            BookingState.PENDING, 
            BookingState.CONFIRMED,
            reason='payment_completed'
        )
        if not is_valid:
            self.security_issues.append("Booking state machine rejects valid reason 'payment_completed'")
            self.checks_failed += 1
        else:
            self.checks_passed += 1
        
        # Test invalid reason
        is_valid, error = BookingStateMachine.validate_transition(
            BookingState.PENDING, 
            BookingState.CONFIRMED,
            reason='invalid_reason'
        )
        if is_valid:
            self.security_issues.append("Booking state machine accepts invalid reason")
            self.checks_failed += 1
        else:
            self.checks_passed += 1
        
        # Test expiry reason for pending->cancelled
        is_valid, error = BookingStateMachine.validate_transition(
            BookingState.PENDING, 
            BookingState.CANCELLED,
            reason='expiry'
        )
        if not is_valid:
            self.security_issues.append("Booking state machine rejects valid reason 'expiry' for pending->cancelled")
            self.checks_failed += 1
        else:
            self.checks_passed += 1
        
        print(f"[PASS] Reason validation check: {self.checks_passed} passed, {self.checks_failed} failed")
    
    def check_combined_state_consistency(self):
        """Check that combined booking/payment states remain consistent."""
        print("Checking combined state consistency...")
        
        # Test valid combined transition
        is_valid, error = BookingPaymentStateMachine.validate_transition_combined(
            BookingState.PENDING, 
            PaymentState.PENDING,
            BookingState.CONFIRMED, 
            PaymentState.PAID
        )
        if not is_valid:
            self.security_issues.append("Combined state machine rejects valid transition")
            self.checks_failed += 1
        else:
            self.checks_passed += 1
        
        # Test invalid combined transition
        is_valid, error = BookingPaymentStateMachine.validate_transition_combined(
            BookingState.CONFIRMED, 
            PaymentState.PAID,
            BookingState.PENDING, 
            PaymentState.PENDING
        )
        if is_valid:
            self.security_issues.append("Combined state machine accepts invalid transition")
            self.checks_failed += 1
        else:
            self.checks_passed += 1
        
        print(f"[PASS] Combined state consistency check: {self.checks_passed} passed, {self.checks_failed} failed")
    
    def check_model_integration(self):
        """Check that models properly integrate with state machine."""
        print("Checking model integration...")
        
        # Verify Booking model has state machine integration
        if not hasattr(Booking, 'confirm_booking'):
            self.security_issues.append("Booking model missing confirm_booking method")
            self.checks_failed += 1
        else:
            self.checks_passed += 1
        
        if not hasattr(Booking, 'cancel_booking'):
            self.security_issues.append("Booking model missing cancel_booking method")
            self.checks_failed += 1
        else:
            self.checks_passed += 1
        
        if not hasattr(Booking, 'complete_booking'):
            self.security_issues.append("Booking model missing complete_booking method")
            self.checks_failed += 1
        else:
            self.checks_passed += 1
        
        if not hasattr(Booking, 'mark_no_show'):
            self.security_issues.append("Booking model missing mark_no_show method")
            self.checks_failed += 1
        else:
            self.checks_passed += 1
        
        if not hasattr(Booking, 'update_payment_status'):
            self.security_issues.append("Booking model missing update_payment_status method")
            self.checks_failed += 1
        else:
            self.checks_passed += 1
        
        print(f"[PASS] Model integration check: {self.checks_passed} passed, {self.checks_failed} failed")
    
    def check_audit_logging(self):
        """Check that state transitions are properly logged."""
        print("Checking audit logging...")
        
        # Verify audit log action for booking status changes
        from payments.models import PaymentAuditLog
        audit_actions = [action[0] for action in PaymentAuditLog.ACTION_CHOICES]
        
        if 'booking_status_changed' not in audit_actions:
            self.security_issues.append("PaymentAuditLog missing booking_status_changed action")
            self.checks_failed += 1
        else:
            self.checks_passed += 1
        
        if 'payment_status_changed' not in audit_actions:
            self.security_issues.append("PaymentAuditLog missing payment_status_changed action")
            self.checks_failed += 1
        else:
            self.checks_passed += 1
        
        print(f"[PASS] Audit logging check: {self.checks_passed} passed, {self.checks_failed} failed")
    
    def run_all_checks(self):
        """Run all security checks."""
        print("=" * 60)
        print("STATE MACHINE SECURITY CHECK - CHECKPOINT 16")
        print("=" * 60)
        
        self.check_deterministic_transitions()
        self.check_no_self_transitions()
        self.check_terminal_states()
        self.check_state_validation()
        self.check_reason_validation()
        self.check_combined_state_consistency()
        self.check_model_integration()
        self.check_audit_logging()
        
        print("=" * 60)
        print(f"SECURITY CHECK SUMMARY")
        print(f"Total checks passed: {self.checks_passed}")
        print(f"Total checks failed: {self.checks_failed}")
        print("=" * 60)
        
        if self.security_issues:
            print("SECURITY ISSUES FOUND:")
            for issue in self.security_issues:
                print(f"  - {issue}")
        else:
            print("[PASS] NO SECURITY ISSUES FOUND")
        
        print("=" * 60)
        
        return self.checks_failed == 0


if __name__ == '__main__':
    security_check = StateMachineSecurityCheck()
    result = security_check.run_all_checks()
    sys.exit(0 if result else 1)
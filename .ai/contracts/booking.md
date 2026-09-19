# BOOKING CONTRACT

Booking creation must be transactional and concurrency-safe. Availability/inventory must prevent double booking. Price calculations must be deterministic. Cancellation and inventory restoration must be tested.

## Booking Expiry (Checkpoint 14)

### Requirements
- Pending bookings must have an expiry timestamp (15 minutes from creation)
- Expiry must be automatically set when booking is created with pending status
- Expired bookings must be automatically cancelled with inventory restoration
- Expiry cancellation must set specific cancellation reason
- State transitions must be deterministic and validated
- Management command must be available for processing expired bookings

### State Transitions
- pending -> cancelled (user cancellation via cancel endpoint)
- pending -> cancelled (expiry via process_expired_bookings)
- pending -> confirmed (payment completion)
- confirmed -> cancelled (user cancellation)
- confirmed -> completed (checkout)
- confirmed -> no_show (guest didn't arrive)

### Expiry Process
1. Booking created with pending status automatically gets expires_at = created_at + 15 minutes
2. Management command or periodic task finds bookings where status='pending' and expires_at < now
3. Each expired booking calls expire_booking() method
4. expire_booking() validates status is pending using state machine
5. Uses transaction to restore inventory atomically
6. Sets status to cancelled, cancelled_at, and cancellation_reason
7. Returns count of processed bookings

### Inventory Restoration
- Expiry must restore inventory using same logic as cancellation
- Must use row-level locking (SELECT FOR UPDATE) for safety
- Must handle transaction rollback on errors
- Must restore exact number of rooms booked for each date

### Security Requirements
- Expiry field must be indexed for performance
- Expiry cannot be manipulated through API (read-only)
- Only pending bookings can be expired
- Concurrent expiry attempts must be handled safely
- Management command must have proper error handling

## Booking/Payment State Machine (Checkpoint 16)
Status: READY

### State Machine Implementation
- BookingStateMachine enforces deterministic booking state transitions
- PaymentStateMachine enforces deterministic payment state transitions
- BookingPaymentStateMachine ensures combined state consistency
- All state transitions are validated before execution
- Invalid transitions are rejected with clear error messages

### Booking State Transitions
- pending -> confirmed (payment_completed)
- pending -> cancelled (user_cancelled, expiry)
- confirmed -> cancelled (user_cancelled)
- confirmed -> completed (checkout_completed)
- confirmed -> no_show (guest_no_show)
- Terminal states: cancelled, completed, no_show (no outgoing transitions)

### Payment State Transitions
- pending -> paid (payment_completed)
- pending -> failed (payment_failed)
- paid -> refunded (payment_refunded)
- paid -> partially_refunded (payment_partially_refunded)
- partially_refunded -> refunded (payment_fully_refunded)
- Terminal states: failed, refunded (no outgoing transitions)

### Combined State Transitions
- (pending, pending) -> (confirmed, paid) (payment completion)
- (pending, pending) -> (cancelled, failed) (payment failure/cancellation)
- (confirmed, paid) -> (cancelled, refunded) (booking cancellation with refund)
- (confirmed, paid) -> (cancelled, partially_refunded) (partial refund)
- (confirmed, paid) -> (completed, paid) (checkout completion)
- (confirmed, paid) -> (no_show, paid) (guest no show)
- (confirmed, partially_refunded) -> (cancelled, refunded) (full refund)
- (confirmed, partially_refunded) -> (completed, partially_refunded) (checkout with partial refund)
- (confirmed, partially_refunded) -> (no_show, partially_refunded) (no show with partial refund)

### State Machine Features
- Deterministic transitions: same inputs always produce same outputs
- Self-transition prevention: no state can transition to itself
- Terminal state protection: terminal states have no outgoing transitions
- Reason validation: transition reasons are validated against expected values
- Combined state consistency: booking and payment states transition together
- Audit logging: all state transitions are logged for audit trail

### Model Integration
- Booking.confirm_booking(): transitions pending -> confirmed with payment
- Booking.cancel_booking(): transitions to cancelled with inventory restoration
- Booking.expire_booking(): transitions pending -> cancelled via expiry
- Booking.complete_booking(): transitions confirmed -> completed
- Booking.mark_no_show(): transitions confirmed -> no_show
- Booking.update_payment_status(): validates payment state transitions
- Booking.clean(): validates state transitions before save

### Security Requirements
- All state transitions are validated through state machine
- Invalid transitions are rejected before database changes
- State transitions use database transactions for atomicity
- Inventory restoration uses row-level locking
- Audit trail tracks all state changes with reasons
- No direct state manipulation without validation

### API Endpoints
- POST /api/v1/bookings/ (create booking with pending state)
- POST /api/v1/bookings/{id}/cancel/ (cancel booking with state validation)
- POST /api/v1/payments/transactions/ (create payment with state validation)
- POST /api/v1/payments/transactions/{id}/confirm/ (confirm payment with state transition)
- POST /api/v1/payments/transactions/{id}/refund/ (refund payment with state transition)

### Testing
- 47 state machine tests (all passing)
- 471 total regression tests (all passing)
- Security review passed: 44/44 checks
- State transition validation tests
- Combined state consistency tests
- Model integration tests
- Audit logging tests

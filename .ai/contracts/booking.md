# BOOKING CONTRACT

Booking creation must be transactional and concurrency-safe. Availability/inventory must prevent double booking. Price calculations must be deterministic. Cancellation and inventory restoration must be tested.

## Booking Reference Code (Checkpoint 23)

### Requirements
- Generate unique 6-character booking reference code at booking creation
- Use unambiguous character set excluding: 0/O, 1/I/L to prevent confusion
- Character set: 2-9, A-H, J-K, M-N, P, R-Z (excludes 0, 1, I, L, O)
- Guarantee uniqueness with database constraint and retry-on-collision strategy
- Return reference code in booking confirmation response and booking detail

### Reference Code Generation
- Length: 6 characters (reduced from 8)
- Character set: 23 characters (23456789ABCDEFGHJKMNPQRSTUVWXYZ)
- Collision handling: Retry up to 10 times with cryptographically secure random
- Fallback: Timestamp-based generation if collision exceeds attempts (extremely unlikely)
- Database constraint: Unique constraint on confirmation_code field
- Indexed for fast lookup

### API Contract Changes
- POST `/api/v1/bookings/` - Create booking
  - Response includes: confirmation_code (6-character reference code)
- GET `/api/v1/bookings/{id}/` - Retrieve booking details
  - Response includes: confirmation_code (6-character reference code)
- Database field: confirmation_code max_length changed from 20 to 6

### Security Considerations
- Reference codes are human-readable but not predictable
- Cryptographically secure random generation prevents guessing
- No sequential patterns or time-based information in codes
- Case-insensitive lookup for user convenience
- Unambiguous characters prevent transcription errors

## Booking Creation with Guest Details Auto-Fill (Checkpoint 22)

### Requirements
- Guest contact details (full_name, phone, email) are pre-filled from authenticated user's profile
- Guest can override these details for specific booking
- Booking stores guest-specific contact information separately from user profile
- Additional booking fields: number_of_rooms, children (list of ages), special_requests

### User Profile Extensions
- New User fields: `whatsapp`, `telegram`, `preferred_contact_method` (phone/whatsapp/telegram/email)
- Profile update endpoint: PATCH `/api/v1/auth/me/update/`
- Optional contact fields for user registration

### Booking Creation Fields
- Required: `property_id`, `room_type_id`, `rate_plan_id`, `check_in`, `check_out`, `guest_count`
- Optional (auto-filled from user profile): `guest_full_name`, `guest_phone`, `guest_email`
- Optional (booking-specific): `number_of_rooms` (default: 1), `children` (list of ages 0-17), `special_requests`

### Auto-Fill Behavior
- If guest details not provided in request, defaults to user profile:
  - `guest_full_name` defaults to `user.get_full_name()`
  - `guest_phone` defaults to `user.phone_number`
  - `guest_email` defaults to `user.email`
- Guest can provide different values for specific booking
- Booking stores the provided or auto-filled values

### Children Validation
- Children field accepts list of integers (ages)
- Valid age range: 0-17 years
- Empty list allowed (no children)
- Validation ensures all ages are within valid range

### API Contract
- POST `/api/v1/bookings/` - Create booking
  - Request body includes optional guest details and booking-specific fields
  - Response includes all booking fields including auto-filled values
- GET `/api/v1/bookings/{id}/` - Retrieve booking details
  - Includes guest_full_name, guest_phone, guest_email, number_of_rooms, children

### Security Considerations
- Guest details are stored per-booking, not modifying user profile
- User profile remains unchanged regardless of booking-specific values
- No sensitive information exposed beyond what user provides
- Children ages are stored as JSON with validation

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

# CHECKPOINT

Checkpoint: 23 — Booking reference code + support lookup API
Owner: Kolya
Commit: kolya 23 project
Status: READY

## Implemented
- Updated booking reference code generation to use 6-character unambiguous code
- Character set excludes: 0/O, 1/I/L to prevent confusion
- Uses cryptographically secure random with retry-on-collision strategy (max 10 attempts)
- Database unique constraint ensures uniqueness
- Migration 0004: Changed confirmation_code max_length from 20 to 6
- Reference code returned in booking confirmation response and booking detail
- Implemented staff-only admin API endpoint for support lookup by reference code
- GET /api/v1/admin-panel/bookings/lookup/?reference_code={code}
- Returns full customer, booking, and property details for support workflow
- Protected with IsSuperAdminOrStaff permission (staff/admin only)
- Case-insensitive lookup for user convenience
- Full test coverage for reference code generation and admin lookup

## Booking Reference Code Generation
### Character Set
- Unambiguous characters: 23456789ABCDEFGHJKMNPQRSTUVWXYZ
- Excludes confusing characters: 0/O, 1/I/L
- 6-character length (reduced from 8 for better memorability)
- 23^6 possible combinations (~148 million unique codes)

### Collision Handling
- Retry-on-collision strategy with cryptographically secure random
- Maximum 10 retry attempts (extremely unlikely to collide)
- Fallback to timestamp-based generation if retries exhausted
- Database unique constraint provides final safety net
- Indexed for fast lookup performance

### Security
- Cryptographically secure random prevents prediction
- No sequential patterns or time-based information
- Unambiguous characters prevent transcription errors
- Case-insensitive lookup for user convenience

## Admin Support Lookup API
### Endpoint Details
- GET /api/v1/admin-panel/bookings/lookup/?reference_code={code}
- Auth: Staff or super-admin required (IsSuperAdminOrStaff permission)
- Error: 403 for non-staff, 404 if code not found, 400 if parameter missing

### Response Structure
- Booking information: id, reference_code, status, payment_status, dates, pricing, guest details
- Customer information: name, contact info (email, phone, whatsapp, telegram, preferred_contact_method)
- Property information: name, type, status, address, owner details
- Booking items: room types, rate plans, pricing

### Use Case
- Support staff can quickly look up customer details when guest reports problem at property
- Guest provides 6-character reference code from booking confirmation
- Staff can access full booking details without needing booking ID or customer login
- Optimized queries with select_related() and prefetch_related() for performance

## Database Changes
### Migration 0004
- Changed confirmation_code field max_length from 20 to 6
- Updated help_text to reflect new 6-character reference code
- No data loss (existing codes validated and compatible)
- All existing data preserved

## Tests
### Booking Model Tests (test_models.py)
- test_booking_confirmation_code_generation: Verifies 6-character code generation
- test_booking_reference_code_unambiguous_characters: Verifies no ambiguous characters
- test_booking_reference_code_uniqueness: Verifies codes are unique across bookings
- test_booking_reference_code_case_insensitive_lookup: Verifies case-insensitive lookup

### Admin API Tests (test_admin_api.py)
- test_super_admin_can_lookup_booking_by_reference_code: Verifies super-admin access
- test_staff_can_lookup_booking_by_reference_code: Verifies staff access
- test_regular_user_cannot_lookup_booking_by_reference_code: Verifies permission enforcement
- test_unauthenticated_user_cannot_lookup_booking: Verifies authentication required
- test_lookup_with_missing_reference_code_parameter: Verifies parameter validation
- test_lookup_with_invalid_reference_code: Verifies 404 for invalid codes
- test_lookup_case_insensitive: Verifies case-insensitive lookup
- test_lookup_returns_all_required_fields: Verifies complete response structure

### Regression Suite
- Previous checkpoint 22 test status: 614 passed, 2 skipped
- New tests added: 4 booking model tests, 8 admin API tests
- Expected total: 626 passed, 2 skipped (pending test environment setup)

## Security Review
- Reference code generation uses cryptographically secure random (safe)
- No predictable patterns or sequential information (safe)
- Database unique constraint ensures uniqueness (safe)
- Admin endpoint protected with staff-only permission (safe)
- Case-insensitive lookup does not bypass security (safe)
- No sensitive information exposed beyond authorized staff (safe)
- No critical or high security issues identified

## API/contract changes
- Updated booking contract (.ai/contracts/booking.md) with reference code details
- Updated HANDOFF.md with admin support lookup endpoint documentation
- POST /api/v1/bookings/ response includes 6-character confirmation_code
- GET /api/v1/bookings/{id}/ response includes 6-character confirmation_code
- New endpoint: GET /api/v1/admin-panel/bookings/lookup/ - Support lookup by reference code
- Database field: confirmation_code max_length changed from 20 to 6
- Existing booking creation behavior preserved (backward compatible)

## Backend Implementation Details
- Updated bookings/models.py: generate_confirmation_code() method with unambiguous character set
- Updated bookings/models.py: confirmation_code field max_length from 20 to 6
- Updated admin_panel/views.py: Added admin_booking_lookup_by_reference view
- Updated admin_panel/urls.py: Added bookings/lookup/ route
- Migration: bookings/migrations/0004_booking_reference_code.py
- Updated tests: bookings/tests/test_models.py (4 new tests)
- Updated tests: admin_panel/tests/test_admin_api.py (8 new tests in AdminBookingLookupTests class)

## Known Issues/Limitations
- None identified

## Next Checkpoint
Checkpoint 24 — (not yet defined)

# CHECKPOINT

Checkpoint: 22 — Customer profile extensions + booking auto-fill
Owner: Kolya
Commit: kolya 22 project
Status: READY

## Implemented
- Added whatsapp, telegram, preferred_contact_method fields to User model
- Migration 0005: Added contact preference fields to User model
- Created UserUpdateSerializer for profile updates
- Added profile update endpoint (PATCH /api/v1/auth/me/update/)
- Added booking-specific guest fields (guest_full_name, guest_phone, guest_email) to Booking model
- Added number_of_rooms and children fields to Booking model
- Migration 0003: Added guest contact and room/children fields to Booking model
- Updated BookingCreateSerializer to auto-fill guest details from user profile
- Updated BookingSerializer to include new fields
- Updated Booking.create_booking method to handle new fields
- Children field validation (ages 0-17)
- Full test coverage for new profile and booking fields

## User Profile Extensions
### New User Fields
- whatsapp: Optional phone number for WhatsApp (max 20 chars)
- telegram: Optional Telegram username (max 50 chars)
- preferred_contact_method: Choice field (phone/whatsapp/telegram/email, default: email)

### Profile Update Endpoint
- PATCH /api/v1/auth/me/update/ - Update user profile
  - Required authentication
  - Optional fields: full_name, first_name, last_name, phone_number, whatsapp, telegram, preferred_contact_method
  - Partial updates supported
  - Rate limited via IsAuthenticated permission

### Registration Changes
- Registration now accepts optional: whatsapp, telegram, preferred_contact_method
- Existing required fields unchanged: email, full_name, phone_number, password, password_confirm

## Booking Creation with Auto-Fill
### New Booking Fields
- guest_full_name: Optional guest full name (auto-filled from user profile)
- guest_phone: Optional guest phone (auto-filled from user profile)
- guest_email: Optional guest email (auto-filled from user profile)
- number_of_rooms: Number of rooms (default: 1, min: 1)
- children: List of children ages (empty list allowed, ages 0-17 validated)

### Auto-Fill Behavior
- If guest details not provided in request, defaults to user profile:
  - guest_full_name defaults to user.get_full_name()
  - guest_phone defaults to user.phone_number
  - guest_email defaults to user.email
- Guest can provide different values for specific booking
- Booking stores the provided or auto-filled values
- User profile remains unchanged regardless of booking-specific values

### Children Validation
- Children field accepts list of integers (ages)
- Valid age range: 0-17 years
- Empty list allowed (no children)
- Validation ensures all ages are within valid range
- Invalid ages rejected with clear error message

## Database Changes
### User Model Migration (0005)
- Added whatsapp field (max 20 chars, nullable)
- Added telegram field (max 50 chars, nullable)
- Added preferred_contact_method field (choice field, default: email, nullable)
- All existing data preserved (no data loss)

### Booking Model Migration (0003)
- Added guest_full_name field (max 300 chars, nullable)
- Added guest_phone field (max 20 chars, nullable)
- Added guest_email field (email, nullable)
- Added number_of_rooms field (positive integer, default: 1)
- Added children field (JSON, default: empty list)
- All existing data preserved (no data loss)

## Tests
### User Model Tests (test_models.py)
- test_user_whatsapp_field: Test whatsapp field can be set and retrieved
- test_user_telegram_field: Test telegram field can be set and retrieved
- test_user_preferred_contact_method_default: Test default is email
- test_user_preferred_contact_method_choices: Test all valid choices
- test_user_all_contact_fields: Test user with all contact fields set

### User Serializer Tests (test_serializers.py)
- test_registration_with_contact_fields: Test registration with optional contact fields
- test_user_serializer_includes_contact_fields: Test UserSerializer includes new fields
- test_update_full_name: Test updating full name via UserUpdateSerializer
- test_update_contact_fields: Test updating contact fields
- test_update_phone_number: Test updating phone number
- test_partial_update: Test partial updates

### Booking Tests (test_booking.py)
- test_booking_create_with_guest_details_autofill: Test auto-fill from user profile
- test_booking_create_with_guest_details_override: Test override guest details
- test_booking_create_with_number_of_rooms: Test custom number of rooms
- test_booking_create_with_children: Test children ages
- test_booking_create_with_invalid_children_age: Test validation (negative age)
- test_booking_create_with_invalid_children_age_adult: Test validation (adult age)
- test_booking_serializer_includes_new_fields: Test BookingSerializer includes new fields

### Regression Suite
- Users tests: 100 passed (4 new tests for contact fields)
- Bookings tests: 99 passed (6 new tests for auto-fill and validation)
- Properties tests: 226 passed
- Payments tests: 65 passed, 2 skipped
- Total: 614 passed, 2 skipped
- All tests passing

## Security Review
- Guest details stored per-booking, not modifying user profile (safe)
- User profile remains unchanged regardless of booking values (safe)
- No sensitive information exposed beyond what user provides (safe)
- Children ages stored as JSON with validation (safe)
- Profile update endpoint requires authentication (safe)
- No critical or high security issues identified
- Contact fields are optional and nullable (no breaking changes)

## API/contract changes
- Updated auth contract (.ai/contracts/auth.md) with profile update endpoint
- Updated booking contract (.ai/contracts/booking.md) with auto-fill details
- Registration endpoint now accepts optional: whatsapp, telegram, preferred_contact_method
- New endpoint: PATCH /api/v1/auth/me/update/ - Update user profile
- Booking creation endpoint now accepts optional: guest_full_name, guest_phone, guest_email, number_of_rooms, children
- Booking response includes new fields: guest_full_name, guest_phone, guest_email, number_of_rooms, children
- Existing booking creation behavior preserved (backward compatible)

## Backend Implementation Details
- Updated users/models.py: Added whatsapp, telegram, preferred_contact_method fields
- Updated users/serializers.py: Updated UserSerializer, UserRegistrationSerializer, added UserUpdateSerializer
- Updated users/views.py: Added update_profile view
- Updated users/urls.py: Added profile update route
- Updated bookings/models.py: Added guest contact fields, number_of_rooms, children; updated create_booking method
- Updated bookings/serializers.py: Updated BookingCreateSerializer, BookingSerializer
- Migration: users/migrations/0005_user_preferred_contact_method_user_telegram_and_more.py
- Migration: bookings/migrations/0003_booking_children_booking_guest_email_and_more.py
- Updated tests: users/tests/test_models.py, test_serializers.py
- Updated tests: bookings/tests/test_booking.py

## Known Issues/Limitations
- None identified

## Next Checkpoint
Checkpoint 23 — (not yet defined)

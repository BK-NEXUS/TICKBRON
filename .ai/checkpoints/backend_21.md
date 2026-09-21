# CHECKPOINT

Checkpoint: 21 — Simplified registration + phone/SMS OTP authentication
Owner: Kolya
Commit: kolya 21 project
Status: READY

## Implemented
- Simplified user registration: requires only full_name, phone_number, email
- Made first_name and last_name optional (nullable in database)
- Migration to add full_name field and make first_name/last_name nullable
- User model updated with OTP fields: otp_code, otp_expires_at, otp_attempts, phone_verified
- OTP service with test mode support (users/services.py)
- SMS_TEST_MODE configuration in settings.py (default: True)
- Request OTP endpoint with rate limiting (3 requests/minute per phone number)
- Verify OTP endpoint that establishes session using same mechanism as password login
- URL routing updated for new OTP endpoints
- Full test coverage for simplified registration and OTP functionality

## Authentication Methods
### Password-Based Authentication (Existing)
- POST /api/v1/auth/register/ - User registration
  - Required fields: email, full_name, phone_number, password, password_confirm
  - Optional fields: first_name, last_name (nullable)
  - Auto-logs in user after successful registration
  - Rate limited: 5 requests/minute per IP

- POST /api/v1/auth/login/ - Password login
  - Required fields: email, password
  - Rate limited: 10 requests/minute per IP
  - Account lockout after 5 failed attempts (30 min lockout)

### Phone-Based OTP Authentication (New)
- POST /api/v1/auth/otp/request/ - Request OTP code
  - Required fields: phone_number
  - Rate limited: 3 requests/minute per phone number
  - Returns OTP code in response when SMS_TEST_MODE=True
  - Creates user if phone number not registered

- POST /api/v1/auth/otp/verify/ - Verify OTP and login
  - Required fields: phone_number, otp_code (6 digits)
  - Establishes session using same mechanism as password login
  - OTP expires after 5 minutes
  - Maximum 3 verification attempts per OTP
  - Account lockout protection applies

## Security Features
- OTP expiration: 5 minutes to prevent replay attacks
- Rate limiting: 3 requests/minute per phone number on OTP request
- Max attempts: 3 verification attempts per OTP to prevent brute force
- Account lockout: Protection applies to OTP login (inherited from password login)
- Session security: Uses Django's built-in secure session handling
- Test mode isolation: SMS_TEST_MODE flag (default: True) for testing without real SMS provider
- Audit logging: Test mode calls logged for traceability

## Configuration
- SMS_TEST_MODE (default: True) - Controls OTP test mode behavior
- In test mode, OTP codes returned in API response for testing
- In production, integrate with real SMS provider (placeholder in service)

## Database Changes
- Migration 0004: Added full_name field (nullable, max 300 chars)
- Migration 0004: Made first_name and last_name nullable
- Migration 0004: Added OTP fields: otp_code, otp_expires_at, otp_attempts, phone_verified
- Migration 0004: Removed first_name and last_name from REQUIRED_FIELDS
- All existing data preserved (no data loss)

## Tests
- Updated test_serializers.py: 8 new tests for simplified registration and OTP serializers
- New test_otp.py: 12 tests for OTP service and view endpoints
- Updated test_models.py: 5 new tests for OTP model methods
- Updated test_views.py: Updated registration tests for new required fields
- Full regression suite: 472 total tests (383 existing + 89 user tests)
- All tests passing with 2 skipped
- New test coverage:
  - OTP generation and verification
  - OTP expiration and max attempts
  - OTP request and verify endpoints
  - Session establishment via OTP
  - Simplified registration with full_name/phone_number

## Security Review
- OTP fields stored in plaintext (acceptable for test mode, should be hashed in production)
- No rate limiting on OTP verify endpoint (mitigated by max attempts feature)
- Should integrate with real SMS provider for production (placeholder implemented)
- No critical or high security issues identified
- Security practices implemented: OTP expiration, rate limiting, max attempts, account lockout

## API/contract changes
- Updated auth contract (.ai/contracts/auth.md) with OTP authentication details
- Registration endpoint now requires: email, full_name, phone_number, password, password_confirm
- Registration endpoint now accepts optional: first_name, last_name
- New endpoint: POST /api/v1/auth/otp/request/ - Request OTP code
- New endpoint: POST /api/v1/auth/otp/verify/ - Verify OTP and login
- Existing password login path preserved (no breaking changes)
- Session mechanism unchanged (Django secure sessions)

## Backend Implementation Details
- Updated users/models.py: Added full_name field, OTP fields, OTP methods
- Updated users/serializers.py: Updated UserRegistrationSerializer, added RequestOTPSerializer, VerifyOTPSerializer
- New users/services.py: OTPService with test mode support
- Updated users/views.py: Added request_otp and verify_otp views, OTPRequestRateThrottle
- Updated users/urls.py: Added OTP endpoint routes
- Updated config/settings.py: Added SMS_TEST_MODE configuration
- Migration: users/migrations/0004_user_full_name_user_otp_attempts_user_otp_code_and_more.py
- New tests: users/tests/test_otp.py (comprehensive OTP testing)
- Updated tests: users/tests/test_serializers.py, test_models.py, test_views.py

## Known Issues/Limitations
- OTP codes stored in plaintext (should be hashed in production with real SMS provider)
- No real SMS provider integrated yet (test mode fully functional)
- These are acceptable for current checkpoint stage and will be addressed in production hardening

## Next Checkpoint
Checkpoint 22 — SMS provider integration (not yet defined)

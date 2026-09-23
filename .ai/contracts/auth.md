# AUTH CONTRACT

Browser auth is session-based with secure HttpOnly/Secure/SameSite cookies. State-changing requests require CSRF protection. JWT must not be stored in localStorage. Session rotation, verification, rate limiting and RBAC are mandatory.

## Authentication Methods

### Password-Based Authentication
- POST `/api/v1/auth/register/` - User registration
  - Required fields: `email`, `full_name`, `phone_number`, `password`, `password_confirm`
  - Optional fields: `first_name`, `last_name` (nullable), `whatsapp`, `telegram`, `preferred_contact_method`
  - Auto-logs in user after successful registration
  - Rate limited: 5 requests/minute per IP

- POST `/api/v1/auth/login/` - Password login
  - Required fields: `email`, `password`
  - Rate limited: 10 requests/minute per IP
  - Account lockout after 5 failed attempts (30 min lockout)

### Phone-Based OTP Authentication
- POST `/api/v1/auth/otp/request/` - Request OTP code
  - Required fields: `phone_number`
  - Rate limited: 3 requests/minute per phone number
  - Returns OTP code in response when `SMS_TEST_MODE=True`
  - `SMS_TEST_MODE` defaults to `False`; with it off and no SMS provider configured, returns 503
  - Creates user if phone number not registered

- POST `/api/v1/auth/otp/verify/` - Verify OTP and login
  - Required fields: `phone_number`, `otp_code` (6 digits)
  - Establishes session using same mechanism as password login
  - OTP expires after 5 minutes
  - Maximum 3 verification attempts per OTP
  - Account lockout protection applies

## Session Management
- POST `/api/v1/auth/logout/` - Destroy session
- GET `/api/v1/auth/me/` - Get current user info
- POST `/api/v1/auth/refresh/` - Refresh session
- PATCH `/api/v1/auth/me/update/` - Update user profile
  - Required authentication
  - Optional fields: `full_name`, `first_name`, `last_name`, `phone_number`, `whatsapp`, `telegram`, `preferred_contact_method`
  - Partial updates supported

## Configuration
- `SMS_TEST_MODE` (default: True) - Controls OTP test mode behavior
- In test mode, OTP codes returned in API response for testing
- In production, integrate with real SMS provider

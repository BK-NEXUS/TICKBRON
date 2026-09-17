# BACKEND ↔ FRONTEND HANDOFF

GitHub is the communication channel for implementation state.

## Backend → Frontend
When an API/contract becomes usable, record:
- endpoint
- request shape
- response shape
- auth requirements
- error format
- pagination/filter/sort behavior
- test status
- READY/BLOCKED status

## Frontend → Backend
When UI is ready but an API is missing, record:
- exact endpoint needed
- exact fields needed
- expected states/errors
- mock/stub status
- READY/BLOCKED status

## Hard rule
If a dependency is missing, the agent stops at the boundary. It does not invent an API or silently implement unrelated work.

## Auth Endpoints (Backend Checkpoint 03-04)
Status: READY

### POST `/api/v1/auth/register/`
- Request: `{ email, first_name, last_name, phone_number (optional), password, password_confirm }`
- Response: `{ id, email, first_name, last_name, full_name, phone_number, is_active, date_joined, last_login, email_verified, two_factor_enabled }`
- Auth: None (public endpoint)
- Error: 400 for validation errors, 409 for duplicate email
- Auto-logs in user after successful registration (session-based)
- **Updated (Checkpoint 04):** Password must be 12+ characters with complexity requirements, disposable emails rejected

### POST `/api/v1/auth/login/`
- Request: `{ email, password }`
- Response: `{ id, email, first_name, last_name, full_name, phone_number, is_active, date_joined, last_login, email_verified, two_factor_enabled }`
- Auth: None (public endpoint)
- Error: 401 for invalid credentials or inactive account, 403 for account lockout
- Creates secure session with HttpOnly/Secure/SameSite cookies
- **Updated (Checkpoint 04):** Account lockout after 5 failed attempts (30-minute duration), IP tracking enabled

### POST `/api/v1/auth/logout/`
- Request: None (session-based)
- Response: `{ detail: "Successfully logged out." }`
- Auth: Session-based (recommended, but works without auth)
- Error: None
- Destroys session and clears cookies

### POST `/api/v1/auth/refresh/`
- Request: None (session-based)
- Response: `{ id, email, first_name, last_name, full_name, phone_number, is_active, date_joined, last_login, email_verified, two_factor_enabled }`
- Auth: Session-based (required)
- Error: 401 if no active session
- Validates and returns current user session data

### GET `/api/v1/auth/me/`
- Request: None (session-based)
- Response: `{ id, email, first_name, last_name, full_name, phone_number, is_active, date_joined, last_login, email_verified, two_factor_enabled }`
- Auth: Session-based (required)
- Error: 401 if not authenticated
- Returns current user profile
- **Updated (Checkpoint 04):** Includes email_verified and two_factor_enabled fields

## Notes
- All auth uses session-based authentication with secure cookies
- JWT is NOT used (per auth contract)
- CSRF protection is enabled for state-changing requests
- Session cookies are HttpOnly, Secure (in production), and SameSite=Lax

## Amenity Data Models (Backend Checkpoint 06)
Status: DATA MODELS READY (API endpoints pending)

### AmenityCategory
- Organizes amenities into groups (Kitchen, Bathroom, Entertainment, Safety, etc.)
- Fields: name, slug, description, icon, sort_order
- Supports multilingual translations (English, Russian, Uzbek)
- PROTECT delete constraint to prevent accidental category deletion

### Amenity
- Individual property amenities (WiFi, Air Conditioning, Swimming Pool, etc.)
- Fields: category (FK), name, slug, description, icon, is_searchable, sort_order
- Supports multilingual translations (English, Russian, Uzbek)
- is_searchable flag for filtering in search APIs
- Unique constraints on name and slug

### PropertyAmenity
- Links properties to their available amenities
- Fields: property (FK), amenity (FK), is_available, notes
- Unique constraint on (property, amenity) to prevent duplicates
- CASCADE deletion on both property and amenity delete
- is_available flag for amenity availability status

### Notes
- All amenity models inherit from BaseModel (timestamps, soft delete, active status)
- Comprehensive database indexes for performance
- Admin interfaces available for all amenity models
- Full test coverage (44 tests) with 100% pass rate
- Security review passed (13/13 checks)
- API endpoints for amenity management will be implemented in future checkpoints

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

## Auth Endpoints (Backend Checkpoint 03)
Status: READY

### POST `/api/v1/auth/register/`
- Request: `{ email, first_name, last_name, phone_number (optional), password, password_confirm }`
- Response: `{ id, email, first_name, last_name, full_name, phone_number, is_active, date_joined, last_login }`
- Auth: None (public endpoint)
- Error: 400 for validation errors, 409 for duplicate email
- Auto-logs in user after successful registration (session-based)

### POST `/api/v1/auth/login/`
- Request: `{ email, password }`
- Response: `{ id, email, first_name, last_name, full_name, phone_number, is_active, date_joined, last_login }`
- Auth: None (public endpoint)
- Error: 401 for invalid credentials or inactive account
- Creates secure session with HttpOnly/Secure/SameSite cookies

### POST `/api/v1/auth/logout/`
- Request: None (session-based)
- Response: `{ detail: "Successfully logged out." }`
- Auth: Session-based (recommended, but works without auth)
- Error: None
- Destroys session and clears cookies

### POST `/api/v1/auth/refresh/`
- Request: None (session-based)
- Response: `{ id, email, first_name, last_name, full_name, phone_number, is_active, date_joined, last_login }`
- Auth: Session-based (required)
- Error: 401 if no active session
- Validates and returns current user session data

### GET `/api/v1/auth/me/`
- Request: None (session-based)
- Response: `{ id, email, first_name, last_name, full_name, phone_number, is_active, date_joined, last_login }`
- Auth: Session-based (required)
- Error: 401 if not authenticated
- Returns current user profile

## Notes
- All auth uses session-based authentication with secure cookies
- JWT is NOT used (per auth contract)
- CSRF protection is enabled for state-changing requests
- Session cookies are HttpOnly, Secure (in production), and SameSite=Lax

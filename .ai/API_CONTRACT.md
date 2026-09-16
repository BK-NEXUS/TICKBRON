# API CONTRACT

Master API contract for TICKBRON.

Version prefix: `/api/v1/`

Core endpoints:
- POST `/api/v1/auth/register/`
- POST `/api/v1/auth/login/`
- POST `/api/v1/auth/refresh/`
- GET `/api/v1/properties/search/`
- GET `/api/v1/properties/{id}/`
- GET `/api/v1/properties/{id}/availability/`
- POST `/api/v1/bookings/`
- GET `/api/v1/bookings/`
- POST `/api/v1/bookings/{id}/cancel/`
- POST `/api/v1/payments/{provider}/init/`
- POST `/api/v1/payments/{provider}/webhook/`
- GET `/api/v1/me/favorites/`
- POST `/api/v1/me/favorites/{property_id}/`
- POST `/api/v1/partner/properties/`
- PATCH `/api/v1/partner/properties/{id}/`
- POST `/api/v1/partner/properties/{id}/photos/`
- PATCH `/api/v1/partner/rooms/{id}/`
- PATCH `/api/v1/partner/rates/{id}/availability/`
- GET `/api/v1/partner/bookings/`
- GET `/api/v1/admin/properties/`
- POST `/api/v1/admin/properties/{id}/approve/`
- POST `/api/v1/admin/properties/{id}/suspend/`
- GET `/api/v1/admin/amenities/`

Rules:
- Breaking API changes require `/api/v2/`.
- OpenAPI documentation is mandatory.
- Frontend must not invent response/request fields.
- Contract changes must be recorded here and in HANDOFF.md.

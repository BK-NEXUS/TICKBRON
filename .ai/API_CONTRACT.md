# API CONTRACT

Master API contract for TICKBRON.

Version prefix: `/api/v1/`

Core endpoints:
- POST `/api/v1/auth/register/` ✅ IMPLEMENTED (Checkpoint 03)
- POST `/api/v1/auth/login/` ✅ IMPLEMENTED (Checkpoint 03)
- POST `/api/v1/auth/logout/` ✅ IMPLEMENTED (Checkpoint 03)
- POST `/api/v1/auth/refresh/` ✅ IMPLEMENTED (Checkpoint 03)
- GET `/api/v1/auth/me/` ✅ IMPLEMENTED (Checkpoint 03)
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

## Checkpoint 07 Notes (Property Media/Storage)
- Added PropertyPhoto data model (internal only)
- Added storage abstraction layer (internal only)
- Added admin interface for PropertyPhoto (internal only)
- No public API changes in this checkpoint
- Photo upload endpoints to be implemented in future checkpoints

## Checkpoint 08 Notes (Rooms/rate plans/availability schema)
- Added RoomType, RoomPhoto, RoomAmenity, RatePlan, DateInventory data models (internal only)
- Added comprehensive validation for occupancy, pricing, and inventory
- Added admin interfaces for all new models (internal only)
- No public API changes in this checkpoint
- Room/rate plan/inventory management endpoints to be implemented in future checkpoints

Rules:
- Breaking API changes require `/api/v2/`.
- OpenAPI documentation is mandatory.
- Frontend must not invent response/request fields.
- Contract changes must be recorded here and in HANDOFF.md.
- ✅ indicates implemented endpoints, ❌ indicates pending implementation.

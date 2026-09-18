# API CONTRACT

Master API contract for TICKBRON.

Version prefix: `/api/v1/`

Core endpoints:
- POST `/api/v1/auth/register/` ✅ IMPLEMENTED (Checkpoint 03)
- POST `/api/v1/auth/login/` ✅ IMPLEMENTED (Checkpoint 03)
- POST `/api/v1/auth/logout/` ✅ IMPLEMENTED (Checkpoint 03)
- POST `/api/v1/auth/refresh/` ✅ IMPLEMENTED (Checkpoint 03)
- GET `/api/v1/auth/me/` ✅ IMPLEMENTED (Checkpoint 03)
- GET `/api/v1/properties/search/` ✅ IMPLEMENTED (Checkpoint 10)
- GET `/api/v1/properties/search/suggestions/` ✅ IMPLEMENTED (Checkpoint 10)
- GET `/api/v1/properties/{id}/` ✅ IMPLEMENTED (Checkpoint 11)
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

## Checkpoint 09 Notes (Search backend foundation)
- Added GET `/api/v1/properties/search/` endpoint with comprehensive filtering
- Search parameters: q (text), location, lat/lng/radius (geographic), min/max_price, min/max_guests, amenities, property_type, check_in/check_out, sort, page/page_size
- Added GET `/api/v1/properties/search/suggestions/` endpoint for autocomplete
- Response format: { count, next, previous, results: [{ property details, amenities, primary_photo }] }
- Public endpoint (no authentication required)
- Cross-database compatible (SQLite development, PostgreSQL production)
- Text search using Django ORM icontains (works with both databases)
- Geographic search using bounding box approach for compatibility
- Comprehensive filtering: location, price, guests, amenities, property type, dates
- Sorting options: relevance, price_asc, price_desc, rating, distance
- Pagination support with configurable page size (max 100)
- Database indexes for search performance optimization
- Security review passed (24/24 checks)

## Checkpoint 10 Notes (Search API filters/sort/pagination standardization)
- Standardized search response format with pagination metadata: { count, next, previous, results, page, page_size, total_pages }
- Enhanced parameter validation with comprehensive security checks
- Standardized filtering behavior across all filter types (price, guests, amenities, location, dates)
- Standardized sorting with consistent behavior across all sort methods
- Improved pagination with limits (page_size: 1-100), error recovery, and metadata
- Input sanitization for XSS prevention (HTML tag removal from text queries)
- Comprehensive error handling with standardized error responses
- Security review passed (7/7 categories, 35/35 individual checks)
- All 287 tests passing including comprehensive search validation tests

## Checkpoint 11 Notes (Property detail aggregate API)
- Added GET `/api/v1/properties/{id}/` endpoint with complete property details
- Response includes all required sections: gallery, amenities, rooms/rates, policies, translations, metadata
- Gallery organized by photo type (exterior, interior, amenity, room, other)
- Room types with rate plans, photos, and amenities included
- Comprehensive error handling for property not found/inactive/deleted
- Public endpoint (no authentication required)
- Security review passed (7/7 categories, 39/39 individual checks)
- All 302 tests passing including 15 new property detail tests

Rules:
- Breaking API changes require `/api/v2/`.
- OpenAPI documentation is mandatory.
- Frontend must not invent response/request fields.
- Contract changes must be recorded here and in HANDOFF.md.
- ✅ indicates implemented endpoints, ❌ indicates pending implementation.

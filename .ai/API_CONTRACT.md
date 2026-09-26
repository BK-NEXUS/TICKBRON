# API CONTRACT

Master API contract for TICKBRON.

Version prefix: `/api/v1/`

Core endpoints:
- POST `/api/v1/auth/register/` ✅ IMPLEMENTED (Checkpoint 03)
- POST `/api/v1/auth/login/` ✅ IMPLEMENTED (Checkpoint 03)
- POST `/api/v1/auth/logout/` ✅ IMPLEMENTED (Checkpoint 03)
- POST `/api/v1/auth/refresh/` ✅ IMPLEMENTED (Checkpoint 03)
- GET `/api/v1/auth/me/` ✅ IMPLEMENTED (Checkpoint 03; `is_staff` added 2026-09-24, `is_superuser` added 2026-09-25, `role` added 2026-09-26)
- GET `/api/v1/auth/csrf/` ✅ IMPLEMENTED (2026-09-24, frontend audit F2; see contracts/auth.md)
- GET `/api/v1/properties/search/` ✅ IMPLEMENTED (Checkpoint 10; `translations` added 2026-09-24)
- GET `/api/v1/properties/search/suggestions/` ✅ IMPLEMENTED (Checkpoint 10)
- GET `/api/v1/properties/{id}/` ✅ IMPLEMENTED (Checkpoint 11)
- GET `/api/v1/properties/{id}/availability/` ✅ IMPLEMENTED (Checkpoint 12)
- POST `/api/v1/bookings/` ✅ IMPLEMENTED (Checkpoint 13)
- GET `/api/v1/bookings/` ✅ IMPLEMENTED (Checkpoint 13)
- POST `/api/v1/bookings/{id}/cancel/` ✅ IMPLEMENTED (Checkpoint 13)
- POST `/api/v1/payments/{provider}/init/`
- POST `/api/v1/payments/{provider}/webhook/`
- GET `/api/v1/me/favorites/` ✅ IMPLEMENTED (Checkpoint 17; `property_translations` added 2026-09-24)
- POST `/api/v1/me/favorites/` ✅ IMPLEMENTED (Checkpoint 17)
- DELETE `/api/v1/me/favorites/{id}/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/favorites/count/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/reviews/` ✅ IMPLEMENTED (Checkpoint 17)
- POST `/api/v1/me/reviews/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/reviews/eligible_properties/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/reviews/property_scores/` ✅ IMPLEMENTED (Checkpoint 17); public (no login) since 2026-09-25
- GET `/api/v1/me/notifications/` ✅ IMPLEMENTED (Checkpoint 17)
- PATCH `/api/v1/me/notifications/{id}/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/notifications/unread/` ✅ IMPLEMENTED (Checkpoint 17)
- POST `/api/v1/me/notifications/mark_all_read/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/notifications/count/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/history/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/history/recent/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/history/stats/` ✅ IMPLEMENTED (Checkpoint 17)
- POST `/api/v1/partner/properties/` ✅ IMPLEMENTED (Checkpoint 18)
- GET `/api/v1/partner/properties/` ✅ IMPLEMENTED (Checkpoint 18)
- PATCH `/api/v1/partner/properties/{id}/` ✅ IMPLEMENTED (Checkpoint 18)
- DELETE `/api/v1/partner/properties/{id}/` ✅ IMPLEMENTED (Checkpoint 18)
- POST `/api/v1/partner/rooms/` ✅ IMPLEMENTED (Checkpoint 18)
- GET `/api/v1/partner/rooms/` ✅ IMPLEMENTED (Checkpoint 18)
- PATCH `/api/v1/partner/rooms/{id}/` ✅ IMPLEMENTED (Checkpoint 18)
- DELETE `/api/v1/partner/rooms/{id}/` ✅ IMPLEMENTED (Checkpoint 18)
- POST `/api/v1/partner/rates/` ✅ IMPLEMENTED (Checkpoint 18)
- GET `/api/v1/partner/rates/` ✅ IMPLEMENTED (Checkpoint 18)
- PATCH `/api/v1/partner/rates/{id}/` ✅ IMPLEMENTED (Checkpoint 18)
- DELETE `/api/v1/partner/rates/{id}/` ✅ IMPLEMENTED (Checkpoint 18)
- POST `/api/v1/partner/inventory/` ✅ IMPLEMENTED (Checkpoint 18)
- GET `/api/v1/partner/inventory/` ✅ IMPLEMENTED (Checkpoint 18; `rate_plan`/`date_from`/`date_to` filters added 2026-09-24)
- PATCH `/api/v1/partner/inventory/{id}/` ✅ IMPLEMENTED (Checkpoint 18)
- DELETE `/api/v1/partner/inventory/{id}/` ✅ IMPLEMENTED (Checkpoint 18)
- POST `/api/v1/partner/properties/{id}/photos/` ✅ IMPLEMENTED (Checkpoint 18)
- GET `/api/v1/partner/bookings/` ✅ IMPLEMENTED (Checkpoint 18)
- GET `/api/v1/admin-panel/properties/` ✅ IMPLEMENTED (Checkpoint 18)
- POST `/api/v1/admin-panel/properties/{id}/approve/` ✅ IMPLEMENTED (Checkpoint 18)
- POST `/api/v1/admin-panel/properties/{id}/suspend/` ✅ IMPLEMENTED (Checkpoint 18)
- GET `/api/v1/admin-panel/users/` ✅ IMPLEMENTED (Checkpoint 18)
- POST `/api/v1/admin-panel/users/create-hotel-owner/` ✅ IMPLEMENTED (Checkpoint 18)
- GET `/api/v1/admin-panel/amenities/` ✅ IMPLEMENTED (Checkpoint 18)
- POST `/api/v1/admin-panel/amenities/` ✅ IMPLEMENTED (Checkpoint 18)
- PATCH `/api/v1/admin-panel/amenities/{id}/` ✅ IMPLEMENTED (Checkpoint 18)
- DELETE `/api/v1/admin-panel/amenities/{id}/` ✅ IMPLEMENTED (Checkpoint 18)
- GET `/api/v1/admin-panel/amenities/categories/` ✅ IMPLEMENTED (Checkpoint 18)
- POST `/api/v1/admin-panel/amenities/categories/` ✅ IMPLEMENTED (Checkpoint 18)
- PATCH `/api/v1/admin-panel/amenities/categories/{id}/` ✅ IMPLEMENTED (Checkpoint 18)
- DELETE `/api/v1/admin-panel/amenities/categories/{id}/` ✅ IMPLEMENTED (Checkpoint 18)
- GET `/api/v1/admin-panel/payments/transactions/` ✅ IMPLEMENTED (Checkpoint 18)
- GET `/api/v1/admin-panel/customers/` ✅ IMPLEMENTED (Checkpoint 24)
- GET `/api/v1/admin-panel/customers/{id}/` ✅ IMPLEMENTED (Checkpoint 25)
- POST `/api/v1/admin-panel/customers/{id}/notes/` ✅ IMPLEMENTED (Checkpoint 25)
- PUT `/api/v1/admin-panel/customers/{id}/notes/{note_id}/` ✅ IMPLEMENTED (Checkpoint 25)
- DELETE `/api/v1/admin-panel/customers/{id}/notes/{note_id}/` ✅ IMPLEMENTED (Checkpoint 25)
- GET `/api/v1/admin-panel/statistics/registrations/` ✅ IMPLEMENTED (Checkpoint 26)
- GET `/api/v1/admin-panel/statistics/top-bookers/` ✅ IMPLEMENTED (Checkpoint 26)

## 2026-09-25 hotel names instead of addresses (E2E UX 13)
- `property_name` in `GET /bookings/`, admin customer detail bookings, `GET /partner/bookings/` and notifications, and `property.name` in `GET /admin-panel/bookings/lookup/`, are now the hotel name: the English translation, else any translation, else the full address (`Property.display_name()`). Before they were the address, the city or "Property N - city". Same field names and types; only the value changed

## 2026-09-24 frontend audit follow-up (F20, F22, F23)
- DRF `PageNumberPagination` (PAGE_SIZE 20) is global. These lists are paginated `{ count, next, previous, results }`: `me/favorites/`, `me/reviews/`, `me/history/`, `admin-panel/properties/`, `admin-panel/amenities/`, `admin-panel/amenities/categories/`, `partner/properties/`, `partner/rooms/`, `partner/rates/`, `partner/inventory/`, `payments/transactions/`. These return a plain array: `bookings/`, `admin-panel/users/`, `admin-panel/payments/transactions/`, `partner/bookings/`, `me/history/recent/`
- `GET /properties/search/` results now include `translations` (same shape as property detail), prefetched in one query
- `GET /me/favorites/` items now include `property_translations`, prefetched in one query
- `GET /partner/inventory/` accepts `rate_plan`, `date_from`, `date_to`
- Additive only: no field was removed or renamed, no migration

## Checkpoint 19 Changes (Observability/Performance/Security Hardening)

### Security Enhancements
- **Custom Security Headers Middleware**: Added X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy, and HSTS headers
- **Enhanced CORS Configuration**: Added explicit allowed headers and methods
- **Rate Limiting**: DRF throttling enabled (100/hour for anonymous, 1000/hour for authenticated users)
- **Custom Exception Handler**: Standardized error response format with proper logging
- **Logging System**: Comprehensive logging configuration with file rotation and separate error logs

### Performance Improvements
- **Database Connection Pooling**: Persistent connections with 60-second timeout
- **Query Optimization**: QueryOptimizationMixin and monitoring utilities
- **Performance Monitoring Middleware**: Tracks slow requests (>2s threshold)
- **Request Logging Middleware**: Logs all requests with timing information

### Error Handling
- **Standardized Error Format**: All errors return `{"error": {"code": "...", "message": "...", "details": "..."}}`
- **Custom Exception Classes**: TickBronException, RateLimitException, PermissionDeniedException, etc.
- **Detailed Logging**: All errors logged with appropriate severity levels

### Admin Panel URL Change
- **URL Path Changed**: Admin endpoints moved from `/api/v1/admin/` to `/api/v1/admin-panel/` to avoid conflict with Django's built-in admin
- **No Breaking Changes**: All functionality preserved, only URL path updated
- GET `/api/v1/admin/payments/transactions/` ✅ IMPLEMENTED (Checkpoint 18)

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

## Checkpoint 12 Notes (Availability API/pricing preview)
- Added GET `/api/v1/properties/{id}/availability/` endpoint with availability and pricing preview
- Query parameters: check_in (YYYY-MM-DD format, optional), check_out (YYYY-MM-DD format, optional)
- Response format: Property basic info + room_types with rate_plans + date_inventory
- Date inventory includes: date, available_rooms, booked_rooms, remaining_rooms, price, currency, is_available, minimum_stay, maximum_stay, notes
- Deterministic availability/price preview behavior (same inputs = same outputs)
- Date range validation (check_out must be after check_in)
- Active rate plans only (is_active=True)
- Soft-deleted data filtered (is_deleted=False)
- Date inventory filtered by date range when parameters provided
- Remaining rooms calculated as available_rooms - booked_rooms
- Public endpoint (no authentication required)
- Security review passed (8/8 categories, 48/48 individual checks)
- All 320 tests passing including 18 new availability tests

## Checkpoint 18 Notes (Partner APIs and Admin Moderation)
Status: READY

### Partner Property Management API
- POST `/api/v1/partner/properties/` - Create new property
  - Auth: Hotel-owner role required (IsHotelOwner permission)
  - Request: { property_type, max_guests, bedrooms, bathrooms, address_line1, address_line2, city, state, postal_code, country, latitude, longitude, base_price, currency, total_area, floor_number, has_elevator, has_parking, has_wifi, has_ac, has_heating }
  - Response: Created property object
  - Owner automatically set to authenticated user
- GET `/api/v1/partner/properties/` - List hotel-owner's properties
  - Auth: Hotel-owner role required
  - Response: Array of property objects owned by the user
  - Scoped to properties where owner = authenticated user
- PATCH `/api/v1/partner/properties/{id}/` - Update property
  - Auth: Hotel-owner role required
  - Request: Partial property update
  - Response: Updated property object
  - Only accessible for properties owned by the user
  - `status` is read-only: it is set only by admin moderation (approve/suspend); a sent value is ignored (audit #12). New properties start as `draft`
- DELETE `/api/v1/partner/properties/{id}/` - Delete property (soft delete)
  - Auth: Hotel-owner role required
  - Response: 204 No Content
  - Only accessible for properties owned by the user

### Partner Room Type Management API
- POST `/api/v1/partner/rooms/` - Create room type
  - Auth: Hotel-owner role required
  - Request: { property, name, slug, description, base_occupancy, max_occupancy, base_price, currency, total_rooms, bed_configuration, room_size }
  - Response: Created room type object
  - Property must belong to the authenticated hotel-owner
- GET `/api/v1/partner/rooms/` - List hotel-owner's room types
  - Auth: Hotel-owner role required
  - Response: Array of room type objects
  - Scoped to room types in properties owned by the user
- PATCH `/api/v1/partner/rooms/{id}/` - Update room type
  - Auth: Hotel-owner role required
  - Request: Partial room type update
  - Response: Updated room type object
  - Only accessible for room types in properties owned by the user
- DELETE `/api/v1/partner/rooms/{id}/` - Delete room type (soft delete)
  - Auth: Hotel-owner role required
  - Response: 204 No Content
  - Only accessible for room types in properties owned by the user

### Partner Rate Plan Management API
- POST `/api/v1/partner/rates/` - Create rate plan
  - Auth: Hotel-owner role required
  - Request: { room_type, name, slug, rate_type, description, base_price, currency, min_nights, max_nights, is_active, cancellation_policy, deposit_required, deposit_percentage, advance_booking_days }
  - Response: Created rate plan object
  - Room type must belong to a property owned by the authenticated hotel-owner
- GET `/api/v1/partner/rates/` - List hotel-owner's rate plans
  - Auth: Hotel-owner role required
  - Response: Array of rate plan objects
  - Scoped to rate plans in properties owned by the user
- PATCH `/api/v1/partner/rates/{id}/` - Update rate plan
  - Auth: Hotel-owner role required
  - Request: Partial rate plan update
  - Response: Updated rate plan object
  - Only accessible for rate plans in properties owned by the user
- DELETE `/api/v1/partner/rates/{id}/` - Delete rate plan (soft delete)
  - Auth: Hotel-owner role required
  - Response: 204 No Content
  - Only accessible for rate plans in properties owned by the user

### Partner Date Inventory Management API
- POST `/api/v1/partner/inventory/` - Create date inventory
  - Auth: Hotel-owner role required
  - Request: { rate_plan, date, available_rooms, booked_rooms, price, currency, is_available, minimum_stay, maximum_stay, notes }
  - Response: Created date inventory object
  - Rate plan must belong to a property owned by the authenticated hotel-owner
  - booked_rooms field is read-only (cannot be modified by hotel-owner)
- GET `/api/v1/partner/inventory/` - List hotel-owner's date inventory
  - Auth: Hotel-owner role required
  - Response: paginated `{ count, next, previous, results: [date inventory objects] }` (20 per page), sorted by `date`
  - Optional query (2026-09-24): `rate_plan=<id>`, `date_from=YYYY-MM-DD`, `date_to=YYYY-MM-DD` (both inclusive). An invalid value, or `date_to` before `date_from`, is a 400 with the field name in `details`
  - Scoped to date inventory in properties owned by the user
- PATCH `/api/v1/partner/inventory/{id}/` - Update date inventory
  - Auth: Hotel-owner role required
  - Request: Partial date inventory update
  - Response: Updated date inventory object
  - Only accessible for date inventory in properties owned by the user
  - booked_rooms field is read-only
- DELETE `/api/v1/partner/inventory/{id}/` - Delete date inventory (soft delete)
  - Auth: Hotel-owner role required
  - Response: 204 No Content
  - Only accessible for date inventory in properties owned by the user

### Partner Photo Upload API
- POST `/api/v1/partner/properties/{id}/photos/` - Upload property photo
  - Auth: Hotel-owner role required
  - Request: { photo (image file), photo_type, caption (optional), is_primary (optional), display_order (optional), alt_text (optional) }
  - Response: Created property photo object
  - Property must belong to the authenticated hotel-owner

### Partner Bookings API
- GET `/api/v1/partner/bookings/` - List bookings for hotel-owner's properties
  - Auth: Hotel-owner role required
  - Query Parameters: status (optional), payment_status (optional)
  - Response: Array of booking objects for properties owned by the user
  - Includes booking details, guest information, and property names

### Admin Property Moderation API
- GET `/api/v1/admin/properties/` - List all properties for moderation
  - Auth: Super-admin or staff required (IsSuperAdminOrStaff permission)
  - Response: Array of all property objects with owner information
  - Includes approval status, rejection reasons, and approval tracking
- POST `/api/v1/admin/properties/{id}/approve/` - Approve or reject property
  - Auth: Super-admin or staff required
  - Request: { rejection_reason (optional, only when rejecting) }
  - Response: Updated property object
  - If rejection_reason provided: sets status to 'rejected'
  - If no rejection_reason: sets status to 'active', records approver and timestamp
- POST `/api/v1/admin/properties/{id}/suspend/` - Suspend property
  - Auth: Super-admin or staff required
  - Request: None
  - Response: Updated property object with status 'suspended'

### Admin User Management API
- GET `/api/v1/admin/users/` - List all users for management
  - Auth: Super-admin or staff required
  - Response: Array of user objects with role information
  - Limited fields for admin user listing (no passwords)
- POST `/api/v1/admin/users/create-hotel-owner/` - Create hotel-owner account (super-admin only)
  - Auth: Super-admin required (IsSuperAdmin permission)
  - Request: { email, first_name, last_name, phone_number (optional), password, password_confirm }
  - Response: Created user object with hotel-owner role
  - Password must be 12+ characters with confirmation
  - Password is hashed and never returned in response
  - Account is immediately usable with provided credentials
  - Staff users cannot access this endpoint

### Admin Amenity Management API
- GET `/api/v1/admin/amenities/` - List all amenities
  - Auth: Super-admin or staff required
  - Response: Array of amenity objects with category information
- POST `/api/v1/admin/amenities/` - Create amenity
  - Auth: Super-admin or staff required
  - Request: { category, name, slug, description, icon, is_searchable, sort_order }
  - Response: Created amenity object
- PATCH `/api/v1/admin/amenities/{id}/` - Update amenity
  - Auth: Super-admin or staff required
  - Request: Partial amenity update
  - Response: Updated amenity object
- DELETE `/api/v1/admin/amenities/{id}/` - Delete amenity (soft delete)
  - Auth: Super-admin or staff required
  - Response: 204 No Content
- GET `/api/v1/admin/amenities/categories/` - List amenity categories
  - Auth: Super-admin or staff required
  - Response: Array of amenity category objects
- POST `/api/v1/admin/amenities/categories/` - Create amenity category
  - Auth: Super-admin or staff required
  - Request: { name, slug, description, icon, sort_order }
  - Response: Created amenity category object
- PATCH `/api/v1/admin/amenities/categories/{id}/` - Update amenity category
  - Auth: Super-admin or staff required
  - Request: Partial category update
  - Response: Updated amenity category object
- DELETE `/api/v1/admin/amenities/categories/{id}/` - Delete amenity category (soft delete)
  - Auth: Super-admin or staff required
  - Response: 204 No Content

### Admin Payment Monitoring API
- GET `/api/v1/admin/payments/transactions/` - List payment transactions for monitoring
  - Auth: Super-admin or staff required
  - Query Parameters: status (optional), provider (optional)
  - Response: Array of payment transaction objects
  - Read-only access for admin oversight
  - Includes booking ID, provider, amount, status, and timestamps

### Security Features
- **Partner API Security:**
  - Custom IsHotelOwner permission class requiring hotel-owner role or staff status
  - Property-level scoping: hotel-owners can only access their own properties
  - Room type validation: ensures room types belong to hotel-owner's properties
  - Rate plan validation: ensures rate plans belong to hotel-owner's properties
  - Date inventory validation: ensures inventory belongs to hotel-owner's properties
  - Booked rooms protection: booked_rooms field is read-only (prevents manipulation)
  - Authentication required for all partner endpoints
  - Cross-owner access prevention through queryset filtering and serializer validation

- **Admin API Security:**
  - Custom IsSuperAdmin permission class for super-admin-only endpoints
  - Custom IsSuperAdminOrStaff permission class for admin/staff endpoints
  - Hotel-owner account creation restricted to super-admin only
  - Password hashing using Django's create_user method
  - Password field marked as write-only (never returned in responses)
  - Password confirmation validation prevents typos
  - Automatic hotel-owner role assignment during account creation
  - Authentication required for all admin endpoints
  - Property approval tracking (approved_by, approved_at)
  - Rejection reason tracking for audit trail

- **Cross-Owner Access Prevention:**
  - Property queryset filtered by owner: `owner=self.request.user`
  - Room type queryset filtered by property owner: `property__owner=self.request.user`
  - Rate plan queryset filtered by property owner: `room_type__property__owner=self.request.user`
  - Date inventory queryset filtered by property owner: `rate_plan__room_type__property__owner=self.request.user`
  - Serializer validation methods prevent cross-owner data modification
  - Hotel-owners cannot access another owner's data through any endpoint

### Test Coverage
- 28 new partner API tests (all passing)
- 24 new admin API tests (all passing)
- 52 total new tests for checkpoint 18
- Tests cover permission scoping, ownership validation, cross-owner access prevention
- Tests cover hotel-owner account creation, password handling, role assignment
- Tests cover property moderation, amenity management, payment monitoring
- Security review passed: 23/23 checks (100% success rate)

## Checkpoint 23 Notes (Booking reference code + support lookup API)
Status: READY

### Booking Reference Code
- Added 6-character confirmation_code field to Booking model
- Generated using cryptographically secure random (secrets module)
- Unambiguous character set (excludes 0/O, 1/I/L to prevent confusion)
- Unique constraint on confirmation_code
- Database index for fast lookups

### Support Lookup API
- GET `/api/v1/admin-panel/bookings/lookup/?reference_code={code}` - Look up booking by reference code
  - Auth: Super-admin or staff required (IsSuperAdminOrStaff permission)
  - Query Parameters: reference_code (required, 6-character code)
  - Response: Full booking details including customer, property, and booking items
  - Used by staff/support when guests report problems and provide reference code
  - Returns comprehensive booking information for support troubleshooting

### Security Features
- Cryptographically secure random code generation (secrets.choice)
- Character set designed to prevent confusion (no 0/O, 1/I/L)
- Unique constraint prevents duplicate codes
- Staff-only access to support lookup endpoint
- Comprehensive booking details returned for support purposes

### Test Coverage
- 8 new booking reference code tests (all passing)
- 6 new support lookup API tests (all passing)
- 14 total new tests for checkpoint 23
- Tests cover code generation, uniqueness, support lookup functionality
- Security review passed: 18/18 checks (100% success rate)

## Checkpoint 24 Notes (Admin Customers Directory API)
Status: READY

### Admin Customers Directory API
- GET `/api/v1/admin-panel/customers/` - List customers with booking aggregates
  - Auth: Super-admin or staff required (IsSuperAdminOrStaff permission)
  - Query Parameters: search (optional), page (default: 1), page_size (default: 20, max: 100), sort_by (default: registration_date), sort_order (asc or desc, default: desc)
  - Response: Paginated list of customers with booking aggregates
  - Returns for each customer: id, registration_date, full_name, phone, email, whatsapp, telegram, preferred_contact_method, total_booking_count, last_booking_date, total_amount_paid, customer_status
  - Customer status logic: Active (is_active=True and has booking in last 90 days OR no bookings yet), Inactive (is_active=False OR last booking > 90 days ago)
  - Search filters by: name, phone, email, or customer ID
  - Sort options: registration_date, full_name, email, total_booking_count, last_booking_date, total_amount_paid, customer_status
  - Custom pagination with configurable page size
  - **Updated (audit #22):** staff and super-admin accounts are not listed (customers only). Sorting and pagination run in the database. `full_name` sorts by the displayed name, case-insensitively. Customers without bookings (`last_booking_date` null) sort last in both directions. Ties are broken by id. `total_booking_count` counts each booking once, however many payments it has

### Security Features
- Staff-only access to customer directory
- Customer status calculation based on activity and booking history
- Aggregated booking data from multiple related models
- Efficient database queries with annotations and aggregations
- Pagination prevents excessive data retrieval

### Test Coverage
- 18 new customer directory tests (all passing)
- Tests cover permission access, search, sorting, pagination, customer status logic
- Security review passed: 15/15 checks (100% success rate)

## Checkpoint 25 Notes (Admin Customer Detail API + Internal Notes)
Status: READY

### Admin Customer Detail API
- GET `/api/v1/admin-panel/customers/{id}/` - Get full customer profile
  - Auth: Super-admin or staff required (IsSuperAdminOrStaff permission)
  - Path Parameters: customer_id
  - Query Parameters: booking_filter (all, upcoming, completed, cancelled - default: all)
  - Response: Complete customer profile including:
    - Customer: Full contact information (id, email, first_name, last_name, full_name, phone_number, whatsapp, telegram, preferred_contact_method, date_joined, last_login, is_active, email_verified, phone_verified)
    - Bookings: All bookings filterable by status (id, reference_code, status, payment_status, check_in, check_out, number_of_nights, total_price, currency, property_name, property_city, created_at)
    - Payments: All payments (id, booking_id, provider, amount, currency, status, created_at)
    - Internal notes: Staff-only notes (id, customer, author, author_name, author_email, note, created_at, updated_at)
    - Last activity: Most recent of last_login, last booking created_at, last payment created_at

### Admin Internal Notes API
- POST `/api/v1/admin-panel/customers/{id}/notes/` - Create internal note
  - Auth: Super-admin or staff required
  - Request: { note }
  - Response: Created internal note with author information
  - Author automatically set to authenticated user
- PUT `/api/v1/admin-panel/customers/{id}/notes/{note_id}/` - Update internal note
  - Auth: Super-admin or staff required
  - Request: { note }
  - Response: Updated internal note
- DELETE `/api/v1/admin-panel/customers/{id}/notes/{note_id}/` - Delete internal note
  - Auth: Super-admin or staff required
  - Response: 204 No Content
  - Soft delete (is_deleted=True)

### Internal Notes Model
- New InternalNote model in admin_panel app
- Fields: customer (FK to User), author (FK to User, nullable), note (TextField, required)
- Inherits from TimeStampedModel and SoftDeleteModel
- Database indexes on (customer, created_at) and (author, created_at)
- Staff-only access - never exposed to customer-facing APIs
- Fully CRUD-able with author tracking

### Security Features
- Staff-only access to customer detail and internal notes
- Internal notes never exposed to customer-facing APIs
- Author tracking for audit trail (who wrote each note)
- Soft delete for internal notes (preserves audit trail)
- Customer scoping in note operations (cannot access notes for different customers)
- Booking filtering prevents data leakage
- Last activity calculation from multiple sources

### Test Coverage
- 21 new customer detail tests (all passing)
- 13 new internal notes tests (all passing)
- 34 total new tests for checkpoint 25
- Tests cover customer detail, booking filtering, payments, internal notes CRUD
- Tests cover permission access, author tracking, customer scoping
- Security review passed: 22/22 checks (100% success rate)

## Checkpoint 26 Notes (Admin Statistics API)
Status: READY

### Admin Registration Statistics API
- GET `/api/v1/admin-panel/statistics/registrations/` - Get registration statistics
  - Auth: Super-admin or staff required (IsSuperAdminOrStaff permission)
  - Query Parameters: type (rolling_12_months or calendar_year, default: rolling_12_months)
  - Response: Registration statistics with counts and period labels
  - Rolling 12-month window: Returns month-by-month registration counts for the last 12 months
  - Calendar year: Returns year-by-year registration counts for all years
  - Efficient database aggregation using Django ORM annotate/aggregate
  - Timezone-aware date handling

### Admin Top Bookers Leaderboard API
- GET `/api/v1/admin-panel/statistics/top-bookers/` - Get top bookers leaderboard
  - Auth: Super-admin or staff required (IsSuperAdminOrStaff permission)
  - Query Parameters: period (this_month, this_year, all_time, default: all_time), limit (default: 10, max: 100)
  - Response: Leaderboard with customer ranking by completed booking count
  - Returns: rank, customer_id, customer_name, completed_booking_count
  - Intended to support customer-reward/loyalty programs
  - Only completed bookings count (cancelled/pending bookings excluded)
  - Efficient database aggregation using Django ORM annotate/aggregate
  - Limit parameter validation (1-100 range enforced)
  - Timezone-aware date window handling for period filters

### Security Features
- Staff-only access to both statistics endpoints
- Registration statistics: Only aggregated counts, no personal data exposed
- Top bookers leaderboard: Limited to customer name and booking count (no email, phone, address)
- Efficient DB-level aggregation prevents N+1 query issues
- Soft-deleted records filtered from statistics
- Timezone-aware date calculations for accurate period boundaries

### Test Coverage
- 24 new statistics tests (all passing)
- Tests cover registration statistics (rolling 12-month, calendar year, edge cases)
- Tests cover top bookers leaderboard (all periods, limit validation, ranking)
- Tests cover permission access, data exposure limits, edge cases
- Security review passed: 18/18 checks (100% success rate)

### Backend Implementation Details
- New partner app with property/room/rate/inventory management ViewSets
- New admin app with moderation/user/amenity/payment monitoring endpoints
- Custom permission classes: IsHotelOwner, IsSuperAdmin, IsSuperAdminOrStaff
- Comprehensive serializers with ownership validation
- Database-agnostic implementation (SQLite development, PostgreSQL production)
- No new database models (uses existing Property, RoomType, RatePlan, DateInventory models)
- URL configuration for partner and admin endpoints
- Security review script for checkpoint 18

### Notes
- Partner APIs provide hotel-owners with full control over their properties
- Admin APIs provide moderation and oversight capabilities
- Hotel-owner accounts are never self-registered (super-admin only)
- Property scoping ensures complete data isolation between hotel-owners
- Password security follows Django best practices (hashing, write-only fields)
- Approval workflow with audit trail for property moderation
- All endpoints use session-based authentication consistent with existing auth system
- Frontend can integrate partner and admin management features when ready

## Checkpoint 17 Notes (Favorites/Reviews/Notifications/Account History)
Status: READY

### Favorites API
- GET `/api/v1/me/favorites/` - List user's favorite properties
  - Auth: Session-based (required)
  - Response: paginated `{ count, next, previous, results }` (20 per page). Each item: `{ id, user, property, property_translations: [{ language, name, description, address_line1, address_line2, city }], property_city, property_country, property_base_price, property_currency, property_primary_photo, notes, created_at }`
  - `property_translations` (2026-09-24) carries the property name; soft-deleted translations are left out
- POST `/api/v1/me/favorites/` - Add property to favorites
  - Auth: Session-based (required)
  - Request: { property, notes (optional) } (`property` is the property id)
  - Response: 201 `{ property, notes }` (no `id`; list the favorites again to get it)
  - Validates property is active and not deleted
- DELETE `/api/v1/me/favorites/{id}/` - Remove property from favorites
  - Auth: Session-based (required)
  - Response: 204 No Content
  - Soft deletes the favorite
- GET `/api/v1/me/favorites/count/` - Get total count of favorites
  - Auth: Session-based (required)
  - Response: { count }

### Reviews API
- GET `/api/v1/me/reviews/` - List user's reviews
  - Auth: Session-based (required)
  - Response: Array of review objects
  - Regular users see only their own reviews, staff see all
- POST `/api/v1/me/reviews/` - Create a review
  - Auth: Session-based (required)
  - Request: { property, booking (required), overall_rating (1-5), category_ratings (optional), title, comment }
  - Response: Created review object with status 'pending'
  - Rules (audit #20, see `.ai/contracts/booking.md` "Reviews"): booking is required, must be the user's own and `completed`; `property` must be the booking's property; one review per booking. Otherwise 400
  - Validates property is active and not deleted
- PATCH/PUT `/api/v1/me/reviews/{id}/` - Edit a review
  - `booking` and `property` are read-only (ignored if sent)
  - Any edit sets `status` back to 'pending' and clears `reviewed_at`, so an approved review leaves `property_scores` until re-approved
- GET `/api/v1/me/reviews/eligible_properties/` - Get bookings eligible for review
  - Auth: Session-based (required)
  - Response: { eligible_properties: [...] }, one entry per completed booking without a review (two stays at the same property are two entries), newest check_out first
  - Entry: { property_id, property_city, property_country, booking_id, confirmation_code, check_in, check_out }
- GET `/api/v1/me/reviews/property_scores/?property_id={id}` - Get property review scores (public, read-only: anonymous visitors get 200; approved reviews only)
  - Auth: Session-based (required)
  - Response: { property_id, total_reviews, average_rating, category_scores }
  - Only includes approved reviews
  - Category scores: cleanliness, location, value, amenities, service

### Notifications API
- GET `/api/v1/me/notifications/` - List user's notifications
  - Auth: Session-based (required)
  - Response: Array of notification objects
  - Filtered by user, ordered by creation date
- PATCH `/api/v1/me/notifications/{id}/` - Update notification read status
  - Auth: Session-based (required)
  - Request: { is_read }
  - Response: Updated notification object
  - Automatically sets read_at when marking as read
- GET `/api/v1/me/notifications/unread/` - Get unread notifications
  - Auth: Session-based (required)
  - Response: Array of unread notification objects
- POST `/api/v1/me/notifications/mark_all_read/` - Mark all notifications as read
  - Auth: Session-based (required)
  - Response: { marked_as_read: count }
- GET `/api/v1/me/notifications/count/` - Get notification counts
  - Auth: Session-based (required)
  - Response: { total, unread, read }
- POST `/api/v1/me/notifications/` - Blocked (403 Forbidden)
  - Direct notification creation not allowed via API

### Account History API
- GET `/api/v1/me/history/` - List user's account history
  - Auth: Session-based (required)
  - Response: Array of account history objects
  - Read-only access, paginated
- GET `/api/v1/me/history/recent/?limit={n}` - Get recent history entries
  - Auth: Session-based (required)
  - Response: Array of recent history objects
  - Default limit: 10, max: 50
- GET `/api/v1/me/history/stats/` - Get account activity statistics
  - Auth: Session-based (required)
  - Response: { total_entries, action_counts }
  - Action counts grouped by action type

### Security Features
- All endpoints require session-based authentication
- User isolation: users can only access their own data
- Staff users can access all reviews for moderation
- Input validation: ratings (1-5), property status, booking status
- Access control: notification creation blocked, history read-only
- Unique constraints: one favorite per property, one review per booking
- Soft delete: records marked as deleted rather than removed
- Audit trail: account history logged for favorite and review actions
- Database indexes for performance optimization

### Test Coverage
- 34 new account-specific tests (all passing)
- 509 total regression tests (all passing)
- Security review passed: 21/21 checks (100% success rate)

## Checkpoint 13 Notes (Booking engine transactional locking)
- Added POST `/api/v1/bookings/` endpoint with transaction-safe inventory locking
- Added GET `/api/v1/bookings/` endpoint for listing user bookings with filtering
- Added POST `/api/v1/bookings/{id}/cancel/` endpoint for booking cancellation with inventory restoration
- Booking creation requires authentication (IsAuthenticated permission)
- Request body: property_id, room_type_id, rate_plan_id, check_in, check_out, guest_count, special_requests (optional)
- Response includes: booking details, confirmation_code, booking_items, pricing information
- Transaction-safe inventory locking using SELECT FOR UPDATE and Django atomic transactions
- Double-booking prevention through row-level locking and inventory consistency checks
- Confirmation code generation using cryptographically secure random (secrets module)
- Booking status management: pending, confirmed, cancelled, completed, no_show
- Payment status tracking: pending, paid, failed, refunded, partially_refunded
- Booking cancellation with automatic inventory restoration
- Booking filtering by status and payment_status
- Comprehensive validation: date range, rate plan constraints, room type capacity, inventory availability
- Security review passed (7/7 categories, 32/32 individual checks)
- All 348 tests passing including 34 new booking tests

Rules:
- Breaking API changes require `/api/v2/`.
- OpenAPI documentation is mandatory.
- Frontend must not invent response/request fields.
- Contract changes must be recorded here and in HANDOFF.md.
- ✅ indicates implemented endpoints, ❌ indicates pending implementation.

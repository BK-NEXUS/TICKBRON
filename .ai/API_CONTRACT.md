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
- GET `/api/v1/properties/{id}/availability/` ✅ IMPLEMENTED (Checkpoint 12)
- POST `/api/v1/bookings/` ✅ IMPLEMENTED (Checkpoint 13)
- GET `/api/v1/bookings/` ✅ IMPLEMENTED (Checkpoint 13)
- POST `/api/v1/bookings/{id}/cancel/` ✅ IMPLEMENTED (Checkpoint 13)
- POST `/api/v1/payments/{provider}/init/`
- POST `/api/v1/payments/{provider}/webhook/`
- GET `/api/v1/me/favorites/` ✅ IMPLEMENTED (Checkpoint 17)
- POST `/api/v1/me/favorites/` ✅ IMPLEMENTED (Checkpoint 17)
- DELETE `/api/v1/me/favorites/{id}/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/favorites/count/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/reviews/` ✅ IMPLEMENTED (Checkpoint 17)
- POST `/api/v1/me/reviews/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/reviews/eligible_properties/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/reviews/property_scores/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/notifications/` ✅ IMPLEMENTED (Checkpoint 17)
- PATCH `/api/v1/me/notifications/{id}/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/notifications/unread/` ✅ IMPLEMENTED (Checkpoint 17)
- POST `/api/v1/me/notifications/mark_all_read/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/notifications/count/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/history/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/history/recent/` ✅ IMPLEMENTED (Checkpoint 17)
- GET `/api/v1/me/history/stats/` ✅ IMPLEMENTED (Checkpoint 17)
- POST `/api/v1/partner/properties/`
- PATCH `/api/v1/partner/properties/{id}/`
- POST `/api/v1/partner/properties/{id}/photos/`
- PATCH `/api/v1/partner/rooms/{id}/`
- PATCH `/api/v1/partner/rates/{id}/availability/`
- GET `/api/v1/partner/bookings/` ✅ IMPLEMENTED (Checkpoint 18)
- GET `/api/v1/admin/properties/` ✅ IMPLEMENTED (Checkpoint 18)
- POST `/api/v1/admin/properties/{id}/approve/` ✅ IMPLEMENTED (Checkpoint 18)
- POST `/api/v1/admin/properties/{id}/suspend/` ✅ IMPLEMENTED (Checkpoint 18)
- GET `/api/v1/admin/amenities/` ✅ IMPLEMENTED (Checkpoint 18)
- POST `/api/v1/admin/users/create-hotel-owner/` ✅ IMPLEMENTED (Checkpoint 18)
- GET `/api/v1/admin/users/` ✅ IMPLEMENTED (Checkpoint 18)
- GET `/api/v1/admin/amenities/categories/` ✅ IMPLEMENTED (Checkpoint 18)
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
  - Response: Array of date inventory objects
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
  - Response: Array of favorite objects with property details
  - Includes property city, country, base price, currency, primary photo
- POST `/api/v1/me/favorites/` - Add property to favorites
  - Auth: Session-based (required)
  - Request: { property_id, notes (optional) }
  - Response: Created favorite object
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
  - Request: { property_id, booking_id (optional), overall_rating (1-5), category_ratings (optional), title, comment }
  - Response: Created review object with status 'pending'
  - Validates booking is completed if provided
  - Validates property is active and not deleted
- GET `/api/v1/me/reviews/eligible_properties/` - Get properties eligible for review
  - Auth: Session-based (required)
  - Response: Array of properties with completed bookings not yet reviewed
  - Includes property details and booking information
- GET `/api/v1/me/reviews/property_scores/?property_id={id}` - Get property review scores
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

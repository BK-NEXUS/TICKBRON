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

## Property Detail Page (Frontend Checkpoint 06)
Status: FRONTEND READY (API endpoint pending)

### GET `/api/v1/properties/{id}/`
- Request: Property ID via URL parameter
- Response needed: Full property details including:
  - Basic property information (id, name, description, location, etc.)
  - Property type details
  - Amenities (with categories and availability)
  - Media/images (gallery URLs)
  - Pricing information
  - Policies (check-in, cancellation, etc.)
  - Rating and review information
  - Availability information
- Auth: None (public endpoint for property viewing)
- Error: 404 if property not found, 403 if property is inactive/suspended
- Mock status: Frontend uses mock adapter with property data structure
- Expected states: Loading, property found, property not found, error
- READY/BLOCKED status: READY (frontend complete, waiting for backend API)

### Frontend Implementation Details
- PropertyDetailPage component with routing at `/property/:id`
- PropertyGallery component with image navigation (mock images)
- PropertyDetailHeader component with property metadata
- SEO metadata foundations (document title, meta description)
- Responsive design for all breakpoints (mobile, tablet, desktop, large desktop)
- Comprehensive error handling and loading states
- Accessibility features (ARIA attributes, keyboard navigation, semantic HTML)
- PropertyCard navigation to property detail page
- Test coverage: 35 new tests (PropertyGallery: 10, PropertyDetailHeader: 12, PropertyDetailPage: 13, PropertyCard: +1)
- Security review passed (13/13 checks)
- No API calls made - uses mock adapter architecture

### Notes
- Frontend property detail page is complete and production-ready
- Mock adapter structure matches backend Property models from Backend Checkpoint 05
- Gallery uses placeholder images (real images to come from backend media API)
- SEO metadata structure ready for backend integration
- Responsive interaction patterns implemented for all device sizes
- No backend API dependencies for checkpoint 06 (mock adapter only)
- Frontend can continue with checkpoint 07 independently

## Property Detail Extensions (Frontend Checkpoint 07)
Status: FRONTEND READY (API endpoint pending)

### Property Amenities Detail
- Displays property amenities grouped by category with availability status
- Shows amenity icons, names, descriptions, and availability indicators
- Supports category-based organization with proper sorting
- Mock status: Frontend uses mock adapter with amenity data structure
- Expected API: GET `/api/v1/properties/{id}/amenities/` when backend endpoint is available

### Property Policies Detail
- Displays property policies grouped by type (check-in, cancellation, house rules, payment, security)
- Shows policy titles, descriptions, and strictness indicators
- Formats policy type labels for better readability
- Mock status: Frontend uses mock adapter with policy data structure
- Expected API: GET `/api/v1/properties/{id}/policies/` when backend endpoint is available

### Nearby Places
- Displays nearby attractions and places with distance, rating, and category information
- Sorts places by distance (ascending) for user convenience
- Shows place names, categories, distances, ratings, and addresses
- Mock status: Frontend uses mock adapter with nearby places data structure
- Expected API: GET `/api/v1/properties/{id}/nearby-places/` when backend endpoint is available

### Dining Restaurants
- Displays nearby restaurants with cuisine, distance, rating, and price range information
- Formats price range labels (Budget-friendly, Moderate, Expensive, Fine dining)
- Sorts restaurants by distance (ascending) for user convenience
- Shows restaurant names, cuisine, distances, ratings, price ranges, and addresses
- Mock status: Frontend uses mock adapter with restaurant data structure
- Expected API: GET `/api/v1/properties/{id}/restaurants/` when backend endpoint is available

### Frontend Implementation Details
- All four components integrated into PropertyDetailPage as additional sections
- Comprehensive test coverage: 40 new tests (PropertyAmenitiesDetail: 9, PropertyPoliciesDetail: 8, NearbyPlaces: 10, DiningRestaurants: 13)
- Responsive design for all breakpoints with proper grid layouts
- Empty state handling for missing data
- Accessibility features: semantic HTML, ARIA labels, proper heading hierarchy
- Security review passed (13/13 checks)
- No API calls made - uses mock adapter architecture
- Mock adapter extended with amenities, nearby places, and restaurants data

### Notes
- All property detail extensions are complete and production-ready
- Mock adapter structure matches expected backend data models
- Components are ready for backend API integration when endpoints become available
- Responsive interaction patterns implemented for all device sizes
- No backend API dependencies for checkpoint 07 (mock adapter only)
- Frontend can continue with checkpoint 08 independently

## Property Photo Data Model (Backend Checkpoint 07)
Status: DATA MODEL READY (API endpoints pending)

### PropertyPhoto
- Stores property photos with metadata and ordering
- Fields: property (FK), photo (ImageField), photo_type, caption, is_primary, display_order, alt_text
- Photo types: exterior, interior, amenity, room, other
- is_primary flag for cover photo (enforced: only one primary per property)
- display_order for photo gallery ordering
- Server-side image validation (file type, size, content type)
- Storage abstraction layer (TickBronStorage, LocalStorage, S3 placeholder)
- Upload path: properties/{property_id}/photos/{filename}
- CASCADE deletion on property delete
- Admin interface with inline editing in Property admin

### Storage Abstraction
- TickBronStorage: Unified storage interface across environments
- LocalStorage: Local filesystem storage for development
- S3Storage: Placeholder for S3-compatible storage (production)
- get_media_upload_path: Generates upload paths
- validate_image_file: Server-side image validation (10MB limit, .jpg/.jpeg/.png/.gif/.webp only)

### Notes
- PropertyPhoto model inherits from BaseModel (timestamps, soft delete, active status)
- Comprehensive database indexes for performance
- Admin interface available for PropertyPhoto model
- Full test coverage (25 tests) with 100% pass rate
- Security review passed (9/9 checks)
- API endpoints for photo management will be implemented in future checkpoints

## Room/rate plan/inventory Data Models (Backend Checkpoint 08)
Status: DATA MODELS READY (API endpoints pending)

### RoomType
- Classifies rooms within properties (Standard Room, Suite, Deluxe Room, etc.)
- Fields: property (FK), name, slug, description, base_occupancy, max_occupancy, base_price, currency, total_rooms, bed_configuration, room_size
- Occupancy validation: max_occupancy cannot be less than base_occupancy
- Price validation: negative prices prevented
- Unique constraint on (property, slug)
- CASCADE deletion on property delete
- Admin interface with inline editing (RoomPhotoInline, RoomAmenityInline)

### RoomPhoto
- Stores room-specific photos with metadata and ordering
- Fields: room_type (FK), photo (ImageField), photo_type, caption, is_primary, display_order, alt_text
- Photo types: bedroom, bathroom, living_area, kitchen, view, other
- is_primary flag enforced (only one primary per room type)
- Server-side image validation using storage abstraction
- CASCADE deletion on room_type delete
- Admin interface with inline editing in RoomType admin

### RoomAmenity
- Links room types to their available amenities
- Fields: room_type (FK), amenity (FK), is_available, notes
- Unique constraint on (room_type, amenity)
- CASCADE deletion on both room_type and amenity delete
- Admin interface with inline editing in RoomType admin

### RatePlan
- Defines pricing strategies for room types
- Fields: room_type (FK), name, slug, rate_type, description, base_price, currency, min_nights, max_nights, is_active, cancellation_policy, deposit_required, deposit_percentage, advance_booking_days
- Rate types: standard, non_refundable, early_bird, last_minute, long_stay, seasonal, corporate, promo
- Validation: max_nights cannot be less than min_nights
- Validation: deposit_percentage required when deposit_required is True
- Price validation: negative prices prevented
- Unique constraint on (room_type, slug)
- CASCADE deletion on room_type delete
- Admin interface with comprehensive fieldsets

### DateInventory
- Tracks day-by-day availability and pricing
- Fields: rate_plan (FK), date, available_rooms, booked_rooms, price, currency, is_available, minimum_stay, maximum_stay, notes
- Validation: booked_rooms cannot exceed available_rooms
- Validation: maximum_stay cannot be less than minimum_stay
- remaining_rooms property: calculates available rooms minus booked rooms
- is_available_for_booking method: checks availability with night count constraints
- Unique constraint on (rate_plan, date)
- CASCADE deletion on rate_plan delete
- Admin interface with remaining_rooms display

### Notes
- All models inherit from BaseModel (timestamps, soft delete, active status)
- Comprehensive database indexes for performance
- Full admin interfaces available for all models
- Full test coverage (54 tests) with 100% pass rate
- Security review passed (25/25 checks)
- API endpoints for room/rate plan/inventory management will be implemented in future checkpoints

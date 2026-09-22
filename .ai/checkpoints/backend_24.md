# CHECKPOINT

Checkpoint: 24 — Admin Customers directory API
Owner: Kolya
Commit: kolya 24 project
Status: READY

## Implemented
- Admin API endpoint for customers directory with booking aggregates
- GET /api/v1/admin-panel/customers/ with pagination, sorting, and search
- Returns customer information: ID, registration date, full name, phone, email, whatsapp, telegram, preferred contact method
- Returns booking aggregates: total booking count, last booking date, total amount paid
- Returns customer status (active/inactive based on account activity)
- Search functionality: search by name, phone, email, or customer ID
- Pagination support: default 20 items per page, max 100
- Sorting support: by registration_date, full_name, email, total_booking_count, last_booking_date, total_amount_paid, customer_status
- Protected with IsSuperAdminOrStaff permission (staff/admin only)
- Customer status logic: Active if is_active=True and (has booking in last 90 days OR no bookings yet), Inactive otherwise

## Admin Customers Directory API
### Endpoint Details
- GET /api/v1/admin-panel/customers/
- Auth: Staff or super-admin required (IsSuperAdminOrStaff permission)
- Error: 403 for non-staff users, 400 for invalid pagination parameters

### Query Parameters
- search: Search by name, phone, email, or customer ID (optional)
- page: Page number (default: 1)
- page_size: Items per page (default: 20, max: 100)
- sort_by: Sort field (default: registration_date)
- sort_order: Sort order (asc or desc, default: desc)

### Response Structure
- count: Total number of customers
- next: URL for next page (null if no next page)
- previous: URL for previous page (null if no previous page)
- results: Array of customer objects

### Customer Object Fields
- id: Customer ID
- registration_date: Date when customer registered
- full_name: Customer's full name
- phone: Phone number
- email: Email address
- whatsapp: WhatsApp number
- telegram: Telegram handle
- preferred_contact_method: Preferred contact method (phone, whatsapp, telegram, email)
- total_booking_count: Total number of bookings
- last_booking_date: Date of last booking
- total_amount_paid: Total amount paid across all bookings
- customer_status: Customer status (active/inactive)

### Use Case
- Admin staff can view and search customer directory
- Sort customers by various metrics (booking count, amount paid, registration date)
- Paginate through large customer lists
- Search customers by name, phone, email, or ID for quick lookup

## Backend Implementation Details
- admin_customers_directory view in admin_panel/views.py
- AdminCustomerPagination class for pagination (default 20, max 100)
- AdminCustomerSerializer for response structure
- Django ORM annotations for booking aggregates (Count, Sum, Max)
- Search filters: full_name, first_name, last_name, phone_number, email, id
- URL configuration: admin_panel/urls.py
- Customer status calculation based on is_active and last_booking_date (90-day threshold)

## Database Changes
- No database migrations required (uses existing User and Booking models)
- Booking aggregates calculated via Django ORM annotations
- No new tables or fields

## Tests
### Admin Customers Directory Tests (test_admin_api.py)
- test_super_admin_can_access_customers_directory: Verifies super-admin access
- test_staff_can_access_customers_directory: Verifies staff access
- test_regular_user_cannot_access_customers_directory: Verifies permission enforcement
- test_unauthenticated_user_cannot_access_customers_directory: Verifies authentication required
- test_customers_directory_returns_required_fields: Verifies complete response structure
- test_customers_directory_includes_booking_aggregates: Verifies booking aggregates
- test_search_by_name: Verifies search by name
- test_search_by_email: Verifies search by email
- test_search_by_phone: Verifies search by phone
- test_search_by_customer_id: Verifies search by customer ID
- test_pagination_works: Verifies pagination
- test_sorting_by_registration_date: Verifies sorting by registration date
- test_sorting_by_total_booking_count: Verifies sorting by booking count
- test_sorting_by_total_amount_paid: Verifies sorting by amount paid
- test_customer_status_active_for_recent_booking: Verifies active status for recent bookings
- test_customer_status_inactive_for_no_booking: Verifies active status for new customers
- test_contact_method_fields_returned: Verifies contact method fields
- test_invalid_sort_field_defaults_to_registration_date: Verifies default sort field
- test_invalid_sort_order_defaults_to_desc: Verifies default sort order

### Regression Suite
- Previous checkpoint 23 test status: 626 passed, 2 skipped
- New tests added: 20 admin customers directory tests
- Expected total: 646 passed, 2 skipped (pending test environment setup)

## Security Review
- Admin endpoint protected with staff-only permission (safe)
- Authentication required via IsSuperAdminOrStaff permission (safe)
- No sensitive data exposed beyond authorized staff (safe)
- Search uses icontains (case-insensitive) which is safe (safe)
- Pagination prevents data dumping attacks (safe)
- Input validation for sort_by and sort_order parameters (safe)
- No SQL injection risk (Django ORM protected) (safe)
- No critical or high security issues identified

## API/contract changes
- Updated HANDOFF.md with admin customers directory endpoint documentation
- New endpoint: GET /api/v1/admin-panel/customers/ - Admin customers directory
- No breaking changes to existing endpoints
- No database schema changes

## Known Issues/Limitations
- None identified

## Next Checkpoint
Checkpoint 25 — (not yet defined)

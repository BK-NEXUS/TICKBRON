# API CONTRACT

Master API contract for TICKBRON.

Version prefix: `/api/v1/`

Core endpoints:
- POST `/api/v1/auth/register/` ✅ IMPLEMENTED (Checkpoint 03)
- POST `/api/v1/auth/login/` ✅ IMPLEMENTED (Checkpoint 03)
- POST `/api/v1/auth/logout/` ✅ IMPLEMENTED (Checkpoint 03)
- POST `/api/v1/auth/refresh/` ✅ IMPLEMENTED (Checkpoint 03)
- GET `/api/v1/auth/me/` ✅ IMPLEMENTED (Checkpoint 03; `is_staff` added 2026-09-24, `is_superuser` added 2026-09-25, `role` added 2026-09-26, `phone_verified` added 2026-10-10, removed 2026-10-16)
- `/api/v1/auth/otp/*` and `/api/v1/auth/phone/verify/*` ❌ REMOVED (2026-10-16): accounts are e-mail only; see contracts/auth.md
- GET `/api/v1/auth/csrf/` ✅ IMPLEMENTED (2026-09-24, frontend audit F2; see contracts/auth.md)
- GET `/api/v1/properties/search/` ✅ IMPLEMENTED (Checkpoint 10; `translations` added 2026-09-24; `features`, `min_rating`, `sort=reviews`, real date availability, `average_rating`/`review_count` added 2026-09-28)
- GET `/api/v1/properties/filter-options/` ✅ IMPLEMENTED (2026-09-28)
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
- GET `/api/v1/partner/properties/` ✅ IMPLEMENTED (Checkpoint 18; read-only `name` added 2026-09-28)
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
- POST `/api/v1/partner/inventory/` ✅ IMPLEMENTED (Checkpoint 18); `available_rooms`/`booked_rooms` DEPRECATED 2026-09-29, see "Phase 3 item 3.4" below
- GET `/api/v1/partner/inventory/` ✅ IMPLEMENTED (Checkpoint 18; `rate_plan`/`date_from`/`date_to` filters added 2026-09-24)
- PATCH `/api/v1/partner/inventory/{id}/` ✅ IMPLEMENTED (Checkpoint 18)
- DELETE `/api/v1/partner/inventory/{id}/` ✅ IMPLEMENTED (Checkpoint 18)
- POST `/api/v1/partner/room-inventory/` ✅ IMPLEMENTED (2026-09-29, Phase 3 item 3.4)
- GET `/api/v1/partner/room-inventory/` ✅ IMPLEMENTED (2026-09-29, Phase 3 item 3.4; `room_type`/`date_from`/`date_to` filters)
- PATCH `/api/v1/partner/room-inventory/{id}/` ✅ IMPLEMENTED (2026-09-29, Phase 3 item 3.4)
- DELETE `/api/v1/partner/room-inventory/{id}/` ✅ IMPLEMENTED (2026-09-29, Phase 3 item 3.4)
- POST `/api/v1/partner/room-inventory/bulk/` ✅ IMPLEMENTED (2026-09-29, Phase 3 item 3.6)
- POST `/api/v1/partner/inventory/bulk-price/` ✅ IMPLEMENTED (2026-09-29, Phase 3 item 3.7)
- POST `/api/v1/partner/blocks/` ✅ IMPLEMENTED (2026-09-29, Phase 3 item 3.5)
- GET `/api/v1/partner/blocks/` ✅ IMPLEMENTED (2026-09-29, Phase 3 item 3.5; `room_type` filter added 2026-09-29 Phase 3 item 3.6)
- DELETE `/api/v1/partner/blocks/{id}/` ✅ IMPLEMENTED (2026-09-29, Phase 3 item 3.5; undoes the block, no PATCH/PUT)
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

## 2026-10-02 Geography: Country > Region > City (Geography plan G3, G4)
**REMOVED 2026-10-19:** the old text location input on partner property writes and the name-based Status URL keys (they worked next to the ids and codes since 2026-10-02) are gone. Use the ids and codes; see the notes below.
Dictionary rows carry `name_uz`, `name_ru`, `name_en`; the frontend picks the language (English until i18n exists). The old text fields `country` / `state` / `city` stay on Property but are now **read-only copies** of the English names of the refs (set by `Property.save()`).

Public (no login, read-only, active rows only, ordered by `sort_order` then English name; `hotel_count` = public properties: active, approved, not deleted):
- NEW `GET /api/v1/geography/countries/` -> `[{ id, code, currency, name_uz, name_ru, name_en, hotel_count }]`
- NEW `GET /api/v1/geography/countries/{code}/regions/` (code: ISO2, any case) -> `[{ id, name_uz, name_ru, name_en, hotel_count }]`. 404 for an unknown or hidden country
- NEW `GET /api/v1/geography/regions/{id}/cities/` -> `[{ id, name_uz, name_ru, name_en, hotel_count }]`. 404 for an unknown or hidden region (or one in a hidden country)

Super-admin only (`is_superuser`; staff get 403), under `/api/v1/admin-panel/geography/`, one set per kind `countries/`, `regions/`, `cities/`:
- `GET` list (paginated `{count, next, previous, results}`, `page_size` up to 200; hidden rows included): `?search=` (any of the three names, countries also the code), `?is_active=true|false`, `?country=<id>` (regions), `?region=<id>` (cities)
- `POST` create. Country `{ code (2 letters), currency (3 letters), name_uz, name_ru, name_en, is_active? }`; region `{ country, names... }`; city `{ region, names... }`. Codes are upper-cased; names must be non-blank and unique inside the parent (400 otherwise)
- `GET/PATCH/PUT {id}/`: edit names and `is_active` (hide/show). The parent (`country` / `region`) and the `slug` cannot be changed (400 / read-only). Rows: country `{ id, code, currency, names, is_active, sort_order, region_count, hotel_count }`, region `{ id, country, slug, names, is_active, sort_order, city_count, hotel_count }`, city `{ id, region, slug, names, is_active, sort_order, hotel_count }`
- `DELETE {id}/`: 204, or **409** when the row is in use (regions, cities or properties): hide it instead
- `POST {kind}/reorder/` body `{ "ids": [..] }`: `sort_order` becomes the position of each id (400 for an empty, repeated or unknown id; nothing changes then)

Property writes (BREAKING):
- `POST /api/v1/partner/properties/` needs the location: `country_ref`, `region_ref`, `city_ref` (ids). 400 when a ref is missing, null, hidden, the region is not in the country or the city not in the region (field errors under `error.details`)
  - **REMOVED (2026-10-19):** the text fields `country`, `state`, `city` are no longer input on create or edit (they used to be resolved through the geography mapping). They stay in the response as read-only copies of the English names of the chosen refs. A create with text only is 400 naming `country_ref`, `region_ref` and `city_ref`; text sent next to the ids is ignored; text sent on a PATCH changes nothing.
- `PATCH /api/v1/partner/properties/{id}/`: the three refs are optional; refs cannot be null; the merged result is validated the same way (changing only the region while the old city stays is a 400). Responses include `country_ref`, `region_ref`, `city_ref` (ids). Editing other fields never re-validates an unchanged location.
- `PATCH /api/v1/admin-panel/properties/{id}/region/` accepts `{ country_ref, region_ref, city_ref }` (the admin can fix country and city too; all three `null` clears the location -> "Unspecified"). The old `{ state }` body still works when no ref is sent. Admin property list/detail now include the three ref ids

Search: `location`, `q` and `suggestions` match the uz/ru/en names of the city, region and country through the refs ("Toshkent", "Ташкент" and "Tashkent" find the same hotel), and still match the old text fields, so unmapped hotels stay searchable. Suggestions are strings in the language that matched what was typed, for places with public hotels.

Status (replaces the 2026-09-30 admin Status URLs below; the URL keys are an ISO country code and a region id, names no longer work, see below): hotels are grouped by their refs; hotels without a ref are "unspecified".
- **REMOVED (2026-10-19):** wherever a URL key is `{code}` or `{region_id}` the old name keys (a country or region name in any language) are no longer accepted: a key that is not an ISO code (countries) or a number (regions) and not `unspecified` matches nothing, so the list is empty (`count: 0`). `country` / `region` in the response are the upper-case code / the region id as text; `country_name` and `region_name` are the English names. The row fields `country` and `region` (English names) stay in the lists for display only.
- `GET /api/v1/admin-panel/status/countries/`: rows `{ rank, code, country, name_uz, name_ru, name_en, hotels, bookings, guests, revenue }`. `code` is the ISO2 code, `null` for the "Unspecified" group (`country: "Unspecified"`). `search` matches the names in all languages or the code
- `GET /api/v1/admin-panel/status/countries/{code}/regions/`: `{code}` is the ISO2 code (any case) or `unspecified`. Rows `{ rank, id, region, name_uz, name_ru, name_en, hotels, bookings, guests, revenue }` (`id` null = "Unspecified"), plus `country` (upper-case code or `unspecified`) and `country_name` (English, null for an unknown code)
- `GET /api/v1/admin-panel/status/countries/{code}/regions/{region_id}/hotels/`: `{region_id}` is a region id or `unspecified`; rows as before `{ rank, id, name, city, status, bookings, guests, revenue }`, plus `country`, `country_name`, `region` (the id as text or `unspecified`) and `region_name`. A region of another country or a non-numeric segment gives an empty list
- `GET /api/v1/admin-panel/status/hotels/{id}/`: `hotel` gains `country_code`, `region_id`, `city_id`; `hotel.region` is the English region name from the ref ("Unspecified" without one)
- `GET /api/v1/partner/status/` is unchanged (its `region` / `country` text are the synced English names)

## 2026-09-30 partner Status (Status plan S4)
Same definitions and `period` as the admin Status (S2 below).
- NEW `GET /api/v1/partner/status/?period=&year=` (hotel owners; staff pass the permission but see only properties they own themselves): `{ since: "YYYY-MM-DD" (the account's creation date), period, totals: { bookings, guests, revenue }, properties: [{ id, name, city, region, country, status, bookings, guests, revenue }], year, available_years: [YYYY, ...], monthly: [{ month: "YYYY-MM", bookings, guests, revenue }] x 12 }`
- Only the requesting owner's non-deleted properties; `properties` lists all of them (ordered by name), with zeros when a property has no counted booking in `period`. `totals` and `properties` follow `period` (default `all` = since the account was created); `monthly` covers `year` (default: the current year). 400 `{ period: [...] }` / `{ year: [...] }` for bad values
- Additive only, no existing field or endpoint changed

## 2026-09-30 admin Status: hotel detail + users (Status plan S3)
Same definitions, `period` and access rules as S2 below.
- NEW `GET /api/v1/admin-panel/status/hotels/{id}/?period=&year=`: `{ hotel: { id, name, status, address, city, region, country, registered_at, owner: { id, name, email, phone } }, period, totals: { bookings, guests, revenue }, year, available_years: [YYYY, ...], monthly: [{ month: "YYYY-MM", bookings, guests, revenue }] x 12 }`. `totals` follow `period`; `monthly` covers `year` (default: the current year; 400 `{ year: [...] }` unless YYYY 2000-2100), every month present (zeros when empty). `available_years` = years with counted bookings, ascending. `region` is `"Unspecified"` when empty. `registered_at` = the property's creation time. 404 for an unknown or deleted hotel
- NEW `GET /api/v1/admin-panel/status/users/` (top 1000, paginated like S2): guests ranked by counted bookings in `period` (ties: latest stay first, then id). Rows `{ rank, id, full_name, first_name, last_name, phone, email, bookings, total_spent: [{ currency, amount }], last_booking_date: "YYYY-MM-DD" }` (`last_booking_date` = check-in of the latest counted booking in the period). Only accounts with at least one counted booking are listed. `search` matches first name, last name, full name, phone, email or ID (partial, any case). The frontend links each row to the existing customer profile `/admin/customers/{id}`
- Additive only, no existing field or endpoint changed

## 2026-09-30 admin Status: countries > regions > hotels (Status plan S2)
Definitions (`backend/bookings/stats.py`, used by every Status endpoint):
- A booking **counts** when `status` is `confirmed` or `completed` (not pending, cancelled or no_show) and it is not soft-deleted
- A booking belongs to the period containing its **check-in date**
- **Revenue** = sum of `total_price` of counted bookings (gross booking value), always a list per currency: `[{ currency: "USD", amount: "530.00" }, ...]` (amount is a decimal string, list sorted by currency, `[]` when none). Currencies are never mixed. Commission is not defined yet (`bookings.stats.commission_amount`, returns None; not reported)
- **Guests** = distinct guest accounts with at least one counted booking
- Soft-deleted properties are left out everywhere

Common query parameters: `period` = `all` (default) | `YYYY` | `YYYY-MM` (400 `{ period: [...] }` otherwise, year 2000-2100); `search` (partial, any case, inside the current list only); `page`, `page_size` (default 20, max 100). Lists are ranked by counted bookings (ties: guests, then name). Response: `{ count, next, previous, results, period, ...context }`, each row has `rank` (1-based across pages), `bookings`, `guests`, `revenue`. Staff and super-admin only (403 for customers and hotel owners)

- (SUPERSEDED 2026-10-02: see the Geography section; grouping is by refs, URLs use codes and ids) NEW `GET /api/v1/admin-panel/status/countries/` (top 100): rows `{ rank, country, hotels, bookings, guests, revenue }`. `search` matches the country name. `hotels` counts every non-deleted property of the country, with or without bookings
- (SUPERSEDED 2026-10-02) NEW `GET /api/v1/admin-panel/status/countries/{country}/regions/` (top 100): rows `{ rank, region, hotels, bookings, guests, revenue }`, plus `country`. `country` is the exact value from the countries list (URL-encoded). Properties without a region are one row `region: "Unspecified"`. Unknown country -> empty list
- (SUPERSEDED 2026-10-02) NEW `GET /api/v1/admin-panel/status/countries/{country}/regions/{region}/hotels/` (top 1000): rows `{ rank, id, name, city, status, bookings, guests, revenue }`, plus `country`, `region`. `region: "Unspecified"` lists hotels without a region. `search` matches the hotel name (English translation, else any translation, else the address)
- New indexes (migrations `bookings/0005_status_indexes`, `properties/0011_status_indexes`, schema only): bookings (status, check_in), properties (country, state)
- Additive only, no existing field or endpoint changed

## 2026-09-30 property region (Status plan S1)
- The region of a property is its existing `state` field (the partner wizard's "State/Region"); no new field. Geography levels: `country` (text) > region (`state`) > hotel. A property with no region (NULL or blank) is shown as `"Unspecified"` by the Status endpoints
- Data migration `properties/0010_backfill_property_regions`: sets `state` from `city` when `state` is empty and the city is Tashkent, Samarkand or Bukhara (case/whitespace-insensitive); never overwrites a region that is set; reverse is a no-op
- NEW `PATCH /api/v1/admin-panel/properties/{id}/region/` (staff and super-admin): `{ state: string|null }` (max 100, trimmed; blank or null clears it) -> the admin property object (same shape as `GET /admin-panel/properties/{id}/`). Only the region changes, other fields in the body are ignored. 400 `{ state: [...] }` when missing or too long, 404 for an unknown or deleted property
- Partners already set it through `state` on `POST/PATCH /partner/properties/`
- Additive only, no existing field or endpoint changed

## 2026-09-29 calendar bulk edit + bulk price edit (Phase 3 items 3.6/3.7)
- NEW `POST /partner/room-inventory/bulk/`: `{room_type, date_from, date_to, available_rooms?, is_available?}` (at least one of the two) -> array of the affected `RoomInventory` rows (same shape as `GET /partner/room-inventory/`). `date_to` is **exclusive**, the check_in/check_out convention (unlike this endpoint's own list `date_from`/`date_to` filters, which are inclusive). Creates any missing, unmanaged row (opened at the room type's full `total_rooms`) first. 400 naming the date, on `available_rooms`, if it would drop a night below what is already booked on TICKBRON; nothing is applied if any night fails. Owner's own room types only
- NEW `POST /partner/inventory/bulk-price/`: `{rate_plan, date_from, date_to, price}` -> array of the affected `DateInventory` rows (same shape as `GET /partner/inventory/`). `date_to` is **exclusive**. Creates any missing row (price = the given value, `available_rooms` defaulted to the room type's `total_rooms`, open); an existing row's other fields (rules, `booked_rooms`) are untouched, only `price` changes. Owner's own rate plans only
- `GET /partner/blocks/` accepts `room_type` (used by the calendar to load one room type's blocks)
- Additive only, no existing field or endpoint changed

## 2026-09-29 external booking blocks (Phase 3 item 3.5, audit #31)
- NEW model `properties.RoomBlock` (table `room_blocks`, new migration `properties/0009_roomblock`): rooms taken out of sale for a date range without a TICKBRON booking (external sale via Booking.com, phone, walk-in, or maintenance). Fields: `room_type`, `date_from`, `date_to` (exclusive, same convention as check_in/check_out), `rooms`, `note`, `created_by`, `created_at`
- NEW `POST /partner/blocks/` (owner's own room types only): `{ room_type, date_from, date_to, rooms, note }` -> `{ id, room_type, date_from, date_to, rooms, note, created_by, created_at }`. `created_by` is always the authenticated user, ignored if sent. Locks every affected night's RoomInventory row (materializing an unmanaged one at the room type's full `total_rooms` first) and decrements `available_rooms` by `rooms`; blocks on the same nights stack (each stacks on top of `available_rooms` as already reduced by earlier blocks/bookings). 400 `{error: {details: {rooms: ["Blocking N room(s) on YYYY-MM-DD would leave fewer than the M already booked on TICKBRON."]}}}` when a night doesn't have `rooms` free -- nothing is applied, the date is always named
- NEW `GET /partner/blocks/` (owner's own blocks only, paginated like the other partner list endpoints)
- NEW `DELETE /partner/blocks/{id}/` undoes the block: restores the blocked rooms to RoomInventory, then soft-deletes the block row (kept for audit trail, `created_by`/`created_at`/`note` preserved; excluded from `GET`/`POST` scoping by `is_deleted=False`). No PATCH/PUT -- a block is created or undone, never edited in place; those methods return 405 on an owner's own block (permission checks alone gate anonymous/other-user access, same as every other verb)
- Additive only, no existing field or endpoint changed

## 2026-09-29 room inventory partner API + public availability (Phase 3 item 3.4, audit #31)
- NEW `POST/GET/PATCH/DELETE /partner/room-inventory/` (owner sees and edits only own room types): `{ id, room_type, date, available_rooms, booked_rooms (read-only), remaining_rooms (read-only), is_available }`. `available_rooms` cannot be more than `room_type.total_rooms` (400 on `available_rooms` naming the limit, same rule DateInventory already enforces). Unique per `(room_type, date)`. `GET` accepts `room_type`, `date_from`, `date_to` filters (same shape as `/partner/inventory/`'s). This is the room type's real, shared-across-rate-plans physical room count that the booking engine locks and updates (RoomInventory, added 3.1-3.3)
- **DEPRECATED**: `available_rooms`/`booked_rooms` on `/partner/inventory/` (DateInventory) are no longer the source of truth for how many physical rooms are left -- the booking engine stopped writing them in 3.3. `/partner/inventory/` still owns price and each rate plan's own rules (open/closed `is_available`, `minimum_stay`, `maximum_stay`); use the new `/partner/room-inventory/` to see or change actual room counts
- `GET /properties/{id}/availability/`'s nested `date_inventory` items keep the same shape (`available_rooms`, `booked_rooms`, `remaining_rooms`, `price`, `currency`, `is_available`, `minimum_stay`, `maximum_stay`, `notes`), but `available_rooms`/`booked_rooms`/`remaining_rooms` are now read from RoomInventory for that room type/date (falling back to the room type's full `total_rooms`, 0 booked, when no RoomInventory row exists yet -- unmanaged, same default `quote_stay` uses). `price`/`currency`/`is_available`/`minimum_stay`/`maximum_stay`/`notes` are still DateInventory's own, per rate plan
- `GET /properties/search/` with `check_in`/`check_out`: the "has a room left" check now also reads RoomInventory for the rate plan's room type (previously only DateInventory's own, now-stale, `available_rooms`/`booked_rooms`), so a room sold out through one rate plan correctly hides every other rate plan selling the same physical room type. `is_available`/`minimum_stay`/`maximum_stay` are still checked from DateInventory
- Additive only for the new endpoint; behaviour change (bugfix) for the two read endpoints above: numbers now match what was actually booked instead of drifting from it

## 2026-09-28 partner property name (Phase 2 item 4)
- `GET /partner/properties/` and `GET/PATCH /partner/properties/{id}/` items have a read-only `name`: the English translation, else any translation, else the full address (`Property.display_name()`). Sending `name` is ignored. Additive only
- **Hotel name and description (2026-10-23).** `POST /partner/properties/` requires `translations`: `{ "uz"|"ru"|"en": { "name": string (1-255), "description": string (0-2000, optional) } }`, with at least one language and a non-blank `name` in every language sent; the response now includes `id` and `translations`. `GET/PATCH /partner/properties/{id}/` return `translations` (saved languages only); `PATCH` with `translations` replaces the languages sent and keeps the others (a deleted language row is revived); an empty object is 400. Text rules: no `<` or `>`, no control characters, digits and punctuation allowed. 400 errors sit under `error.details.translations.<language>`. Name, description and address change at once on an active hotel (no new approval); `status` and the assigned place stay locked as before. Other owners' hotels are 404, guests 403. `name` stays read-only (the display name).

## 2026-09-28 search filters (Phase 2 item 2)
- `GET /properties/search/` new query params (all optional, combine with the existing ones):
  - `features=wifi,parking` comma-separated; the property must have every flag (`wifi`=`has_wifi`, `parking`=`has_parking`, `ac`=`has_ac`, `heating`=`has_heating`, `elevator`=`has_elevator`). Unknown value -> 400 `{error, details: {features: [msg]}}`
  - `min_rating` 1-5 (one decimal): average `overall_rating` of approved, not deleted reviews >= value. Properties without approved reviews drop out
  - `sort` also accepts `reviews` (most approved reviews first). `rating` now really sorts by average rating (highest first, unrated last, more reviews wins a tie). Accepted: `relevance`, `price_asc`, `price_desc`, `rating`, `reviews`, `distance`
  - `property_type` is the type id (unchanged; the frontend used to send a slug)
- `check_in` + `check_out` now filter for real (before they were ignored): a property is returned only if one active rate plan (on an active room type) allows the stay length (`min_nights`/`max_nights`) and has an inventory row that is `is_available`, has a room left and allows the stay length (`minimum_stay`/`maximum_stay`) for every night from check_in up to, not including, check_out. Nights on two different rate plans do not combine. Same rules as `quote_stay`
- Each search result has two new fields: `average_rating` (float, one decimal, or null) and `review_count` (int)
- NEW `GET /properties/filter-options/` (public, search throttle) -> `{property_types: [{id, name, slug, count}], features: [{id, label, count}], amenities: [{id, name, slug, icon, count}], price_range: {min, max}, sort_options: [{id, label}]}`. Counts are over searchable properties (active, approved, not deleted); property types with no such property are left out; amenities are the `is_searchable` ones; `price_range` is min/max `base_price` (null when there are no properties)
- Additive only, no migration. Behaviour change: a search with dates no longer returns properties without open inventory for those nights

## 2026-09-25 hotel names instead of addresses (E2E UX 13)
- `property_name` in `GET /bookings/`, admin customer detail bookings, `GET /partner/bookings/` and notifications, and `property.name` in `GET /admin-panel/bookings/lookup/`, are now the hotel name: the English translation, else any translation, else the full address (`Property.display_name()`). Before they were the address, the city or "Property N - city". Same field names and types; only the value changed

## 2026-09-24 frontend audit follow-up (F20, F22, F23)
- DRF `PageNumberPagination` (PAGE_SIZE 20) is global. These lists are paginated `{ count, next, previous, results }`: `me/favorites/`, `me/reviews/`, `me/history/`, `admin-panel/properties/`, `admin-panel/amenities/`, `admin-panel/amenities/categories/`, `partner/properties/`, `partner/rooms/`, `partner/rates/`, `partner/inventory/`, `payments/transactions/`, `bookings/` (since 2026-10-23). These return a plain array: `admin-panel/users/`, `admin-panel/payments/transactions/`, `partner/bookings/`, `me/history/recent/`
- **Guest bookings are paginated (2026-10-23).** `GET /api/v1/bookings/` now returns `{ count, next, previous, results }` (20 per page, `?page=N`, a page past the last is 404) instead of a plain array. Newest first (`-created_at`, `-id`); `status` and `payment_status` filters apply to `count` and to every page; only the signed-in guest's own bookings. The item shape is unchanged. Breaking for any client that read the array: the web app (`accountAdapter.getBookings(status, paymentStatus, page)`, "Show more bookings" in `BookingsPage`) is updated.
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
  - Password must follow the password rule (see 2026-10-28 below) with confirmation
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
    - Customer: Full contact information (id, email, first_name, last_name, full_name, phone_number, whatsapp, telegram, preferred_contact_method, date_joined, last_login, is_active, email_verified)
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
- GET `/api/v1/me/notifications/?page=<n>` - List user's notifications, newest first
  - Auth: Session-based (required)
  - Response: paginated like every list, 20 a page: `{count, next, previous, results: [notification]}`. The notifications page loads the next page with "Show more" while `next` is not null.
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

## 2026-10-03 Admin access audit log (R4, audit #21)

### GET `/api/v1/admin-panel/audit-log/`
- Auth: staff / super-admin (`IsSuperAdminOrStaff`); anonymous, guests and hotel owners get 401/403. Read-only: POST/PUT/PATCH/DELETE return 405
- Query: `actor_id`, `target_user_id`, `target_booking_id` (integers, else 400), `action`, `page`, `page_size` (default 50, max 200)
- Response: paginated `{ count, next, previous, results: [{ id, actor_id, action, target_user_id, target_booking_id, created_at }] }`, newest first
- `action` values: `customer_list` (GET /customers/), `customer_view` (GET /customers/{id}/, target_user_id), `booking_lookup` (GET /bookings/lookup/, target_booking_id + target_user_id = guest), `user_list` (GET /users/), `status_users` (GET /status/users/)
- A row is written only when data was actually returned (2xx); 404s and permission failures write nothing. Reading the log is not recorded
- Ids only: no names, phones, emails or search terms. Rows cannot be changed or deleted (model and queryset refuse; table `admin_access_log`, migration `admin_panel/0004_admin_access_log`)

## 2026-10-03 Currency: UZS charge, CBU rate, booking snapshot (R6)

Hotels are priced in `USD` or `UZS` (property `currency`; room types, rate plans and nightly prices use the property currency). Guests are always charged in `UZS`. All money values in JSON are strings with exactly 2 decimals; UZS values are whole so'm and always end in `.00` (`"2354590.00"`). Exchange rates are strings with 6 decimals, UZS per 1 USD (`"11772.950000"`).

`exchange_rate` object (used below): `{ rate, date, source, stale }` - `date` is the CBU rate date (`YYYY-MM-DD`, null for `identity`), `source` is `cbu.uz`, `identity` (UZS, rate 1) or `legacy` (bookings made before R6, charged in their own currency), `stale` is true when the rate is older than `FX_STALE_AFTER_DAYS` (default 3).

### GET `/api/v1/properties/{id}/quote/` (added fields)
- `uzs_total`: what the guest will be charged in so'm for this stay (base total x rate, rounded once to whole so'm, half up). UZS hotel: equals `total_price`. USD hotel without any rate yet: `null`
- `exchange_rate`: the rate used, or `null` for UZS hotels and when no rate exists yet
- `total_price`, `currency`, `nights[].price` stay in the hotel's own currency

### POST `/api/v1/bookings/` (and GET list/detail; added fields)
- `charge_amount` (UZS string), `charge_currency` (`"UZS"`), `exchange_rate` object (UZS hotels: `{rate: "1.000000", date: null, source: "identity", stale: false}`)
- Set once when the booking is made (rate read in the same transaction that reserves the rooms) and never changed afterwards; a later rate change does not touch the booking, its payment or its refund limit. If the rate changed since the quote, the booking uses the current rate and returns it: the payment page must show the booking's `charge_amount`, not the quote
- The client cannot send currency, rate or amounts: extra `currency`, `charge_amount`, `exchange_rate`, `uzs_total`, `total_price` fields are ignored
- **503** `{ error: "Exchange rate unavailable", code: "exchange_rate_unavailable", details: "<message>" }` for a USD hotel when no exchange rate has ever been fetched (fresh install). Nothing is reserved; show "Booking is temporarily unavailable, please try again later"
- Bookings made before R6 have `source: "legacy"`, `charge_currency` = their own currency (USD/EUR) and `charge_amount` = `total_price`

### POST `/api/v1/payments/transactions/` (rule changed, replaces the R4 currency rule)
- `amount` must equal the booking's `charge_amount` and `currency` its `charge_currency` (`"UZS"` for every booking made since R6), else 400 `amount` / `currency`. Send exactly the booking's values
- Payme counts in tiyin (1 so'm = 100 tiyin, confirmed in Payme's documentation), Click is assumed to count in so'm (NOT verified from Click's documentation; see RELEASE_CHECKLIST "Unverified before production"): converted only inside the backend adapters, never by the frontend
- Refunds (staff): a full refund is the paid amount (the UZS snapshot), never a re-conversion; a partial refund of a UZS payment must be whole so'm (400 otherwise)

### Search and property pages (informational only)
- `GET /properties/search/` results, `GET /properties/{id}/`, `GET /properties/{id}/availability/`: + `base_price_uzs_approx` (string or `null` when no rate yet) and `uzs_rate` (`exchange_rate` object, `null` for UZS hotels). Approximate: computed from the latest rate, for display next to `base_price`; label it "≈". The amount charged always comes from the booking

### Staff: exchange rates
- `GET /api/v1/admin-panel/exchange-rates/` (staff, super-admin): paginated history `{ count, next, previous, results: [{ id, currency, rate, nominal, rate_date, source, status: accepted|rejected, note, fetched_at }] }`, newest first; query `currency`, `page`, `page_size` (50, max 200)
- `GET /api/v1/admin-panel/exchange-rates/status/` (super-admin only): `{ currencies: [{ currency: "USD", rate, date, source, stale, last_fetch: {attempted_at, success, error} | null, last_error, rejected: [<history row>] }] }`. No rate at all: `rate`/`date`/`source` null and `stale: true`. Show a warning banner when `stale` is true or `rejected` is not empty
- `POST /api/v1/admin-panel/exchange-rates/{id}/accept/` (super-admin only): accepts a rate the fetch rejected (jump over `FX_MAX_CHANGE`, default 10%). 201 with the new accepted row; 400 if the row is not `rejected`; 404 unknown id; 409 if a rate for that date is already accepted. Written to the audit log
- Audit log (`GET /admin-panel/audit-log/`): rows now have `details` (object or null); new `action` `exchange_rate_accept` with `details: { currency, rate_date, old_rate, new_rate, rejected_id, accepted_id }` and the super-admin in `actor_id`

### Display rules for the frontend
- UZS: no decimals, digits grouped by 3 with a non-breaking space, suffix `so'm` (uz, en) or `сум` (ru): `1 250 000 so'm`
- USD: `$1,250.00` (en), `1 250,00 $` (ru, uz)
- Main number = the UZS amount (`uzs_total` / `charge_amount`). For USD hotels also show `≈ $200.00` next to it and "Rate of 03.10.2026 (CBU)" near the total (from `exchange_rate.date`, shown `dd.mm.yyyy`). `stale: true` → small note "rate may be out of date"
- Search cards / property page: `base_price` in its currency plus `≈ 1 177 295 so'm` from `base_price_uzs_approx` (omit when null)

## 2026-10-06 R12 phase 1: business date, auto-completion, Refund model, notification codes

### Business date
- "Today" for bookings, statistics and auto-completion is the date in `BUSINESS_TIME_ZONE` (default `Asia/Tashkent`, UTC+5), not the server's UTC date. Server `TIME_ZONE` stays `UTC`; stored datetimes are still UTC
- `POST /api/v1/bookings/`, `GET /properties/{id}/quote/`, `GET /properties/{id}/availability/`: a check-in earlier than the Tashkent date is refused (400, same error shape as before). Before R12, between 00:00 and 05:00 Tashkent, yesterday was still accepted
- Hotels in other countries use the same business date for now

### Auto-completion of finished stays
- Every night at 00:05 Tashkent (Celery beat) bookings with status `confirmed` and `check_out` before today become `completed` (state reason `checkout_completed`, `PaymentAuditLog` `booking_status_changed`). A missed night heals itself on the next run. Pending, cancelled and no_show bookings are never touched. Frontend: a past stay now shows `completed` instead of staying `confirmed`
- `GET /api/v1/admin-panel/auto-completion/status/` (super-admin only; staff, owners, guests 403, anonymous 401/403): `{ schedule: "00:05 Asia/Tashkent", last_run: { trigger, started_at, finished_at, changed, failed } | null, waiting }`. `last_run` is the newest real run (dry runs are not recorded); `waiting` = finished stays still `confirmed` right now. Show a warning when `last_run` is null or older than a day, or `failed > 0`

### POST `/api/v1/payments/transactions/{id}/refund/` (staff; request unchanged)
- Every refund is now a `Refund` row (`payments.Refund`). Response = the payment object as before + `booking_status` + **`refund`**: `{ id, amount, currency, reason: "staff"|"cancel", status }`
- **200** `refund.status: "succeeded"`: the provider refunded it
- **202** `refund.status: "needs_manual"`: accepted, but the provider cannot refund this amount through its API (a partial refund with Payme, Click or Visa is not verified yet, see RELEASE_CHECKLIST), or the provider is not integrated. The provider was NOT called; the payment status does not change until staff mark it done. Show "Refund recorded; it must be paid by hand" and a link to the needs-attention list
- **400** `{ error: "Payment could not be refunded." }`: the provider call failed; the refund is stored as `failed` and appears in needs-attention (retry there). **Changed:** with `cancel_booking: true` the cancellation now stands (before R12 it was rolled back)
- 400 as before for a bad amount, an amount above what is left (`paid − every refund that is not failed`), non-whole so'm, or a payment that is not `completed`
- The provider is called only after the refund row is committed, never inside the database transaction

### Refunds needing attention (staff)
- Refund object: `{ id, payment_id, booking_id, booking_reference, provider, amount, currency, reason: cancel|no_show|staff, status: pending|succeeded|failed|needs_manual, error_code, provider_reference, created_at, updated_at }`. No guest name, phone or email
- `GET /api/v1/admin-panel/refunds/needs-attention/` (staff, super-admin): refunds `failed`, `needs_manual`, or `pending` for more than 1 hour; oldest first; paginated `{ count, next, previous, results }`, `page_size` 50 (max 200)
- `POST /api/v1/admin-panel/refunds/{id}/mark-done/` (super-admin only) `{ provider_reference }` (required, the bank / provider cabinet id of the manual refund): `needs_manual` → `succeeded`, the payment becomes `refunded` / `partially_refunded`. 400 `{ error, code: "not_manual" }` for any other status, 400 `provider_reference` missing, 404 unknown id. Audit log action `refund_mark_done`, `details: { refund_id }`
- `POST /api/v1/admin-panel/refunds/{id}/retry/` (super-admin only, no body): sends a `failed` refund to the provider again; 200 with the refund (`succeeded`, or `failed` again). 400 `{ error, code: "not_failed" }` for any other status, 400 `code: "limit_exceeded"` if other refunds used up the payment meanwhile, 404 unknown id. Audit log action `refund_retry`, `details: { refund_id }`
- Refunds made before R12 were backfilled as `succeeded` rows (amount from the audit log, else the full payment for `refunded`)

### Notifications (`GET /api/v1/me/notifications/` and the other notification endpoints)
- Added read-only fields `code` (string or null) and `params` (object or null). Notifications created before R12 have both null; show `title` / `message` then
- With a `code`, render your own uz/ru/en text from `code` + `params`; `title` / `message` are the English fallback. `params` contain only ids, amounts (strings), currency codes, percents and ISO dates, never personal data
- Codes (used from R12 phase 3): `no_show_report_approved`, `no_show_report_rejected` (`report_id, booking_id, booking_reference`), `no_show_marked` (`booking_id, booking_reference, amount, currency, percent`), `refund_succeeded` (`refund_id, booking_id, booking_reference, amount, currency`)
- `code` and `params` cannot be changed through PATCH

## 2026-10-06 R12 phase 2 (R12a): Status statistics

Definitions (one module, `backend/bookings/metrics.py`; admin and owner Status use the same functions). Date basis = **check-in date**; "today" = the Tashkent business date.
- **counted** = `confirmed` + `completed`, not fully refunded. `bookings` = count of counted bookings (same set as before minus fully refunded)
- **stayed** = `completed`, not fully refunded. **The new headline number** (before R12 the headline was counted)
- **guests** = SUM(`guest_count`) of counted bookings = **persons** (children included). **CHANGED:** before R12 `guests` was distinct accounts (a family of 4 on one account was 1, is now 4). The old number is `unique_customers`
- `nights` = SUM(`number_of_nights`); `room_nights` = SUM(nights × rooms)
- `upcoming` = `confirmed` with check-in after today; **not limited by the period** (the `last_*` periods end today, so future stays only show here)
- `no_show` = status no_show, not fully refunded; `no_show_reported` = has a pending no-show report (always 0 until R12b)
- `fully_refunded` = counted / no_show bookings whose every paid payment is refunded in full (succeeded refunds only); they are left out of every other number and only counted here
- **revenue** = per currency, never mixed: SUM(paid payments) − SUM(succeeded refunds) of counted + no_show bookings. **CHANGED:** before R12 `revenue` was SUM(`total_price`) in the hotel currency; that old number is now `booking_value`. A no-show keeps its money as revenue; a booking without payment rows counts with revenue 0
- `booking_status` = raw counts in the period per status: `pending, confirmed, completed, cancelled` (not expired), `expired` (cancelled because payment did not arrive in time), `no_show, no_show_reported`
- **Caveat:** "stayed" numbers for the last `NO_SHOW_REPORT_WINDOW_DAYS` (default 7) days after check-out can still change: hotels may report a no-show in that window (R12b), which moves the booking from stayed to no_show. Show a small note "the last 7 days may still change" next to stayed numbers of recent periods
- Pending, cancelled and expired are never guests, stays or revenue

Money lists everywhere: `[{currency, amount}]`, amounts strings with 2 decimals, one entry per currency.

### Periods and granularity (every Status endpoint below)
- `?period=` `all` (default) | `today` | `last_7_days` (today−6 … today) | `last_30_days` | `this_year` (1 Jan … 31 Dec) | `last_5_years` / `last_10_years` (same day N years ago + 1 … today) | `custom` with `from` and `to` (`YYYY-MM-DD`, inclusive, from <= to, at most 20 years) | `YYYY` | `YYYY-MM`. Anything else: 400 `{ period: [...] }`
- Responses carry `period` and `period_range` `{from, to}` (inclusive ISO dates; `null` for `all`)
- `?granularity=` `day` | `week` (ISO week, the bucket starts Monday) | `month` (default) | `year`; at most 1000 buckets (e.g. `day` over 10 years → 400 `{ granularity: [...] }`). Series rows: `{ period, start, bookings, guests, nights, stayed, revenue }` (`period` = `YYYY-MM-DD` for day/week, `YYYY-MM`, `YYYY`), empty buckets included with zeros; with `period=all` the series runs from the first counted check-in to today

### Existing admin Status lists (countries, regions, region hotels; shapes kept)
- Rows gain `unique_customers, nights, room_nights, stayed, booking_value`; `guests` and `revenue` use the new definitions (see CHANGED above). Responses gain `period_range`

### GET `/api/v1/admin-panel/status/hotels/` (NEW, staff + super-admin)
- Flat list of all hotels. Query: period (+from/to), `search` (hotel name in any language, address, city, region or country name in uz/ru/en, ISO country code), `country` (ISO code or `unspecified`), `region` (id or `unspecified`), `status` (`draft, pending_approval, active, suspended, rejected`; else 400), `ordering` = `revenue | bookings | guests | nights | rating | created_at`, `-` prefix for descending (default `-bookings`; unknown → 400 `{ ordering: [...] }`; `revenue` sorts by the **UZS** revenue), `page`, `page_size` (20, max 100); top 1000
- Response: paginated `{ count, next, previous, results, period, period_range, ordering }`; row `{ rank, id, name, city, region_id, region, country_code, status, created_at, rating ("4.50" or null, approved reviews), bookings, guests, unique_customers, nights, room_nights, stayed, revenue, booking_value }`
- `?export=csv`: the whole top 1000 as CSV (see CSV below)

### GET `/api/v1/admin-panel/status/hotels/{id}/` (added fields)
- `totals` now has every field of the definitions (`bookings, stayed, counted, guests, unique_customers, nights, room_nights, no_show, no_show_reported, fully_refunded, upcoming, revenue, booking_value, booking_status`)
- `period_range`, `granularity`, `series` (see above), `reconciliation`: `{ today, this_week (Mon–Sun), this_month, this_year, all_time: { from, to, counted: {bookings, guests}, stayed: {bookings, guests} } }` (by check-in date, not limited by `period`; `all_time` from/to null). `year`, `available_years`, `monthly` kept (monthly rows also have `nights`, `stayed`)

### GET `/api/v1/admin-panel/status/users/` (added fields)
- Rows gain `guests` (persons) and `nights`; `total_spent` = paid − refunded per currency (**CHANGED**, was SUM `total_price`; includes money kept from no-shows). `period_range`. `?export=csv` downloads the whole top 1000 (contains names, phones, emails: staff only, audit-logged)

### GET `/api/v1/admin-panel/status/users/{id}/` (NEW, staff + super-admin)
- `{ user: {id, full_name, first_name, last_name, phone, email, date_joined}, period, period_range, totals (as hotel detail), hotels_visited (hotels with a stay in the period), hotels: [{id, name, city, country, bookings, stayed, nights, guests, spent}], history: { count, next, previous, results: [{ id, reference, hotel {id, name}, check_in, check_out, nights, rooms, guests, status, total_price, currency, charge_amount, charge_currency, paid, refunded }] } }`
- History: every status (also pending and cancelled) with check-in in the period, newest check-in first, `page` / `page_size` (20, max 100)
- 404 for an unknown or deleted user. Audit log action `status_user_view` (target_user_id = the guest). `?export=csv` downloads the history

### Owner: `GET /api/v1/partner/status/` (added fields) and two NEW endpoints (hotel owner; own hotels only)
- Summary: + `period_range`, `granularity`, `series`, `reconciliation`, full `totals` (as admin hotel detail); `properties` rows gain `unique_customers, nights, room_nights, stayed, booking_value`. `?export=csv` = reconciliation table, one row per own hotel and window: `hotel_id, hotel, window, from, to, counted_bookings, counted_guests, stayed_bookings, stayed_guests`
- `GET /api/v1/partner/status/hotels/{id}/`: `{ hotel: {id, name, status, address, city, region, country}, period, period_range, totals, granularity, series, reconciliation, year, available_years, monthly }`. Another owner's hotel or unknown id → 404
- `GET /api/v1/partner/status/arrivals/?day=today|tomorrow` (default today, Tashkent date; else 400), optional `property` (own hotel id; another owner's → 404, not a number → 400): confirmed bookings checking in that day, paginated (50, max 100) `{ count, next, previous, results, day, date }`; row `{ id, reference, property {id, name}, guest_name, room_types: [..], rooms, nights, guests, check_in, check_out, special_requests, phone }`. The **whole phone** (as the guest gave it) so the hotel can call a late guest; no email

### CSV export (`?export=csv`)
- Same permissions and filters as the JSON. UTF-8 **with BOM**, `text/csv`, `Content-Disposition: attachment; filename="<name>.csv"`. At most `CSV_EXPORT_MAX_ROWS` (default 10000) data rows, then a final line `truncated`. Cells starting with `= + - @`, tab or CR get a leading apostrophe (spreadsheet formula injection). Money cells: `UZS 1000000.00; USD 70.00`
- Every export writes an audit-log row `export_csv` with `details: { export, rows }` (no filters, no personal data); names: `status_hotels`, `status_users`, `status_user_<id>_history`, `partner_reconciliation`
- Audit log `action` values added: `status_user_view`, `export_csv`

## 2026-10-07 R12b: no-show reports and the 50% refund

Owner endpoints need the hotel-owner role (`IsHotelOwner`), staff endpoints staff or super-admin. A guest or a visitor gets 403 / 401.

### Owner
- `GET /api/v1/partner/bookings/` — each row now also has `can_report_no_show` (bool) and `report_deadline` (`YYYY-MM-DD`, null unless reportable). Reportable = status `confirmed` or `completed`, the check-in date has passed (today > check-in, Asia/Tashkent business date), today <= check-out + `NO_SHOW_REPORT_WINDOW_DAYS` (7), and no non-withdrawn report exists. Filter `?reportable=true` keeps only those rows (any other value changes nothing). The report endpoint enforces the same rules; the flag is for the UI only.
- `POST /api/v1/partner/bookings/{id}/no-show-report/` body `{comment}` (plain text, 10-500 characters, HTML refused) -> 201 report. Throttled 20/hour per user (`THROTTLE_NO_SHOW_REPORT_RATE`).
- `GET /api/v1/partner/no-show-reports/?status=&property=` (paginated, newest first) and `POST /api/v1/partner/no-show-reports/{id}/withdraw/` (only a pending report).
- Report fields (owner): `id, booking_id, booking_reference, property_id, property_name, check_in, check_out, comment, status (pending|approved|rejected|withdrawn), decision_comment, decided_at, created_at`.

### Staff
- `GET /api/v1/admin-panel/no-show-reports/?status=&property=&from=&to=` (paginated; pending first, oldest pending first), `GET .../{id}/`, `POST .../{id}/approve|reject|reverse/` body `{decision_comment}` (10-500 characters).
- Staff rows add `decided_by_id, created_by_id, hotel_flagged` (abuse flag, see settings `NO_SHOW_FLAG_*`), `refund_preview` (`{amount, currency, percent, already_refunded, paid}` while pending, else null) and `refunds` (rows already made). No guest name, phone or email.
- `reverse`: approved -> rejected (booking restored to completed or confirmed, nights reserved again if still free, money already refunded stays refunded); rejected -> approved (normal approval).

### Errors
`{error, code}` with 400, or 404 for `not_found` (also another owner's booking or report). Codes: `not_reportable_status`, `too_early`, `window_closed`, `report_exists`, `not_pending`, `not_decided`, `booking_not_reportable`, `inventory_unavailable`, `refund_refused`. Comment problems are the usual field errors `{comment: [...]}` / `{decision_comment: [...]}`.

### Guest-facing disclosure (quote, booking create, booking detail, My bookings)
New read-only fields: `no_show_refund_percent` (int, 0 for bookings made before R12b), `no_show_refund_amount` (UZS string or null), `no_show_refund_text_key` (`no_show_refund_statement` or null), `no_show_refund_text_params` (`{percent, amount}` or null). The frontend renders the sentence from the key in the guest's language and never computes the amount. The percent is a snapshot taken at booking time (`NO_SHOW_REFUND_PERCENT`, default 50).

### Refund rules
- Approval marks the booking `no_show`, releases the future nights and refunds `percent` of what was paid in UZS, minus refunds already made, through the `Refund` model (`reason=no_show`, key `{booking_id}:no_show`). Approving twice (also two at once) refunds once.
- A no-show refund is partial, so in real mode (`PAYMENT_TEST_MODE=False`) the provider is not called and the refund is `needs_manual` (staff pay by hand, then `POST /admin-panel/refunds/{id}/mark-done/`); in test mode the fake provider performs it.
- Notifications: `no_show_report_approved`, `no_show_report_rejected` (owner), `no_show_marked` (guest, with amount) or `no_show_marked_no_refund` (percent 0). Auto-completion skips bookings with a pending report. Statistics `no_show_reported` counts pending reports.

## 2026-10-08 R12a-fix: persons next to bookings, meta business_date
Additive only, no field renamed or removed. Every headline number now exists as bookings AND as persons (persons = SUM of `guest_count`, children included). Same exclusions as the booking numbers: soft-deleted, cancelled, pending and fully refunded bookings never count.
- **`stayed_guests`**: persons of `completed` bookings in the period (the people form of `stayed`).
- **`counted_guests`**: persons of confirmed + completed bookings in the period. Always equal to the existing `guests` (kept for compatibility).
- **`upcoming_guests`**: persons of confirmed bookings with check-in after today; like `upcoming` it is never limited by the period.
- Where: `totals` of `GET /admin-panel/status/hotels/{id}/`, `/admin-panel/status/users/{id}/`, `/partner/status/` and `/partner/status/hotels/{id}/`; every row of `/admin-panel/status/countries/`, `.../regions/`, `.../hotels/` (region drill-down), the flat `/admin-panel/status/hotels/`, the owner's `properties` rows, and every row of `/admin-panel/status/users/` (`stayed_guests`, `counted_guests`, `upcoming_guests` next to `guests`). The per-hotel rows of the guest detail (`hotels`) have `stayed_guests` and `counted_guests` (no `upcoming_guests`: they are period-counted rows).
- Reconciliation blocks (today, this_week, this_month, this_year, all_time) already carried persons: `counted.guests` and `stayed.guests` next to `counted.bookings` and `stayed.bookings`. Unchanged.
- Consistency (tested): for one period, SUM(`stayed_guests`) over all users == over all hotels; a guest's per-hotel `stayed_guests` == the completed persons of that guest at that hotel.
- **Meta on every statistics response** (same level as `period` and `period_range`): `business_date` (today in Asia/Tashkent, `YYYY-MM-DD`; after 00:00 Tashkent it is already the next day) and `no_show_report_window_days` (integer, setting `NO_SHOW_REPORT_WINDOW_DAYS`, default 7: "stayed" numbers of the last N days after check-out can still change). Endpoints: countries, regions, region hotels, flat hotels, hotel detail, users, user detail (admin) and `/partner/status/`, `/partner/status/hotels/{id}/` (owner). Not on `status/arrivals/`; CSV exports are unchanged.


## 2026-10-09 R10: hotel promotions ("Reklama") - banner carousel

Only the super-admin promotes a hotel (the owner asks the super-admin outside the platform). A promotion is shown only when ALL are true: paid (`paid_at` set), status `scheduled`/`active`, today (Asia/Tashkent business date) is inside `start_date..end_date`, the hotel is active, and the optional place scope matches the hotel. No online payment: the super-admin types the agreed price (a record only) and presses mark-paid.

### Public
- `GET /api/v1/properties/search/` gets an extra key `promoted`: list (max 8, display order) of full search cards (same fields as `results` items) plus `promotion_id`. Page 1 only (`[]` on other pages). Only hotels that match the guest's own filters (text, location, price, guests, features, rating, dates) are returned. `results` and `count` are unchanged (a promoted hotel may also be in the normal list). Never fails the search: on an internal error `promoted` is `[]`.
- `GET /api/v1/promotions/home/[?country=<geography country id>]` -> `{results: [card + promotion_id]}`, max 8. 400 on a bad `country`. Not cached (each response counts views).
- `POST /api/v1/promotions/<promotion_id>/click/` -> 204; 404 if the promotion is not shown now (nothing counted). Call it when a banner is opened.
- Order: higher `priority` first; equal priority rotates, a different order each business day (stable within a day).
- Counting: a view = returned in a response; a click = the POST. One count per visitor per hour (Redis `cache.add`, key holds a salted hash, no IP/user stored). If the cache is down nothing is counted. Throttle 60/min per IP on home and click.

### Super-admin (`/api/v1/admin-panel/`; GET = staff or super-admin, every change = super-admin only)
- `GET promotion-hotels/?q=` (>= 2 chars; name, address or city) -> `{results: [{id, name, city, status, has_running_promotion}]}`, max 20, any hotel status.
- `GET promotions/` paginated (`count`, `results`); filters `q` (hotel name), `status`, `paid=true|false`, `from`, `to` (periods overlapping the range, YYYY-MM-DD), `ordering` = `start|-start|priority|-priority|clicks|-clicks` (default `-start`).
- `POST promotions/` body `{property, start_date, end_date, priority?, country_ref?, region_ref?, city_ref?, price_amount?, price_currency?, note?}` -> 201 promotion. Starts unpaid/`scheduled`.
- `GET|PATCH promotions/<id>/` (PATCH: dates, priority, scope, price_amount, price_currency, note; status, payment and hotel can never be set here).
- `POST promotions/<id>/pause/`, `resume/`, `cancel/` (body `{reason}` required), `mark-paid/`.
- `GET promotions/<id>/stats/?from=&to=` -> `{days: [{date, impressions, clicks, ctr}], totals: {...}}` (`ctr` = clicks / impressions * 100, `null` without views).
- Promotion object: `id, property {id,name,city,status}, start_date, end_date, priority, country_ref, region_ref, city_ref, price_amount, price_currency, note, paid, paid_at, status, cancelled_reason, is_shown_now, blocked_reason (null | hotel_not_active | outside_scope), total_impressions, total_clicks, created_at`.
- Errors: 400 `{error, code}` with codes `bad_dates, start_in_past, too_long (max 365 days), bad_priority (0-100), bad_price, bad_currency, note_too_long, bad_scope, overlap (same hotel, same dates), bad_status, already_paid, reason_required, reason_too_long, nothing_to_change, invalid_query`; 404 `not_found`.
- Audit (`GET audit-log/`): `promotion_create, promotion_update, promotion_pause, promotion_resume, promotion_cancel, promotion_mark_paid` (ids, dates, amount, currency only).
- Nightly task 00:10 Asia/Tashkent: expired promotions become `ended`, paid ones that started become `active` (serving never waits for it).

- `start_too_far` (start date more than 730 days ahead) is also a 400 code of `POST/PATCH promotions/`; `?country=` accepts ASCII digits only.

## 2026-10-13 OWASP batch 1 and 4: contract changes
- `GET /properties/{id}/`: the fields `owner`, `approved_by`, `approved_at`, `rejection_reason` are no longer returned (internal moderation data).
- `GET /properties/{id}/availability/`: `date_inventory[].notes` is no longer returned; rows are limited to 366 days starting at `check_in` (default: today).
- `GET /properties/search/?q=`: at most the first 8 distinct words of 2+ characters are matched.
- `POST /me/favorites/`: 400 for a hotel that is not published; `GET /me/favorites/` lists only published hotels.
- `POST /me/reviews/` and `POST /payments/transactions/`: a booking id that is not the caller's gets the same 400 ("Booking not found.") as a missing id.
- `POST /payments/webhook/{provider}/`: unknown provider -> 404; JSON body that is not an object -> 400.
- SMS limits: `POST /auth/otp/request/` has an extra IP budget (60/hour) and every number a daily budget (10/day, shared with `POST /auth/phone/verify/request/`); the logged-in phone verification endpoints are limited per account (3/min request, 5/min confirm, 20/day requests). All answer 429.

## 2026-10-14 OWASP batch 2: payments and cancellation
- `POST /payments/webhook/{provider}/`: a paid/failed message with no matching transaction, or with a different amount, answers 409 `{"error": "The payment could not be applied yet"}` (was 200); the event is stored as failed and a retry is processed.
- `POST /payments/transactions/`: an unexpected provider failure answers 502 `{"error": "The payment provider could not be reached. Please try again."}` and the transaction is `failed` (`error_code` `PROVIDER_ERROR`); `payment_method_token` containing a card number is a 400.
- `POST /bookings/{id}/cancel/`: 400 for a confirmed booking whose check-in is today or earlier.
- `POST /bookings/`, `POST /bookings/{id}/cancel/`, `POST /auth/otp/request|verify/`: a database error is a 500 (was a 400 "try again").
- `POST /admin-panel/refunds/{id}/retry/` also accepts a refund pending for over an hour.

## 2026-10-14 OWASP batch 3: probes and account history
- `GET /healthz/` -> 200 `{"status": "ok"}`; `GET /readyz/` -> 200 `{"status": "ok"}` or 503 `{"status": "unavailable"}` (database and cache). Public, outside `/api/`.
- `GET /me/history/` now also lists `login`, `logout` and `account_created` entries (with `ip_address`).

## 2026-10-14 password reset and change
- New: `POST /auth/password-reset/request/`, `POST /auth/password-reset/confirm/`, `POST /auth/password/change/`. Full contract in `.ai/contracts/auth.md` ("Password reset and change").
- Frontend routes: `/forgot-password` (e-mail form), `/reset-password?uid=&token=` (new password form), change-password section on `/profile`.

## 2026-10-17 map: property coordinates (no API change)
The search results, property detail and partner property endpoints already carry `latitude` / `longitude` (decimal, 6 places, range -90..90 / -180..180, both nullable). **They are sent as decimal strings** (`"41.311081"`), `null` when the owner has not set a location; the frontend parses them with `utils/coordinates.ts`. Partner `POST` / `PATCH` accept them as numbers. The search page map shows only the hotels that have both values; the partner wizard sets them from a map pin.

## 2026-10-17 Free cancellation and the cancellation refund (R11)
Plan: `.ai/PLAN_R11_CANCELLATION.md` (approved by the owner 2026-10-17). The rule lives in one module, `bookings/cancellation.py`; amounts are computed only on the backend, in whole so'm (UZS), ROUND_HALF_UP, from what was actually paid (completed payments), never above it and never counting what was already refunded.

**Terms.** A rate plan has `free_cancel_hours` (whole hours before the START of the check-in day in `BUSINESS_TIME_ZONE`; `null` = no free window; 0..8760) and `cancel_refund_percent` (0..100; `null` = the platform percent `CANCEL_REFUND_PERCENT`, default 50; 0 = non-refundable). A guest cancelling a PAID booking gets 100% back up to the end of the free window, otherwise `cancel_refund_percent`. Unpaid bookings have nothing to refund. The terms are copied onto the booking when it is created (`cancel_free_until`, `cancel_refund_percent_after`) and never change afterwards, whatever the owner or the setting does later. Bookings made before this change have no terms (`cancellation_terms: null`): they are cancelled as before, with no automatic refund (staff can still refund by hand).

**Public, no login**
- `GET /properties/{id}/` rate plans (`room_types[].rate_plans[]`): + `free_cancellation` (bool: the plan has a free window), `free_cancel_hours` (int or null), `cancel_refund_percent` (the plan's own or the platform percent, always a number).
- `GET /properties/{id}/quote/` + `cancellation_terms: { free_cancellation, free_until, refund_percent_after }` for THESE dates. `free_cancellation` is true only while the free window of these dates is still ahead; then `free_until` is an ISO datetime (the badge "Free cancellation until ..."), else `null`.

**Guest (login, own bookings only; another user's booking is 404)**
- Booking responses (list, detail, create, cancel) + `cancellation_terms: { free_until, refund_percent_after } | null` (the snapshot).
- `GET /bookings/{id}/cancel-preview/` -> `{ refund_amount: "2354590.00", refund_currency: "UZS", refund_percent: 100 | 50 | 0 | null, free_until: ISO | null }`: what cancelling right now would give back; nothing changes. `refund_percent: null` = the booking has no terms. 400 `{error, details}` when the booking cannot be cancelled in its state (cancelled, completed, no-show, or a stay that has started).
- `POST /bookings/{id}/cancel/` (unchanged request) -> the booking + `refund: { amount, currency: "UZS", percent }` (`amount: "0.00"` when nothing is refunded, `percent: null` for a booking without terms). Cancel and refund happen in ONE transaction: if the refund cannot be created the booking stays as it was. The refund rows are `Refund(reason="cancel")` with idempotency key `"<booking id>:cancel"` (`"<booking id>:cancel:<payment id>"` for each further payment), so a repeated or parallel cancel cannot refund twice; the provider is asked after commit (`pending` -> sent; a failed send leaves the row for staff).

**Hotel owner**
- `POST/PATCH /partner/rates/` accept `free_cancel_hours` and `cancel_refund_percent` (400 outside the ranges or for text; `null` clears). Changing a plan never changes a booking already made.

**Setting.** `CANCEL_REFUND_PERCENT` (env, 0-100, default 50; startup fails otherwise), documented in `backend/.env.example`.

## 2026-10-17 VIP rooms (R9)
Plan: `.ai/PLAN_R9_VIP.md` v2 (the owner decided: the hotel owner marks a room type as VIP or not, whenever they want; no admin approval; no search filter).
- `RoomType.is_vip` (boolean, default `false`). Migration `properties/0015_r9_room_type_vip` (additive, reversible).
- Hotel owner: `is_vip` is a normal writable field of `POST/PATCH /partner/rooms/` and is returned by `GET /partner/rooms/`. Only the owner of the hotel can change its room types (another owner, a guest and an anonymous visitor are refused as before); a value that is not a boolean is 400.
- Public: `GET /properties/{id}/` `room_types[].is_vip` and `GET /properties/{id}/availability/` `room_types[].is_vip`. **VIP room types come first in both lists**, the rest keep the usual order (by name); several VIP rooms are in name order too. Prices are unchanged: a VIP room type has its own rate plans and nightly prices.

## 2026-10-17 R12 additions, slice 1: `insights` on the hotel Status endpoints

Added field `insights` (read only, same definitions as above, one module `bookings/metrics.py`) to `GET /api/v1/partner/status/`, `GET /api/v1/partner/status/hotels/{id}/` and `GET /api/v1/admin-panel/status/hotels/{id}/`. Same period parameters as the rest of the endpoint.
- `previous_period`: `{ range: {from, to}, totals: {bookings, guests, nights, stayed, revenue} }`, the period of the same length right before; `null` for `period=all`
- `change_pct`: `{ bookings, guests, nights, stayed, revenue: [{currency, pct}] }`, strings with one decimal (`"-50.0"`); a value is `null` when the previous value was 0; the whole field is `null` for `period=all`
- `cancellation_rate`: string `"25.00"` = cancelled (not expired) / (cancelled + counted + no_show) bookings in the period; `null` without bookings
- `occupancy_rate`: string `"11.43"` = room nights (by check-in date) / (rooms of the hotel(s) x days of the period), capped at 100; `null` for `period=all` or when the hotels have no rooms. Rooms = SUM of `total_rooms` of the not-deleted room types
- `average_booking_value`: `[{currency, amount}]` per currency (booking value / bookings), `[]` without bookings
- `average_stay_nights`: string `"2.33"` = nights / bookings, `null` without bookings

### R12 additions, slice 2: owner's anonymous rank
`GET /api/v1/partner/status/hotels/{id}/` gains `rank`: `{ position, of }` or `null`. Position among the **active** hotels of the hotel's region by number of counted bookings in the period (same `period` parameters; equal numbers share a position). Only the hotel's own position and the number of hotels are returned, never other hotels. `null` when the hotel has no region, is not active, or its region has fewer than 5 active hotels.

### R12 additions, slice 3: Excel export
Every endpoint with `?export=csv` also accepts `?export=xlsx` (admin hotels list, admin guests list, guest history, owner reconciliation): same permissions, same filters, same columns, same row limit (`CSV_EXPORT_MAX_ROWS`, then a final row `truncated`). Response: `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `Content-Disposition: attachment; filename="<name>.xlsx"`. Numbers are Excel numbers, everything else is written as text, so a cell like `=HYPERLINK(...)` never runs as a formula. Audit log: same action `export_csv`, `details` gains `format: "xlsx"` (key added to `AdminAccessLog.DETAIL_KEYS`). Any other `export` value returns the normal JSON.

## 2026-10-19 R16 slice 1: prices in four currencies (USD, UZS, KZT, RUB)

Plan: `.ai/PLAN_R16_MULTI_CURRENCY.md`. The currency registry is `common/money.py` `CURRENCIES` (code -> decimals): UZS, KZT, RUB whole units, USD cents. A property can now be priced in any of the four (the default is its country's currency when supported: Kazakhstan -> KZT, Uzbekistan -> UZS, else USD).

**Owner write API** (`/api/v1/partner/rates/`, create and update): new field `prices`, an object `{ "USD": "65.00", "UZS": "800000", "KZT": "29000", "RUB": "5800" }`.
- The price in the property's currency is the plan's main price and is stored in `base_price`; the other three are stored as the owner's own prices (new table `rate_plan_prices`). When `prices` is sent, `base_price` may be left out (if sent it must equal `prices[<property currency>]`, else 400 `base_price`).
- `prices` must contain every supported currency (400 `prices`: "Enter the price in: KZT, RUB."), only supported keys, numbers >= 0, no finer part than the currency unit (whole so'm/tenge/rubles, cents for USD).
- Read: `prices` lists what the owner entered (the main price and each other currency present).
- Setting `RATE_PLAN_PRICES_REQUIRED` (env, default **true** since R16 slice 3, 2026-10-19; was false in slice 1): when true, create without `prices` is 400, and a plan without the other prices cannot be edited until `prices` is sent (400 `prices`); a complete plan can be edited without resending them.

**Hotel page** (`GET /properties/{id}/`): each rate plan gains `prices`: `{ "USD": { "amount": "60.00", "source": "main" }, "UZS": { "amount": "750000.00", "source": "owner" }, "KZT": { "amount": "29388.00", "source": "converted" }, ... }`. `source` is `main` (the plan's own currency), `owner` (entered by the owner) or `converted` (main price at the CBU rates, show with "≈"); `amount` is null when a converted price has no rate yet.

**Quote** (`GET /properties/{id}/quote/`): new optional query `currency` (UZS, USD, KZT, RUB; other value 400). The response `currency`, `nights[].price` and `total_price` are in that currency; new field `price_source` (as above). A night with its own price keeps the plan's ratio in the other currencies (+15% in dollars is +15% in so'm). The stay total is rounded once to the currency's unit. 503 `exchange_rate_unavailable` when a converted price has no rate. Without `currency` nothing changes (the plan's currency, `price_source: "main"`).
- `uzs_total` is what the guest pays in so'm: the owner's so'm price for the stay when the owner entered one (then `exchange_rate` is null), otherwise the conversion as before.

**Booking**: payment stays in so'm. When the plan has an owner so'm price, `charge_amount` is that price for the stay (no exchange rate needed, `exchange_rate_source: "owner"`, `exchange_rate` = charge / total (informational), `exchange_rate_date` null, `exchange_rate_stale` false). Without one, the CBU conversion is used as before. `total_price` and `currency` stay in the plan's currency.

**CBU**: the daily fetch now also stores KZT (code 398) and RUB (643); each currency has its own sane range (a share of `FX_MIN_RATE`/`FX_MAX_RATE`, `currency/cbu.py RATE_SANITY_SHARE`).

Slices 2 to 5 below add the per-currency "from" price on cards, the owner screens and the guest screens.

### R16 slice 3: the rule is now on
`RATE_PLAN_PRICES_REQUIRED` defaults to **true**: `POST /partner/rates/` without `prices` is 400, and a rate plan that has only its main price cannot be edited (400 `prices`) until the owner sends the other currencies. The owner screen sends `prices` (all four) and no `base_price`/`currency` on create and update. Set the variable to `false` only to roll back.

## 2026-10-19 R16 slice 2: "from" price per currency on hotel cards, night prices per currency in the calendar

- **Hotel cards** (`GET /properties/search/` results, the home promotion items and the map pins use the same serializer): new field `prices`: `{ "USD": { "amount": "54.00", "source": "main" }, "UZS": { "amount": "750000.00", "source": "owner" }, "KZT": { "amount": "29388.00", "source": "converted" }, "RUB": { "amount": null, "source": "converted" } }`. Each currency holds the **lowest price of the hotel's active rate plans in that currency** (the owner's own price, or a conversion at the CBU rate when the owner entered none; `amount` is null when a conversion has no rate yet). A hotel without active rate plans gets its own `base_price` converted. `base_price`, `currency` and `base_price_uzs_approx` are unchanged, and the price filters and the price sort still use `base_price` (the owner's property-level price).
- **Availability** (`GET /properties/{id}/availability/`): every rate plan gains `prices` (same shape as the hotel page: `{currency: {amount, source}}`), and every `date_inventory` row gains `prices`: `{ "USD": "69.00", "UZS": "862500.00", "KZT": "31050.00", "RUB": null }`, the night's price in each currency, with the plan's ratio for a night that has its own price (a night at +15% in dollars is +15% in the other currencies); null while a conversion has no rate. `price` and `currency` of the row are unchanged.
- Not included: the hotel detail's own `base_price` stays in the hotel's main currency; the hotel page prices come from `room_types[].rate_plans[].prices` (slice 1). Favorites: see below.
- **Favorites** (`GET /me/favorites/`): new field `property_prices`, the same list as a hotel card's `prices` (the lowest price of the hotel's active rate plans in every currency, `source` owner / main / converted). `property_base_price` and `property_currency` are unchanged.

## Pictures of countries and regions (2026-10-21, plan PLAN_GEO_IMAGES.md)
- Public `GET /geography/countries/` and `GET /geography/countries/{code}/regions/` rows carry `image_url` (relative media URL, or `null` when the row has no picture). Cities have none.
- Admin `/admin-panel/geography/countries/` and `.../regions/`: output has `image_url`; input `image` is accepted as multipart (JSON still works for edits without a picture). `image` is REQUIRED when creating a country or region (400 `{image: ...}`), optional on edit (no `image` = the picture stays), and can be replaced but not cleared. Checks: jpg/jpeg/png/gif/webp, 10 MB, 40 megapixels, must decode as an image. Stored name is random (`geography/countries|regions/<uuid>.<ext>`); the old file is deleted on replace and on delete.
- Multipart note: `is_active` now defaults to true when a form omits it (a form without the checkbox used to mean false).
- Existing rows (seeded countries, regions) have `image_url: null` until an admin edits them.

## Place of a hotel-owner account (2026-10-21, plan PLAN_GEO_IMAGES.md step 3)
- `POST /admin-panel/users/create-hotel-owner/` (super admin): `country_ref`, `region_ref`, `city_ref` (Geography ids) are now REQUIRED besides the old fields. They must fit together and be active (same checks as a property: 400 `{field: ...}`). The account and its place (`partner.OwnerPlace`, new table) are created in one transaction; any 400 creates nothing.
- `GET /partner/assigned-place/` (hotel owner): `{country_ref, region_ref, city_ref}` of the place, all `null` when the account has none (older accounts).
- An owner WITH a place: `POST /partner/properties/` and `PATCH /partner/properties/{id}/` refuse a `country_ref`/`region_ref`/`city_ref` that differs from it (400 `{field: "Your hotels are placed by the administrator and cannot be moved."}`); sending the same ids is fine. Owners without a place behave as before.
- A geography row used by an account's place cannot be deleted (409 from the Geography screen), only hidden.
## Person names take letters only (2026-10-21)
`full_name` (register, profile), `first_name` / `last_name` (profile, admin create-hotel-owner) and the booking's `guest_full_name` are refused with 400 (`{field: ["Names can contain letters, spaces, hyphens, dots and apostrophes only."]}`) when they contain a digit or a symbol. Letters of any alphabet, space, hyphen, dot and the apostrophes ' ʻ ʼ ’ are accepted. Existing stored names are not touched.

## Phone number is back, stored only (2026-10-22, plan PLAN_CASH_ONLY.md stage 1)
No SMS, no code, no verification, no uniqueness rule (several accounts may share a number). The number is parsed with the existing `validate_phone_number_format`: international format with a country code, separators allowed, stored as E.164 (`+998901234567`); an invalid one is 400 `{field: "Enter a valid phone number in international format, e.g. +998 90 123 45 67."}`.
- `POST /auth/register/`: `phone_number` REQUIRED.
- `PATCH /auth/me/update/`: `phone_number` can be changed, never blanked (400); not sending it leaves it as is (old accounts without a number can still edit other fields).
- `POST /admin-panel/users/create-hotel-owner/`: `phone_number` REQUIRED.
- `POST /bookings/`: the booking needs a phone: `guest_phone`, else the account's `phone_number`; neither = 400 `{guest_phone: "A phone number is required."}`.
- `GET /auth/me/` and the admin Status/customer screens already return `phone_number` / `phone` and the e-mail; the owner's arrivals list still shows only `phone_last4` (open question for stage 2: a hotel taking cash bookings needs the full number).
- **Booking rules and the arrivals phone (2026-10-23, owner decision).** (1) `POST /bookings/`: a guest holds at most **2** upcoming bookings (409 `too_many_upcoming_bookings`, as before with another number) and a new stay may not **overlap** a live (pending or confirmed) booking of the same guest: 409 `{error, code: "overlapping_booking"}`; a stay that starts the day another ends, or ends the day another starts, is allowed; cancelled bookings and other guests' bookings do not count. Both rules are checked again under the guest's row lock. A guest with invalid data now gets the 400 before the 429/409. (2) `GET /partner/status/arrivals/` rows carry `phone` (the whole number) instead of `phone_last4`; the arrivals list only covers today and tomorrow of the owner's own hotels, and no other partner list shows a phone.
- The OTP / phone-verification endpoints stay removed (404).

## Cash at the hotel: confirmed at once, arrival time, "guest arrived" (2026-10-22, plan PLAN_CASH_ONLY.md stage 2)
- `POST /bookings/`: `expected_arrival_time` ("HH:MM", REQUIRED) is the time the guest will arrive on the check-in day. 400 `{expected_arrival_time}` when it is missing, malformed, or today's time has already passed (business time, Asia/Tashkent). The booking is created `confirmed` at once (`payment_status` stays `pending` = "pay at the hotel"), the rooms are taken at once, there is no 15-minute hold (`expires_at` is null).
- Booking output (guest and admin serializers) has `expected_arrival_time` ("10:30:00" or null on old bookings), `arrived_at` (datetime or null) and `arrival_deadline` (ISO datetime in business time = arrival time + `ARRIVAL_GRACE_HOURS`, null on old bookings).
- Limit: a guest can hold at most 2 upcoming bookings (not cancelled, not arrived, check-out not past): 409 `{code: "too_many_upcoming_bookings"}` (was 429 until 2026-10-27; 429 now means throttling only) (was `too_many_pending_bookings`, 3 unpaid holds). Needed because nothing is paid up front any more.
- `POST /partner/bookings/{id}/arrived/` (hotel owner, own hotels only): the hotel says the guest arrived. 200 `{id, arrived_at}`; idempotent (the first time stays); 400 `{error}` unless the booking is `confirmed` and the check-in day has come; another owner's booking 404; guest 403.
- `GET /partner/bookings/` rows and `GET /partner/status/arrivals/` rows carry `expected_arrival_time` and `arrived_at` (arrivals: "HH:MM" or null).
- Auto-cancel: Celery task `bookings.tasks.cancel_unarrived_bookings` every 10 minutes cancels a `confirmed` booking with an arrival time, no `arrived_at`, and arrival time + `ARRIVAL_GRACE_HOURS` (default 2) passed: `status=cancelled`, `cancellation_reason="no_arrival"`, rooms released, notifications `booking_not_arrived` (guest) and `guest_not_arrived` (owner, no personal data). Bookings made before this existed have no arrival time and are never auto-cancelled.
- Migration `bookings/0012_cash_arrival`: two nullable columns, and a data step that confirms `pending` bookings still inside their payment window (expired ones stay pending for the expiry task). Reverse of the data step is a no-op.
- The payment endpoints still exist but the UI no longer uses them (removed in stage 3).

## Status numbers with cash only (stage 3a of PLAN_CASH_ONLY, 2026-10-22)

Supersedes the refund and revenue lines of the R12 definitions above; every other R12 number is unchanged.
- **counted** = `confirmed` + `completed` (no refund filter), **stayed** = `completed`, `no_show` = status `no_show`.
- **revenue** = per currency, never mixed: SUM(`total_price`) of `completed` bookings in the period (cash the hotel is expected to have received). `confirmed`, `cancelled`, `no_show`, `pending`, `expired` and soft-deleted bookings are never revenue. `booking_value` (counted bookings) is unchanged.
- **Removed:** `totals.fully_refunded`; the user-history rows (`GET /admin-panel/status/users/{id}/`) and its CSV lose `paid` and `refunded`. The hotels list ordered by revenue uses the same SUM in UZS.

## Cash only, stage 3b and 3c: no online payments, no refunds (2026-10-22)

Supersedes the payment, refund, cancellation-terms and no-show-refund parts of the sections above (R6, R11, R12, R12b). Guests pay cash at the hotel; the platform moves no money.

**Removed endpoints (404 now):**
- every `/api/v1/payments/...` route (transactions, init, confirm, refund, webhooks, audit logs)
- `GET /api/v1/admin-panel/payments/transactions/`
- `GET /api/v1/admin-panel/refunds/needs-attention/`, `POST /api/v1/admin-panel/refunds/{id}/mark-done/` and `/retry/`
- `GET /api/v1/bookings/{id}/cancel-preview/`

**Changed responses:**
- `POST /bookings/{id}/cancel/`: always free; returns the booking, no `refund` object.
- Booking, booking list, quote and rate-plan responses no longer carry `cancellation_terms`, `no_show_refund_percent`, `no_show_refund_amount`, `no_show_refund_text_key`, `no_show_refund_text_params`, `free_cancellation`, `free_cancel_hours`, `cancel_refund_percent`. Partner rate plans cannot set `free_cancel_hours` / `cancel_refund_percent` any more (the DB columns stay, unused).
- No-show reports (staff queue): no `refund_preview`, no `refunds`. Approving only moves the booking to `no_show` and releases the future nights. The guest notice is `no_show_marked_no_refund` ("marked as a no-show by the hotel"); the older notification codes stay so old rows still render.
- `GET /admin-panel/customers/`: no `total_amount_paid` (and `sort_by=total_amount_paid` is no longer valid). `GET /admin-panel/customers/{id}/`: no `payments`.
- Error code `refund_refused` of the no-show decision no longer exists.

**Removed settings:** `PAYMENT_TEST_MODE`, `PAYME_*`, `CLICK_*`, `VISA_*`, `NO_SHOW_REFUND_PERCENT`, `CANCEL_REFUND_PERCENT`, `THROTTLE_WEBHOOK_RATE`; `VITE_PAYMENT_TEST_MODE` in the frontend.
## Owner photo management (2026-10-21)
All under `/api/v1/partner/properties/{id}/photos/`, role hotel-owner, own property only (another owner's property or photo = 404, guest = 403).
- `GET .../photos/` -> list of `{id, photo, photo_url, photo_type, caption, is_primary, display_order, alt_text}` ordered by `display_order, id`; deleted photos are not listed.
- `POST .../photos/` (multipart: `photo`, `photo_type`, `caption`, `alt_text`) -> 201 with the photo. The first photo of a property becomes the cover (`is_primary` true); later ones go to the end (`display_order` = highest + 1). The stored file name is `<uuid>.<ext>`, never the client's. Limits unchanged (type/size checks, 40 megapixels, 50 photos; errors are the plain serializer errors, 400).
- `PATCH .../photos/{photo_id}/` JSON `caption`, `alt_text`, `photo_type`, `is_primary: true` (becomes the cover, the old cover is demoted). `is_primary: false` -> 400 (make another photo the cover). The image file itself cannot be replaced (delete and upload again).
- `DELETE .../photos/{photo_id}/` -> 204, soft delete; a deleted cover passes to the first remaining photo (none left = no cover).

### Status v2: owner month comparison, new insights and room types (2026-10-23)
- `GET /api/v1/partner/status/` gains `months`: `{ current: {month, range, bookings, guests, revenue}, previous: {...}, change_pct: { bookings, guests, revenue: [{currency, pct}] }, next_7_days: { bookings, guests } }`. It always covers the calendar month of the Tashkent date and the one before it (independent of `period`). `change_pct` values are strings with one decimal or `null` when last month was empty. Counted bookings (confirmed + completed) by check-in date; revenue only from completed bookings, per currency. `next_7_days` counts confirmed bookings checking in today through day 6.
- `insights` (same endpoints as before) gains `average_lead_days` (`"12.5"` or `null`: days between the booking date in Tashkent and check-in) and `repeat_guest_pct` (`"20.00"` or `null`: share of the period's unique guests with more than one counted booking).
- NEW `GET /api/v1/partner/status/rooms/?period=&property=` (hotel owner; `property` is an own hotel id, another owner's → 404, not a number → 400, bad period → 400): `{ period, period_range, rows: [{ room_type_id, name, property: {id, name}, property_id, total_rooms, bookings, room_nights, revenue: [{currency, amount}], share_pct, occupancy_rate }] }`. Every room type of the owner's hotels appears, also those with no bookings. Sorted by `bookings` desc, `room_nights` desc, name, id. `revenue` is price per night x rooms x nights of completed bookings. `occupancy_rate` is `null` for periods without bounds (`all`).

### Admin Status overview (2026-10-23)
- NEW `GET /api/v1/admin-panel/status/overview/?period=&year=` (staff and super-admin; same period values as the other Status lists; bad `period` or `year` → 400): the whole platform. `{ period, period_range, business_date, no_show_report_window_days, months, totals, insights, no_show_rate, new_users: { current_month, previous_month, in_period }, hotels: { total, active }, top_regions: [{ id, name_uz, name_ru, name_en, hotels, bookings, guests }] (5 busiest by counted bookings; id null = "Unspecified"), top_room_types: [same row as /partner/status/rooms/ plus property {id, name}] (5 busiest), year, available_years, monthly }`.
- `months`, `totals`, `insights`, `monthly` have the same shape and definitions as on `/partner/status/`, over every not-deleted hotel. `no_show_rate` is no-shows of all bookings that were not left unpaid, percent string or `null`. `new_users` counts guests (not staff) by registration date; `in_period` is `null` for `period=all`. `insights.occupancy_rate` uses the rooms of active hotels.

### Owner: room type photos (2026-10-23)
- `GET /api/v1/partner/rooms/{room_type_id}/photos/` (hotel owner; own room types only, another owner's → 404, guest 403): a plain list of the room type's photos `{ id, photo, photo_url, photo_type, caption, is_primary, display_order, alt_text }`, ordered by `display_order, id`; deleted photos are not listed.
- `POST` the same URL (multipart: `photo`, optional `photo_type`, `caption`, `alt_text`): the first photo becomes the cover (`is_primary`), new photos go to the end (`display_order` = highest + 1), the stored file name is a random uuid, the file rules are the hotel photo rules (type, size, 40 megapixels). At most **20** photos per room type (400 `{photo: [...]}`).
- `PATCH /api/v1/partner/rooms/{room_type_id}/photos/{photo_id}/`: `caption`, `alt_text`, `photo_type`, `is_primary: true` (makes it the cover; `false` is refused, the image file cannot be replaced). `DELETE` soft-deletes; a deleted cover passes to the first remaining photo.
- `GET /api/v1/partner/rooms/` and `/rooms/{id}/` gain read-only `photos_count` (live photos) and `cover_url` (the cover, else the first photo, else `null`).
- The guest page already lists `photos` per room type (`properties` detail); owner uploads now fill it.

### Ads: pictures, banner pictures and the regions panel (2026-10-23)
- `GET /api/v1/admin-panel/promotions/{id}/photos/` (staff or super-admin): `[ {id, photo_url, display_order} ]`, live photos in upload order.
- `POST` the same URL (super-admin only; multipart field `photo`): adds one picture. The file is decoded as an image first (a renamed text file → 400 `bad_image`), then the upload rules (JPG, PNG, WebP or GIF, 10 MB, 40 megapixels). At most **10** per ad (400 `too_many_photos`); only an ad that can still change (scheduled, active or paused; else 400 `bad_status`). The stored name is a random uuid under `promotions/{id}/`. Writes an audit row `promotion_photo_add` (ids only).
- `DELETE /api/v1/admin-panel/promotions/{id}/photos/{photo_id}/` (super-admin): soft delete (204; unknown or another ad's photo → 404 `not_found`); audit row `promotion_photo_remove`.
- Promotion rows (`GET /admin-panel/promotions/` and `/{id}/`) gain `photos: [{id, photo_url, display_order}]` and `photos_count`.
- `GET /api/v1/admin-panel/promotions/?region={id}`: only ads of hotels in that region (not a positive integer → 400 `invalid_query`).
- `GET /api/v1/admin-panel/promotions/regions/` (staff or super-admin): every active region `{id, country_code, name_uz, name_ru, name_en, running, waiting, hotels: [{id, name}]}`. `running` = ads shown right now, `hotels` = the hotels running them, `waiting` = paused, unpaid or not started yet (cancelled and ended ads are not counted). Regions with the most running ads first, empty regions included.
- Banner items (`GET /api/v1/promotions/home/` and `promoted` in the search response) gain `promo_photos`: up to 10 picture addresses, the ad's own pictures, else the hotel's own photos with the cover first, `[]` when there are none.

## Support chat (guests and owners with the TICKBRON team)

One thread per account (`Conversation`), newest messages by polling (no WebSocket). Text 1–2000 characters, control characters refused. Error codes: `empty`, `too_long`, `bad_text`, `invalid_query`. Throttles: send 20/min, poll 90/min.

Account (login required, `/api/v1/chat/`):
- `GET messages/?after=<id>` → `{messages: [{id, text, from_staff, created_at}], unread}`; without `after` the last 100.
- `POST messages/` `{text}` → 201 message.
- `POST read/` → 204 (marks the team's messages as read). `GET unread/` → `{unread}`.

Team (staff and super-admin, `/api/v1/admin-panel/chat/`):
- `GET conversations/?q=&unread=true&page=` → paginated `{id, user{id,name,email,role}, last_message{text≤120,from_staff,created_at}, unread, last_message_at}`.
- `GET conversations/{id}/?after=` → `{user, messages}`; `POST conversations/{id}/` `{text}` = staff reply (201); `POST conversations/{id}/read/` → 204.
- `GET unread/` → `{unread_threads}`.

Frontend: route `/support` (login required; `?topic=ads` pre-fills an advertising request for owners), admin tab "Messages" with badge, user menu link with badge, Contact page button.

### Support chat: e-mail notices (2026-10-24)
- No new endpoint and no change to the answers. When a message is saved, a Celery task `chat.tasks.send_chat_notice(message_id)` is queued after the commit; a broken queue or mail server never fails or loses the message.
- A staff reply mails the account's address (subject in Uzbek, Russian and English, link `FRONTEND_URL/support`), only for the first unread message of the run: more replies while the first is unread send nothing; after the user reads the thread, the next reply mails again. Deactivated accounts and accounts without an address get nothing.
- A user message mails `SUPPORT_NOTIFY_EMAIL` (env var, empty = off) with name, address, role and the link `FRONTEND_URL/admin`, by the same one-per-unread-run rule (the run ends when the team reads the thread).
- The e-mails never contain the text of the message, only the link.

### Stay quote: refusals with a code (2026-10-24)
- `GET /api/v1/properties/{id}/quote/` answers 400 as before (`error`, `details`, the English text under `details.availability`). When the refusal is about a night, the body also has `reason: {code, params}` so the site can say it in the user's language and format the date itself. Without a code (other refusals) there is no `reason`.
- Codes and params: `night_unavailable {date}`, `night_min_stay {date, nights}`, `night_max_stay {date, nights}`, `no_rooms_left {date}`, `few_rooms_left {date, rooms}`; `date` is `YYYY-MM-DD`. Code: `bookings/pricing.py` (`availability_reason`).
- The booking create endpoint still returns only the English text (the quote refuses first, so the guest sees the translated text on the price card).

### Refusals with a code: booking create and rate plan limits (2026-10-24)
- `POST /api/v1/bookings/` answers a refusal about a night (400, `error`, `details`) with the same `reason: {code, params}` as the quote when the refusal has a code; the English text stays in `details`.
- New codes (quote and create): `plan_min_stay {nights}` and `plan_max_stay {nights}` (the rate plan's own limits, under `details.check_in`). Full list: `night_unavailable`, `night_min_stay`, `night_max_stay`, `no_rooms_left`, `few_rooms_left`, `plan_min_stay`, `plan_max_stay`. Code: `bookings/pricing.py` (`refusal_reason`).

### Support chat: Telegram notice to the team (2026-10-24)
- When a user writes and the Telegram alert settings are on (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALERT_CHAT_ID`, the same chat as the security alerts), the chat notice task also queues one Telegram message: the user's name and role and a link to `FRONTEND_URL/admin`. No message text and no e-mail address or phone. Same one-per-unread-run rule as the e-mails; replies from the team send none. A broken Telegram queue does not stop the e-mail.

### E-mail addresses ignore capitals (2026-10-26)
- An address is the same address whatever its capitals. It is trimmed and stored in lower case when an account is made (sign-up `POST /auth/register/`, admin `POST /admin-panel/users/create-hotel-owner/`, `createsuperuser`), and compared in lower case at sign-in (`POST /auth/login/`) and password reset (`POST /auth/password-reset/request/`). The answers show the lower-case address.
- `ali@mail.com`, `Ali@Mail.com` and `ALI@MAIL.COM` are one account: signing up with another spelling of an existing address answers 400 `{"email": ["User with this email already exists."]}` as before; signing in works with any spelling.
- The database keeps it: unique constraint on `lower(email)` (`users_email_lower_unique`). Migration `users.0010_email_case_insensitive` lower-cases the stored addresses first and stops, changing nothing, with a message naming the addresses when two accounts differ only by capitals.

## Approving a hotel needs a room, a rate and a photo (2026-10-27)
- `POST /api/v1/admin-panel/properties/{id}/approve/` without `rejection_reason` (approve) now returns `400 {"error": "Property is not ready to be listed", "missing": [...]}` when the hotel lacks any of: `room` (a room type not deleted), `rate` (an active, not deleted rate plan on such a room), `photo` (a property photo not deleted). `missing` lists every absent part, in the order `room`, `rate`, `photo`. Nothing is changed on a refusal.
- Rejecting (`rejection_reason` sent) is never blocked. Suspend and reactivate are unchanged.
- Rule lives in `properties/listing.py` (`missing_for_listing`). The admin screen shows the missing parts in the page language.

## Children on a booking (2026-10-27)
- `POST /api/v1/bookings/`: `children` (ages 0-17) are part of `guest_count`, never extra people, and one guest is always an adult. So `len(children) <= guest_count - 1`; otherwise `400 {"children": [...]}` and nothing is saved. `guest_count` is still limited by the room capacity, which also bounds the list (a list of 100 ages is refused).
- Before, any number of ages was saved. `guest_count: 2` with `children: [5, 8]` (no adult) is now refused.
- Rule in `Booking.create_booking`. The booking page stops adding children at `guest_count - 1` and says why.

## Owner form limits, slugs, error text and small QA fixes (2026-10-27, QA findings F5, F7, F9, F10, F12)
- **Limits (400 naming the field)** on the partner endpoints, create and update (an update is checked together with the saved values):
  - hotel: `base_price` >= 0.01, `bedrooms` <= 50, `bathrooms` <= 20 (`max_guests` <= 50 as before);
  - room type: `base_price` >= 0.01, `base_occupancy` and `max_occupancy` <= 20, `max_occupancy` >= `base_occupancy`, `total_rooms` 1..1000;
  - rate plan: `base_price` >= 0.01, `min_nights` and `max_nights` <= 365, `max_nights` >= `min_nights` (null = unlimited);
  - nightly inventory (`/partner/inventory/`): `date` not before today in Asia/Tashkent when it is created or moved (a past night stays editable where it is), `available_rooms` <= the room type's `total_rooms`, `maximum_stay` >= `minimum_stay`.
  Constants are at the top of `partner/serializers.py`.
- **Slug is optional** on `POST /partner/rooms/` and `POST /partner/rates/`: when missing or blank it is made from `name` (`deluxe-suite`, `deluxe-suite-2`; `room` / `rate` when the name has no Latin letters) and kept unique inside the hotel / room type. A slug that is sent is used as sent; a taken one is still a 400. An update never changes the slug. The owner forms no longer show a Slug field.
- **Error `message`**: in `{"error": {"code", "message", "details"}}` the `message` is plain text (`field: text` per field, no field prefix for `non_field_errors`), never a Python dump. `details` is unchanged.
- **Sign-up**: `full_name` cannot be blank or only spaces (400 `full_name`).
- **Booking cap**: `too_many_upcoming_bookings` is now **409** (was 429, which now means throttling only).
- **Status dates**: on every owner and admin status endpoint, `from` / `to` are only valid with `period=custom`; sent with another period (or alone) they are a 400 like other bad dates.

## Refusal texts follow the page language (2026-10-27)
- Every request may carry `Accept-Language: uz`, `ru` or `en` (quality values such as `uz-UZ,uz;q=0.9,en;q=0.8` work; anything else, or no header, means English). The site sends it from the language the visitor chose, except for English, where it sends nothing. The response has `Content-Language` and `Vary: Accept-Language`.
- Validation errors, in `details` and in `message`, come in that language: Django REST framework's own texts (`This field is required.`, `Ensure this value is greater than or equal to 0.01.`, `Not found.`, ...), Django's validators, and the messages of the owner forms (`partner/serializers.py`), the shared validators (`common/validators.py`) and the picture upload checks (`common/storage.py`).
- DRF ships Russian but no Uzbek, so the project has its own catalogs: `backend/locale/uz/LC_MESSAGES/django.po` (DRF texts + project texts) and `locale/ru/LC_MESSAGES/django.po` (project texts). The compiled `django.mo` files are committed; after editing a `.po` run `python scripts/compile_po.py` (the build machines have no GNU gettext). A test fails when a `.mo` is not the compiled `.po`.
- The language is active for the request only (`common.middleware.RequestLanguageMiddleware`); tasks and other code outside a request stay in English.
- Also in the catalogs (2026-10-27): the refusal texts of bookings, accounts (favorites, reviews), users (password, session), properties (search, quote, availability), geography, currency, promotions and the admin views. A test (`common/tests/test_api_texts_translated.py`) fails when one of these modules sends a plain English sentence that is not wrapped in `gettext` or has no uz/ru translation.
- Still English: the hotel not-found answer (`properties/views.py`; the hotel page shows its own translated text), the readable texts that travel with a refusal `reason` code (booking quote and create; the site words those from the code), the status views, the generic server fallbacks (`common/exception_handlers.py`, `middleware.py`, `decorators.py`) and the dropped payments tables.
- Forms in the site (owner rooms, rates and availability, booking, profile, change and reset password, admin create-owner, promotions, sign-in, sign-up, forgot password; the booking and profile forms keep their own per-field messages) use `noValidate` and word their required/format problems from the page language (`utils/formProblem.ts`, keys `form.*`), not the browser's.

## 2026-10-27 QA round 2 fixes
- `GET /api/v1/partner/inventory/` (and the detail): `booked_rooms` and `remaining_rooms` are the rooms booked on the room type's `RoomInventory` for that night (the shared pool the booking engine locks), `remaining_rooms = max(0, available_rooms - booked_rooms)`; a night without a `RoomInventory` row shows 0 booked. Before, they were the rate plan row's own counter, which bookings never change.
- Room type `name`, `description`, `bed_configuration` and rate plan `name`, `description`, `cancellation_policy` refuse `<` and `>` and control characters, like the hotel texts (400 with the field named).
- `GET /api/v1/partner/property-types/` (hotel owner) -> `[{id, name, slug}]`, every type by name, also those with no hotel yet (the search filter list `properties/filter-options/` keeps showing only types that have hotels). The "add a hotel" form sends the chosen `property_type` id.
- New in-app notification codes (params `booking_id, booking_reference, check_in, check_out`): `booking_confirmed` (guest, when the booking is made), `new_booking` (hotel owner), `booking_cancelled_by_guest` (hotel owner). The English `title`/`message` are the fallback. Mails (uz/ru/en in one text, a link only): guest on confirmation, owner on a new booking and on a guest's cancellation; the owner's mail has the booking reference and no guest details. Sent by the Celery task `bookings.tasks.send_booking_notice`; a broken queue never fails the booking.
- Error answers have two shapes on purpose: `{error: {code, message, details}}` (DRF handler) and `{error: "text", details?, code?}` (hand-written view answers); the frontend (`utils/errorHandler.ts`) reads both.
- Local development (`DEBUG=True`): Django serves `/media/`, and the Vite dev server proxies `/media` to it. Production is unchanged (the web server serves `/media/`).

## 2026-10-27 Add an administrator from the panel; notifications page
- `POST /api/v1/admin-panel/users/create-admin/` (super-admin only; staff, guests and owners get 403). Body: `email, first_name, last_name, phone_number, password` (min 12, same rules as owner accounts), `password_confirm`. 201 -> the user (`is_staff: true`, `is_superuser: false`; a rights field in the body is ignored). 400 names the field. Written to the admin access log as action `admin_create` (new choice, migration `admin_panel/0013`, no table change). The only way to make a super-admin stays `createsuperuser` on the server.
- Frontend: `/notifications` (any signed-in account) lists the newest notices (first page of `GET /me/notifications/`), writes each one in the page language from `code` + `params` (`notification.<code>.title|message` in uz/ru/en; an unknown code shows the English `title`/`message`), opening one calls `PATCH /me/notifications/{id}/` `{is_read: true}`, "Mark all as read" calls `POST /me/notifications/mark_all_read/`. The user menu has a "Notifications" line with the unread number from `GET /me/notifications/count/` (refreshed every 60 s and when the page marks notices).

## 2026-10-28 password rule
- One rule for every password the API sets (`POST /auth/register/`, password reset confirm, change password, admin create owner/admin): at least **8** characters (was 12), at least one letter (any case, any alphabet), at least one digit and at least one special character (not a letter, digit or space). Upper and lower case are no longer required separately. Still refused: the common-password list, a password too like the e-mail or name, and the weak patterns of `StrongPasswordValidator` (`123456`, `qwerty`, `password`, `admin`, ...). 400 `{"password": [...]}` with the first broken rule in the request language (uz/ru/en). Error codes: `password_too_short`, `password_no_letter`, `password_no_digit`, `password_no_special`, `password_common_pattern`.
- Site: the same check runs in the browser first (`utils/passwordRules.ts`), the generated password always holds all three kinds. No endpoint or response shape changed.

## 2026-10-29 Administrator and staff passwords: 8 characters like everybody else
- The owner dropped the longer staff rule (people forget such passwords). One rule for every account, staff and super-admin included: at least **8** characters with a letter, a digit and a special character (see the password rule above). It holds in `POST /admin-panel/users/create-admin/`, `POST /auth/password/change/` and `POST /auth/password-reset/confirm/`. A shorter password: 400 under `password`, "Password must be at least 8 characters long." in the request language.
- Frontend: `STAFF_MIN_PASSWORD_LENGTH` is gone; every password form asks for 8. Backend: `validate_new_password(attrs)` has no `privileged` argument.

## 2026-10-28 Guest reviews: moderation and the public list
- A review is created `pending` (unchanged) and is public only after the staff approves it. Before, nothing but the Django admin could approve one, so no review ever showed.
- `GET /api/v1/me/reviews/public/?property_id=<id>` (no login): the approved, not deleted reviews of an active hotel, newest first, paginated like every list (`count, next, previous, results`, 20 a page). 400 without a whole-number `property_id`, 404 for an unknown or not active hotel. A row: `id, reviewer, stay_month, overall_rating, cleanliness_rating, location_rating, value_rating, amenities_rating, service_rating, title, comment, created_at`. `reviewer` is the first name and the initial of the last one ("Aziz K."), a single word as it is, empty without a name; never the e-mail address (`get_full_name()` falls back to it, so it is not used). `stay_month` is `YYYY-MM` of the booking's check-out or null.
- Staff (`is_staff`, same as property moderation): `GET /api/v1/admin-panel/reviews/?status=pending|approved|rejected` (default `pending`, oldest waiting first; the others newest first; 400 for another value), paginated; a row adds `property`, `property_name`, `reviewer_email`, `status`, `reviewed_at`. `POST /admin-panel/reviews/<id>/approve/` and `/reject/` set `status` and `reviewed_at`, answer the review, 404 for an unknown or deleted one, 403 for non-staff. A decision can be changed later (approved -> rejected and back). Each is written to the admin access log (`review_approve`, `review_reject`, `details {object_id, property_id}`; migration `admin_panel/0014` changes the choices only). Scores (`property_scores`) and search ratings count approved reviews only, as before.
- Frontend: the hotel page lists the guest reviews under "Guest reviews" (with "Show more reviews"), a guest sees "Pending Approval" or "Not approved" on their own review, and the admin panel has a "Reviews" tab (Waiting / Approved / Rejected, Approve / Reject).

## 2026-10-28 Guest reviews: the owner's answer and the notices
- `Review` gets `owner_reply` (text, empty = none) and `replied_at` (migration `accounts/0003`, additive). The public list (`/me/reviews/public/`) and the guest's own reviews (`/me/reviews/`) carry both fields; `replied_at` is read-only there.
- Hotel owner: `GET /api/v1/partner/reviews/[?property=<id>]` -> the approved, not deleted reviews of the owner's own hotels, newest first, paginated; a row is the public row plus `property`, `property_name`, `owner_reply`, `replied_at` (the reviewer as "Aziz K.", no address). `POST /api/v1/partner/reviews/<id>/reply/` body `{text}` (1-1000 characters, plain text: no `<` `>`) writes or replaces the answer and returns the row; 400 names `text`; 404 for a review of another owner's hotel, one that is not approved or deleted. `DELETE` on the same URL takes the answer back (204).
- New in-app notification codes (params `review_id`, `property_id`; the English `title`/`message` are the fallback, uz/ru/en text in the site): `review_approved` and `review_rejected` (to the guest, when the staff decide; only when the decision changes), `new_review` (to the hotel owner when a review is approved), `review_reply` (to the guest, for the first answer only; editing it tells nobody). A notice that cannot be stored never undoes the decision or the answer.
- Frontend: the owner's panel has a "Reviews" tab (pick a hotel, write, change or remove an answer); a review card shows "Answer from the hotel".

## 2026-10-29 Monthly ad renewal (plan `.ai/PLAN_AD_RENEWAL.md`)
- When a paid, running ad (`Promotion` in `scheduled` or `active`) reaches its `end_date`, a daily task (00:05 Asia/Tashkent) opens one **renewal** per ad and end date: "did the hotel pay for the next month?". `deadline` is the end date + 5 days. Until the deadline the ad **stays visible** (search, home banner, click counter) although its end date passed; the nightly tidy does not mark it `ended`.
- The owner gets in-app notices (type `promotion`; ids and dates only): `ad_ending` on the end day, `ad_last_warning` on day 3, `ad_renewed`, `ad_removed`. Params: `promotion_id`, `property_id`, `end_date` (the end date being renewed, or the new one for `ad_renewed`), `until_date` (the deadline).
- Answer **confirm** (the hotel paid): the same ad's end date moves one month on (the last day of the next month if it was a month's last day, else the same day next month, clamped; 31 Oct to 30 Nov, 30 Nov to 31 Dec, 15 Nov to 15 Dec). Refused with 409 `overlap` when the hotel has another ad in the added month.
- Answer **decline**, or **no answer by the deadline** (the day after it, automatically): the ad becomes `cancelled` (`cancelled_reason` "Not renewed" or "Not renewed in time"). The hotel itself is never changed.
- `GET /api/v1/admin-panel/promotions/renewals/?status=pending|renewed|declined|expired&page=` (staff or super-admin; default `pending`, nearest deadline first, the others newest answer first; 400 `{error, code: invalid_query}` for another status). Paginated (`count, next, previous, results`). A row: `id, promotion_id, property_id, hotel_name, city, address, latitude, longitude, owner_name, owner_phone, owner_email, start_date, end_date, price_amount, price_currency, ends_on, deadline, days_left, status, decided_via (panel|telegram|auto|""), decided_at`.
- `POST .../renewals/<id>/confirm/` and `.../decline/` (super-admin only; staff and others 403): answer `200` with the row; `404 {error, code: not_found}`; `409 {error, code}` with `already_decided`, `bad_status` (the ad was cancelled or paused meanwhile) or `overlap`. Written to the admin access log as `ad_renewal_confirm` / `ad_renewal_decline` (migration `admin_panel/0015`, choices only). Table `promotion_renewals` (migration `promotions/0003`, additive).
- Telegram question and buttons come in the next step; until then the answer is given in the panel.
- Frontend: a "Monthly renewals" section at the top of the Promotions area (super-admin answers, staff only look).

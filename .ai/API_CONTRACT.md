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
**DEPRECATED since 2026-10-02 (temporary backward compatibility, remove after the frontend moves to ids, G5-G6):** the old text location input on partner property writes and the name-based Status URL keys keep working next to the new ids / codes. They are marked DEPRECATED below. New code must use the ids and codes.
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
  - **DEPRECATED (2026-10-02):** instead of the ids the old text fields `country`, `state`, `city` are still accepted (also on PATCH). They are resolved through the geography mapping (uz/ru/en names and aliases, case- and apostrophe-insensitive); the region comes from the city, so `state` may be blank or wrong. `country` and `city` must match: otherwise 400 with `error.details.country` or `error.details.city` saying what was not found. When ids are sent too, the ids win and the text is ignored. On PATCH, text equal to what the property already has is ignored
- `PATCH /api/v1/partner/properties/{id}/`: the three refs (or, DEPRECATED, the text fields) are optional; refs cannot be null; the merged result is validated the same way (changing only the region while the old city stays is a 400). Responses include `country_ref`, `region_ref`, `city_ref` (ids). Editing other fields never re-validates an unchanged location
- `PATCH /api/v1/admin-panel/properties/{id}/region/` accepts `{ country_ref, region_ref, city_ref }` (the admin can fix country and city too; all three `null` clears the location -> "Unspecified"). The old `{ state }` body still works when no ref is sent. Admin property list/detail now include the three ref ids

Search: `location`, `q` and `suggestions` match the uz/ru/en names of the city, region and country through the refs ("Toshkent", "Ташкент" and "Tashkent" find the same hotel), and still match the old text fields, so unmapped hotels stay searchable. Suggestions are strings in the language that matched what was typed, for places with public hotels.

Status (replaces the 2026-09-30 admin Status URLs below; the old name keys still work, DEPRECATED): hotels are grouped by their refs; hotels without a ref are "unspecified".
- **DEPRECATED (2026-10-02):** wherever a URL key is `{code}` or `{region_id}` the old name keys are still accepted and return the same rows: a country name in any language (`Uzbekistan`, `Узбекистан`, case-insensitive) and a region name in any language (`Tashkent City`; `Unspecified` or `unspecified` for none). The response then echoes `country` / `region` exactly as sent (new format: upper-case code / region id as text); `country_name` and `region_name` are always the English names. The row fields `country` and `region` (English names) stay in the lists, so a client that builds the next URL from them keeps working
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

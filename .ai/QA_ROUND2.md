# QA round 2: all roles on a local copy

Method: local backend + frontend, a fresh admin, owner and guest. Through the API and a real browser (1440 and 390 px): the owner added a hotel, room, rate and dates; the admin approved it and ran a promotion (reklama); the guest searched, booked, cancelled. Then permission, input and load-style checks. The dev database was restored from a dump afterwards and the uploaded files deleted (0 test users left).

## Works (with evidence)
- No overbooking: 8 guests booked the last 5 rooms at once. 5 bookings confirmed, the rest refused (`bookings/models.py` locks the rows).
- Permissions: a guest and an owner get 403 on admin and partner endpoints; an owner cannot edit or see another hotel (404); a guest cannot read or cancel another guest's booking (404).
- Promotion: create, mark paid, photo, shown in the home carousel and in search `promoted`, click counted, pause hides it, resume, cancel needs a reason; the owner cannot create one (403); bad dates, negative price, priority 999 are refused.
- Booking checks: same dates twice, past dates, check-out before check-in, too many guests are refused with clear texts.
- Screens for guest, owner and admin at 1440 and 390 px: no sideways scroll, no script errors.

## Defects
1. **Owner's date list shows wrong "Booked" (medium).** After 5 real bookings `GET /partner/inventory/` still says `booked_rooms 0, remaining 5`, while `GET /partner/room-inventory/` says `booked 5, remaining 0`. The table `PartnerAvailabilityManagement.tsx:368` reads the first one. The owner would think rooms are free.
2. **Room type name accepts `<script>` (low).** Hotel names refuse `<` and `>`; the room type name does not (`POST /partner/rooms/` returned 201). React escapes it on screen, but mails and exports may not.
3. **Error answers are not one shape (low).** Booking, quote, admin approve and promotions return `{"error": "text", ...}`; the rest return `{"error": {code, message, details}}`.
4. **Admin cannot add another admin from the site (gap).** Only the server command `createsuperuser` does. The owner-creation form needs phone and country/region/city, but its docstring says phone is optional.
5. **Only one property type, "Hotel" (gap).** No hostel, guesthouse or apartment, so such places cannot list themselves honestly.
6. **No notification after a booking (gap).** Right after a booking the guest's and the owner's `notifications` lists are empty.
7. **Room photos are stored under `media/properties/temp/photos/` (low).** All hotels' room photos share one folder.
8. **Local development shows no photos (dev only).** Django serves no `/media/` when `DEBUG` is on and Vite does not proxy it. Production (Caddy/nginx) is fine.
9. The home carousel of the dev database contains `[DEMO]` hotels: the production database must never be seeded with demo data.

## Not checked
Online payment and refunds, reviews after a finished stay, real e-mail sending, real map and photo display (no network in the sandbox), two-factor login, the support chat.

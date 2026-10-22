===== PLAN: country/region pictures, "Where to?" on the home page, admin hotel account with a place (migration + file upload: WAITS FOR THE OWNER'S "ha") =====
Status: DRAFT 2026-10-21. No code changed. Owner answers already given: filter on the home page under the search; admin account creates a draft hotel in the chosen place.

## What exists
Geography admin (G5) already creates countries, regions and cities with names in three languages, but with no picture. The home page has no country filter. Creating a hotel-owner account asks only e-mail, name and password; the owner picks the place later in the wizard.

## 1. Pictures for countries and regions (migration, additive, reversible)
- `Country.image` and `Region.image`: ImageField, null/blank in the database (existing rows stay valid), REQUIRED when the super admin creates a new country or region in the screen ("name and picture are asked").
- Upload rules reused from the hotel photos: type/size check (`validate_image_file`), 40 megapixels, random `<uuid>.<ext>` stored name, replaced file is deleted from storage on change. Super-admin only (existing access matrix).
- Admin API: create/update accept multipart with `image`; public endpoints `/geography/countries/` and `/geography/countries/{code}/regions/` return `image_url` (null when none).
- Geography screen: new/edit dialog gets a picture picker with a preview; list shows a small thumbnail.
- pg_dump before the migration (checklist); migration only adds two nullable columns.

## 2. "Where to?" filter on the home page (frontend, no backend change beyond 1)
- Under the search form: country cards (picture + name in the chosen language, only countries with hotels). Clicking a country shows its regions as cards (picture + name); clicking a region opens the search for that region (the search already filters by region id). A back link returns to the countries.
- Loading, empty and error states; 390px = horizontal scroll row, 1440px = grid; keyboard and alt texts; texts in uz/ru/en. A country or region without a picture shows a neutral placeholder.

## 3. Super admin creates a hotel account with a place
- The create-account form keeps the old fields and adds a step "Where will the hotel appear": the same Country > Region > City picker as the wizard, plus the hotel name. All required.
- Backend: `POST /admin-panel/users/create-hotel-owner/` additionally takes `country_ref, region_ref, city_ref, property_name`; in ONE transaction it creates the owner and a DRAFT property in that place (validated by the existing geography check). A failed place check creates nothing.
- The owner finds the draft in "Properties" and fills the rest (rooms, rates, photos). Rule: a hotel owner can no longer change the place of a property (admin only), so the admin's choice stays; the wizard keeps the picker for new hotels the owner adds later only if the admin allows it: DEFAULT = owners keep creating hotels with their own picker, only the location of an existing property is locked.
- Tests first: account + draft created together; bad place creates nothing; guest/staff 403; owner cannot PATCH the place of a property; contract-extension of the old create-owner tests is listed in the PR.

## 4. Input rules (no gate, started already)
Names take no digits, number boxes take no letters/e/+/-, card number max 16 digits, expiry MM/YY, phones digits and a leading plus. Frontend filters plus the same rules in the backend serializers (names, card is never sent to our backend).

## Order
1 backend pictures -> 1 frontend (Geography screen) -> 2 home filter -> 3 backend + frontend admin account. Each step: tests first, full suites before the PR.

## Not in scope
Pictures for cities, cropping/resizing, drag reorder, hotel pictures changes.

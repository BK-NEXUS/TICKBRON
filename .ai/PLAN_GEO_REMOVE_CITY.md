# PLAN: remove the city level of the geography (Country > Region stays)

Status: DRAFT 2026-11-10. No code changed. It drops a database table and columns (a migration, data is lost), so the owner must approve it before any code is written.

## What the owner decided (2026-11-10)
- Keep the country ("respublika") and the region ("viloyat") as dictionaries.
- Remove everything below the region: the city dictionary (Nukus and the like) and everything built on it.
- The old city data of existing hotels may be lost.

## What exists today (facts)
- `geography.models`: `Country`, `Region`, `City` (`geo_cities`, `Region.cities`). A hotel (`Property`) has the text fields `country`, `state`, `city` and the references `country_ref`, `region_ref`, `city_ref` (`properties/models.py:104`). `Property.save` copies the English name of `city_ref` into the text `city` (`properties/models.py:181`).
- Used by: hotel creation and editing (`partner/serializers.py`, `PartnerPropertyWizard`, `LocationPicker`, `GeographyPicker`), the admin "Geography" tab with a cities level (`AdminGeography`, `AdminCityViewSet`, `/admin-panel/geography/cities/`), the public list of cities of a region (`/geography/regions/{id}/cities/`), advertising scope (`promotions.Promotion.city_ref`, `promotions/service.py:224`), search (`properties/search.py:51`, `GEOGRAPHY_LEVELS`), Status (`admin_panel/status.py:344`), the owner account's place, the demo data and the loader (`geography/data.py`, `load_geography`, `map_property_geography`, `mapping.py`), 45 test files through the helper `uzbek_location`.
- The text `Property.city` is shown in many places (reviews, favourites, bookings, search cards, the map): it is the town as written in the address.

## Design
1. The city dictionary goes: model `City`, its table, the `city_ref` columns of `Property` and `Promotion`, the public cities endpoint, the admin cities level and endpoints, the city part of the loader, the mapping command and the demo data.
2. The text field `Property.city` STAYS, as a plain "town or district" the owner types (required, like the address). It is no longer copied from a dictionary. All screens that show it keep working. Existing hotels keep the town text they already have (it was copied from the dictionary, so nothing visible is lost).
3. The region level stays and keeps its role: hotel creation asks for country and region (dropdowns) and the town (text); advertising can still be scoped by country or region; search and Status keep country and region; "Where to?" and the destinations page keep working on regions.
4. A hotel search for a town works on the text (`city__icontains`), as it already does for hotels without a reference (`properties/search.py:716`).
5. Public API: `GET /geography/regions/{id}/cities/` is removed (404). `city_ref` disappears from the hotel, owner-account and advertising bodies and answers; the town text field `city` is sent and returned as before. `.ai/API_CONTRACT.md` gets a short "Geography: cities removed" section.
6. Admin audit: the action `geography_reorder` keeps its code, its label drops "cities".

## Migrations (new files only, in this order)
1. `promotions`: remove `Promotion.city_ref`.
2. `properties`: remove `Property.city_ref`.
3. `geography`: delete model `City`.
Reversal recreates the empty table and the empty nullable columns (the structure comes back, the city data does not). `pg_dump` before running them on any database that holds real data; a new server has no hotels yet, so nothing is lost there.

## Tests (written first)
- A hotel can be created with country, region and a typed town; without the town it is refused; with a region of another country it is refused (the existing rule stays).
- `city_ref` is not accepted any more (ignored or refused, whichever the serializers do for unknown fields) and is not in any answer.
- `/geography/regions/{id}/cities/` and the admin cities routes answer 404.
- Advertising scoped by region still matches the right hotels; the scope check no longer knows cities.
- Search for a town name finds the hotel by its text.
- The helper `uzbek_location` (45 test files) gives country, region and a town text; the old city assertions are rewritten to the town text, none is deleted without a replacement that checks the same behaviour.
- Migrations: forwards, backwards and forwards again; `makemigrations --check` clean.
- Frontend: no city dropdown; a town text field with its error state; the admin Geography tab has two levels; i18n keys removed from uz/ru/en without a missing key; 390 px and 1440 px.

## Contract and docs
`.ai/API_CONTRACT.md`, `.ai/HANDOFF.md`, the loader data (`geography/data.py`) without cities, `.ai/DEPLOY_DOCKER.md` if it names `load_geography` output.

## Work list (about one working day)
Backend: models and three migrations, serializers (partner, admin, promotions, geography), views and routes, search, Status, mapping and the commands, demo data, `conftest.py` loader. Frontend: pickers, hotel wizard, owner account form, admin Geography, adapters, "Where to?" and destinations, status places, i18n. Tests: the helper and the 45 files.

## Open questions for the owner
1. The town text stays as a typed, required field of the hotel (recommended). Or no town at all, only the address line?
2. Qoraqalpog'iston stays a region like the others (Nukus is then just a typed town).
3. OK to drop the city data of the existing hotels (as answered), and for a server that already holds real hotels, a `pg_dump` is taken first.

## Not in this plan
Changing countries or regions, new levels, the promotion price rules, the map, anything outside the places listed above.

===== PLAN: picture size rules for every upload (security + how the site looks: WAITS FOR THE OWNER'S "ha") =====
Status: DRAFT 2026-11-05. No code changed. Owner request: every place that takes a picture states the size it needs and refuses a picture that does not fit, saying which size to use, so the site never shows a stretched, tiny or odd picture and the upload path is safer.

## What the code does today (evidence)
- One check for all uploads: `common/storage.py:220` `validate_image_file` (10 MB, extension .jpg .jpeg .png .gif .webp, and `file.content_type`, which is the header the client sends) and `:253` `image_upload_error` (adds a 40 000 000 pixel limit). It has no minimum size and no shape rule.
- Used by: hotel and room photos (`partner/serializers.py:735`, via `PartnerPhotoSerializer.validate_photo`), country and region pictures (`geography/admin_serializers.py:27`), ad photos (`promotions/service.py:307`).
- Hotel and room photos are re-saved at most 1600 px on the long side, EXIF removed (`common/images.py` `shrink_upload`). Ad photos and country/region pictures are stored as sent (up to 10 MB, 40 MP, camera data kept).
- The stored extension comes from the client's file name (`partner/serializers.py:726`), not from what the file really is.
- Frontend repeats the type and size check before sending (`frontend/src/utils/imageFile.ts`); no screen tells the owner which size is wanted.
- How each picture is shown (CSS): ad carousel 16:9 on phones, 16:6 and 16:5 on wide screens (`index.css:8878,9103,9109`); room card 16:9 (`panels.css:99`); hotel card a fixed 200 px height; country and region card 4:3 (`index.css:9760`); photo manager 4:3.

## Proposed rules (the numbers are for the owner to confirm or change)
| Picture | Smallest accepted | Accepted shape (width : height) | Recommended | Stored as |
|---|---|---|---|---|
| Hotel photo | 1200 x 800 px | 4:3 to 16:9 (1.33 to 1.78) | 1600 x 1067 (3:2) | max 1600 px long side (as now) |
| Room photo | 1200 x 800 px | 4:3 to 16:9 | 1600 x 1067 (3:2) | max 1600 px (as now) |
| Ad banner | 1600 x 600 px | 16:9 to 16:5 (1.78 to 3.2) | 1920 x 720 (8:3) | max 2400 px wide, EXIF removed (new) |
| Country / region picture | 800 x 600 px | 1.2 to 1.8 | 1200 x 900 (4:3) | max 1600 px, EXIF removed (new) |
Everywhere: JPEG, PNG or WebP, at most 10 MB, at most 40 000 000 pixels (all as now except GIF).

## Behaviour
- A picture outside the rules is refused, nothing is stored. The answer names what is wrong and what to send, in the page language (uz, ru, en), for example: "The picture is too small (800 x 500 px). Send at least 1200 x 800 px; 1600 x 1067 px (3:2) is best. JPG, PNG or WebP, up to 10 MB."
- The shape is checked after the camera's turn flag is applied (a phone photo can be stored sideways and shown upright), so a normal upright landscape phone photo passes.
- Pictures already stored are never touched or rechecked; only new uploads follow the rules. No migration.

## Backend (one place for the rules)
- New module `common/image_rules.py`: the table above as data (`HOTEL_PHOTO`, `ROOM_PHOTO`, `AD_BANNER`, `PLACE_PICTURE`) and one function `image_upload_error(file, rule)`. `common/storage.py` keeps the file-level checks it has now and calls it; the three callers pass their rule. Views and serializers stay thin.
- Real format check: the picture is opened with Pillow and its real format must be JPEG, PNG or WebP; the `Content-Type` header is no longer trusted; the stored file extension comes from the real format. A renamed text file, an SVG or a GIF is refused.
- Ad banners and country/region pictures go through `shrink_upload` too (size, EXIF, GPS data).
- Messages wrapped in `gettext` and added to `locale/uz` and `locale/ru` (the repository test `test_api_texts_translated` requires it).

## Frontend
- A hint under every upload box (`PartnerPhotoManager`, `RoomPhotoQueue`, `PromotionPhotosDialog`, `GeographyRowDialog`): the recommended size, the smallest size and the types, from i18n keys (uz, ru, en).
- `imageFile.ts` also reads the chosen picture's width and height in the browser and refuses it with the same message before sending, so the owner does not wait for an upload. The server stays the authority and returns its own numbers; a difference between the two never lets a wrong picture in.
- Loading, error and empty states of these dialogs keep working; 390 px and 1440 px checked in the browser.

## Tests first
- Backend: each rule (too small, wrong shape, portrait phone photo with a turn flag, exactly on the limits, GIF, SVG, text file renamed .jpg, wrong header with a real picture) for every one of the four callers; ad banners and place pictures are shrunk; the stored extension follows the real format; messages exist in uz and ru.
- Many existing tests upload tiny pictures (about 15 test files). They get a shared helper that makes a picture of a valid size; no assertion is weakened or removed. Tests of the new refusals are added, not swapped in.
- Frontend: the size read, the message, the hints.

## Docs
- `.ai/API_CONTRACT.md`: the rules table and the refusal answer of the four upload endpoints; short note in `.ai/HANDOFF.md`.

## Decisions for the owner
1. The numbers in the table (smallest size, shape, recommended size) - confirm or change.
2. GIF is dropped (an animated GIF is large and the re-save keeps one frame). Recommended: drop it.
3. Refuse a wrong picture (asked for) rather than cut it to fit automatically. Recommended: refuse; the shape range above already shows well because the site crops the middle.
4. Ad banners and place pictures start being re-saved smaller; recommended: yes.

## After this item
The design round proposed in chat (loading skeletons, soft image loading, hotel page booking panel, empty states) follows in its own branch.

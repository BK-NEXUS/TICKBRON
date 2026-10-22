===== PLAN: owner photo management (security: file upload; WAITS FOR THE OWNER'S "ha") =====
Status: DRAFT 2026-10-21. No code changed. No migration.

## Why
Owners cannot manage photos: `POST /partner/properties/{id}/photos/` exists but no screen calls it, and there is no list, delete or set-primary. Real hotels would have no photos at launch.

## Backend (all on the existing PropertyPhoto model, owner-scoped, role IsHotelOwner)
- `GET  /partner/properties/{id}/photos/` list the owner's photos (ordered display_order, id).
- `PATCH /partner/properties/{id}/photos/{photo_id}/` caption, alt_text, photo_type, `is_primary: true` (model.save already demotes the old primary). `is_primary: false` is refused (a property keeps one cover).
- `DELETE /partner/properties/{id}/photos/{photo_id}/` soft delete; if it was the primary, the first remaining photo becomes primary.
- `POST` (existing): the first photo of a property becomes primary; new photos go to the end (`display_order` = max+1).
- Predictable file names: the serializer renames the upload to `<uuid4>.<ext>` before saving. `get_media_upload_path` and its test stay untouched (no test changes).
- Other owner's property or photo = 404. Existing limits stay (5 MB/type checks in `validate_image_file`, 40 megapixels, 50 photos).
- Tests first: list/patch/delete happy paths, other owner 404, anonymous/guest 403, primary rules, delete-primary promotes next, uuid name, limits.

## Frontend
- `PartnerPhotoManager` component on the owner's property screen: file picker (multiple), per-file progress/error, grid with cover badge, "Make cover", caption edit, delete with confirm. Loading, empty and error states; works at 390px and 1440px; keyboard reachable; texts in uz/ru/en.
- Adapter methods for list/patch/delete; `uploadPropertyPhoto` reused.

## Not in scope
Reordering by drag, room-type photos, image resizing/thumbnails, serving /media in dev (production nginx, see RELEASE_CHECKLIST).

## Docs
API_CONTRACT section, HANDOFF note, remove "owners cannot upload photos" from Found-not-fixed.

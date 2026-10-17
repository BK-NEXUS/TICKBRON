===== PLAN: R9 VIP rooms, v2 (migration; WAITS FOR THE OWNER'S "ha") =====
Status: DRAFT v2 2026-10-17 (v1 had an admin approval step; the owner answered on 2026-10-17 that making a room VIP belongs entirely to the hotel owner and no admin approval is needed). No code changed. An additive migration, so it still needs the owner's "ha" (CLAUDE.md approval gate). No money rule changes, no new permission level.

## What the owner decided
- CLIENT_DECISIONS #4 (2026-10-12): VIP is a flag on the room type; no separate search filter.
- 2026-10-17: the hotel owner turns VIP on and off for their own room type, whenever they want. No super-admin or staff approval. (This replaces "approved by an admin" in #4.)

## Proposal
1. **Model:** `RoomType.is_vip` (boolean, default false, additive migration, reversible; existing rooms stay false). The separate price needs nothing new: a VIP room type already has its own rate plans and nightly prices.
2. **Owner** (`/partner/rooms/`): `is_vip` is a normal writable field of the room type form (create and edit). Rules that already protect the form apply: only the owner of the hotel can change its room types (another owner = 404/403, guests and anonymous refused).
3. **Public API:** `room_types[].is_vip` on the property page, and the booking and quote summaries can show it. Nothing else changes. No search filter.
4. **Frontend (after the backend):** a "VIP" badge on room cards (RoomSelection) and in the booking summary; a "This is a VIP room" switch in the owner's room form.
5. **No admin screen, no queue, no audit rows, no notifications:** there is no decision to make. (Decision 3 of v1, "an admin can remove VIP with a reason", belonged to the approval flow and is dropped; if abuse appears, an admin can still switch it in the Django admin, and a reporting screen can be planned then.)

## Steps (each with tests first)
S1 migration + model + Django admin column. S2 owner form: create, edit on, edit off, another owner refused, guest/anonymous refused, default false. S3 public `is_vip` on the property page, quote and booking summary + permission-matrix check + contract. S4 frontend (badge, switch). S5 HANDOFF, ROADMAP.

## One question for the owner
Should VIP rooms be listed first on the property page (above ordinary rooms of the same hotel)? [Yes: stable order, VIP first, then the current order] / [No: keep the current order, only the badge]

## Not in scope
Admin approval, a VIP search filter, price tiers or service bundles (options A, C, D of #4), hotel-wide VIP, commissions.
===== END OF PLAN =====

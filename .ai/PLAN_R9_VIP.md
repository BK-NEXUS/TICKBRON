===== PLAN: R9 VIP rooms (security + migration, WAITS FOR THE OWNER'S "ha") =====
Status: DRAFT 2026-10-17. No code changed. A new permission step (an admin approves what an owner asks for) and a migration, so it needs the owner's approval first (CLAUDE.md approval gate). No money rule changes.

## What the owner decided (CLIENT_DECISIONS #4)
Option B: VIP is a flag on the room type, set by the hotel owner, approved by an admin. "No separate search filter was chosen." (ROADMAP R9 still lists a "VIP only" filter: this plan follows the owner's answer and leaves the filter out; it can be added later without changing the model.) The separate price needs nothing new: a VIP room type already has its own rate plans and nightly prices.

## Proposal
1. **Model** (`RoomType`, additive migration, reversible, existing rows = `none`):
   `vip_status` (`none` / `requested` / `approved` / `rejected`, default `none`), `vip_decided_by` (staff user, null), `vip_decided_at` (null), `vip_rejection_reason` (text, blank). Public `is_vip` = `vip_status == "approved"`.
2. **Owner** (`/partner/rooms/`): a write-only boolean `vip_requested`. `true` moves `none` or `rejected` to `requested`; `false` withdraws a request or drops an approved VIP (back to `none`). The owner can NEVER set `approved`: `vip_status` and the decision fields are read-only for owners (mass-assignment test). The owner sees `vip_status` and the rejection reason.
3. **Admin / staff** (same permission as property moderation, `IsSuperAdminOrStaff`): `GET /admin-panel/vip-requests/` (room types waiting, with hotel and owner), `POST /admin-panel/room-types/{id}/vip/approve/`, `POST .../vip/reject/` (reason required, shown to the owner). Each decision is written to the admin audit log (`AdminAccessLog`) and records who and when. Only a `requested` room type can be decided; deciding twice is refused (409/400), so two admins cannot overwrite each other.
4. **Public API**: `room_types[].is_vip` (bool) on the property page and the quote/booking summaries carry it; nothing else about prices changes. No search filter.
5. **Frontend** (after the backend): a "VIP" badge on room cards (RoomSelection) and in the booking summary; in the owner's room form a "Request VIP status" switch with its state (waiting for approval / approved / rejected with the reason); an admin screen "VIP requests" (approve, reject with a reason), visible to staff.

## Steps (each with tests first)
S1 migration + model fields + admin registration. S2 owner write rules (request, withdraw, drop, re-request after a rejection, read-only status, mass assignment, another owner's room = 404). S3 admin queue + decisions (staff only, super-admin ok, owner/guest/anon refused, audit rows, only `requested` can be decided, reason required to reject). S4 public `is_vip` + permission-matrix rows for the new routes + contract. S5 frontend. S6 HANDOFF, ROADMAP.

## Questions for the owner (defaults in brackets)
1. May any staff member decide, or only the super-admin? [Any staff, like property moderation]
2. If the owner edits an approved VIP room (name, price, size), must an admin approve again? [No: the approval stays; an admin can still remove the badge]
3. Can an admin remove VIP from an approved room later, with a reason? [Yes: the same reject action works on an approved room and records the reason]
4. May the owner ask again after a rejection? [Yes, any time]
5. Add the "VIP only" search filter from the ROADMAP after all? [No, as the owner's answer says; a one-line filter later if wanted]
6. Notify the owner of the decision? [Not now: the frontend has no notification screen yet (the decision is visible in the room form)]

## Not in scope
A price tier or bundles of services (options A and C), hotel-wide VIP, VIP-only search, commissions.
===== END OF PLAN =====

===== PLAN: R11 free cancellation (money rule, WAITS FOR THE OWNER'S "ha") =====
Status: DRAFT 2026-10-17. No code changed. Touches refunds and a migration, so it needs the owner's approval first (CLAUDE.md approval gate).

## Why
R11 asks for a "free cancellation" badge where it is true. Today it cannot be true or false: `RatePlan.cancellation_policy` is free text, and a guest cancelling a paid booking gets NO refund (`Booking.cancel_booking` only releases inventory; staff refund by hand; CLIENT_DECISIONS #1). The owner answered #1 with "option A (by rate plan), the refund is 50%"; the free window is the open point. A badge needs a rule the backend can compute and apply.

## Proposal (the owner may change every number)
1. Two fields on `RatePlan`: `free_cancel_hours` (whole hours before check-in; empty = no free window) and `cancel_refund_percent` (0-100; default `CANCEL_REFUND_PERCENT` = 50, a setting like `NO_SHOW_REFUND_PERCENT`).
2. Rule for a guest cancelling a PAID booking, decided and computed only on the backend:
   - cancelled at least `free_cancel_hours` before check-in (the check-in day starts at the hotel's check-in time in `BUSINESS_TIME_ZONE`): refund 100% of the paid UZS charge;
   - later, or no free window: refund `cancel_refund_percent` of it;
   - unpaid or pending bookings: nothing to refund, cancelled as today.
3. Snapshot: both values are copied onto the booking when it is created (like `no_show_refund_percent`), so a later change of the rate plan never changes a booking that was already made. Bookings made before this change keep today's behaviour (no automatic refund).
4. The refund is created by the existing `create_refund(..., reason='cancellation', idempotency_key=f'{booking.id}:cancel')`: whole so'm, never more than what was paid, one per booking, audit-logged. Cancel and refund happen in one transaction; a repeated cancel request creates no second refund.
5. API (contract in `API_CONTRACT.md`, announced as READY FOR FRONTEND):
   - rate plan (search detail, quote): `free_cancellation` (bool) and, for the chosen dates, `free_cancellation_until` (datetime or null);
   - booking: `cancellation_terms` `{ free_until, refund_percent_after }` (the snapshot);
   - `GET /bookings/{id}/cancel-preview/`: `{ refund_amount, refund_currency, refund_percent, free_until }` for "if you cancel now"; `POST /bookings/{id}/cancel/` returns the same numbers it applied;
   - partner rate plan write: the two fields (validated 0-100, hours 0-8760).
6. Frontend (after the backend): badge "Free cancellation until {date}" on rate plans, the booking page and "My bookings"; "If you cancel now you get X" before the guest confirms a cancel; the two fields in the owner's rate plan form; the refund sentence in uz/ru/en (a lawyer must review the wording before launch).

## Steps (each with tests first)
S1 migration (reversible): `RatePlan.free_cancel_hours`, `RatePlan.cancel_refund_percent`; `Booking.cancel_free_until` (datetime null), `Booking.cancel_refund_percent_after` (int null; null = legacy behaviour). Setting + `.env.example` + the env guard test.
S2 pure function `bookings/cancellation.py::cancellation_refund(booking, now)` (one module, the only place with the rule): tests for the boundary hour, time zone, 0% / 100%, unpaid, legacy, already cancelled.
S3 snapshot at booking creation; plan change does not touch old bookings.
S4 cancel view applies the refund through `create_refund`, idempotent, transactional; concurrency test (two parallel cancels = one refund); access tests (only the guest).
S5 serializers + preview endpoint + partner write + permission matrix rows; contract + HANDOFF.
S6 frontend.

## Questions for the owner (defaults in brackets)
1. Does a rate plan get a free window by default? [No: only plans where the owner sets hours; everyone else gets 50% at any time, as answered]
2. Percent after the free window / without one? [50%, as answered]
3. Should the owner be able to set 0% (non-refundable, cheaper plan)? [Yes: `cancel_refund_percent` 0-100]
4. Who pays for the refund (hotel or platform) and is the commission refunded? Depends on the payment model (CLIENT_DECISIONS #5, undecided). [The refund only moves the guest's money back; settlement with hotels is out of scope until #5 is decided]
5. Real Payme/Click partial refunds are unverified in the providers' sandboxes (RELEASE_CHECKLIST). [Refund rows are created as today; provider calls stay as they are]

## Not in scope
Hotel-side cancellation, date changes, deposits (`deposit_required` stays unused), settlement reports.
===== END OF PLAN =====

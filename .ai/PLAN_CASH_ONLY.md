===== PLAN: cash at the hotel (no online payment for now) + phone number back (money + migration: WAITS FOR THE OWNER'S "ha") =====
Status: DRAFT 2026-10-22. No code changed. Owner decisions already given: (1) no card or online payment for now, the guest pays cash at the hotel; (2) the payment CODE is deleted, not switched off; (3) the booking is confirmed at once, the guest gives the time they will arrive and is told: "if you do not arrive at that time we wait 2 more hours, if you still do not come the booking is cancelled"; (4) the phone number is back: required at sign-up, in the booking, in the admin "create hotel owner" form, editable in the profile; no SMS and no verification; admins see e-mail AND phone in the Status users and customers screens.

## What the code looks like today (evidence)
- `payments` app: 2,658 lines in 11 modules (adapters for Payme/Click/Visa, webhooks, refunds, views, admin views) plus 14 test files; referenced from about 40 other backend files (bookings state machine and models, cancellation refunds R11, no-show refunds R12, Status revenue in `bookings/metrics.py` = paid payments minus succeeded refunds, partner/admin status, accounts notifications, seeds).
- Booking today: created `pending`, held 15 minutes, `confirmed` only when a payment succeeds (`bookings/models.py:657`), expired by the `expire-pending-bookings` task.
- Frontend: payment screens (`PaymentMethodSelector`, `PaymentProcessing`, `PaymentConfirmation`, `PaymentFailure`, `CardForm`), `paymentAdapter`, `utils/card.ts`, `utils/charge.ts`, `utils/paymentTestMode.ts`, the payment steps in `BookingPage`, refund notes (`CancellationNote`, `NoShowRefundNote`).
- Phone: `User.phone_number` still exists (read-only since the phone removal); nothing types it; `guest_phone` on a booking is optional; the Status screens show part of it.

## Stage 1: phone number back (no migration)
- Backend: `phone_number` accepted and validated (international format, 7-15 digits, the existing `validate_phone_number_format`) on register (required), profile update, admin create-hotel-owner (required) and booking `guest_phone` (required, prefilled from the account). Stored only: no SMS, no OTP, no verification, no uniqueness rule (two accounts may share a number, a family phone). Old accounts without a number can still sign in; they are asked for it on the next booking / in the profile.
- Frontend: a phone box (digits and a leading +, max 15) on register, profile, the booking form and the admin owner form; Status users/customers/hotel screens show e-mail and phone in full to admins.
- Tests first for every input and the admin views; the existing "phone is not accepted" tests (`test_no_phone_login.py` and similar) are replaced because they assert the opposite behaviour: listed in the PR.

## Stage 2: cash bookings with an arrival time (one additive migration)
- `Booking.expected_arrival_time` (time, required for new bookings; null for old rows) and `Booking.arrived_at` (datetime, null). Guest chooses the time in the booking form (any time, default 14:00).
- A new booking is `confirmed` at once; inventory is taken as today; the 15-minute hold and `expire-pending-bookings` go away (existing `pending` rows at deploy are confirmed by a data step or expired by the old task once, to decide: DEFAULT = confirm them).
- Notice shown in the form, on the confirmation and in "My bookings" (uz/ru/en): "If you do not arrive at {time}, we wait 2 more hours. If you still do not come, the booking is cancelled."
- The hotel owner marks "Guest arrived" (new button and endpoint, own hotels only). A task cancels a confirmed booking with no `arrived_at` once check-in date + arrival time + 2 hours has passed (Asia/Tashkent), reason `no_arrival`, inventory released, guest and owner notified. DEFAULT: the 2 hours are a setting `ARRIVAL_GRACE_HOURS=2`.
- The existing no-show report (owner reports a guest who never came) stays as the manual path; its refund part goes in stage 3.
- Tests first: confirm at once, the deadline maths across midnight and time zones, arrived bookings are never auto-cancelled, other owner cannot mark arrival, idempotent task, concurrency on inventory (same locking as today).

## Stage 3: remove online payments (no destructive migration)
- Delete: the `payments` app code (views, urls, adapters, webhooks, refunds, serializers, admin) and its tests; payment endpoints; refund calls in cancellation (R11) and no-show (R12); payment/refund settings and `.env.example` keys, `PAYMENT_TEST_MODE`, Payme/Click/Visa lines in RELEASE_CHECKLIST; payment parts of seeds and smoke scripts; frontend payment screens, adapters, utils, the payment steps of `BookingPage`, refund notes and the test-card form.
- Keep (no data loss): the database tables and columns (`payment_transactions`, refunds, booking charge snapshot, `payment_status`), so nothing is dropped; a later, separately approved migration can drop them. The models stay as plain tables with no code using them, or are removed from Django with `managed=False` state migration: DEFAULT = keep the models, delete everything else.
- Status revenue: no paid payments exist any more, so revenue becomes "cash expected" = SUM of `total_price` of bookings that are `completed` (the owner marks arrival or the stay ends), per currency, never mixed; bookings cancelled or auto-cancelled count nothing. DECISION NEEDED if the owner wants another definition (for example confirmed bookings too).
- Cancellation: the guest can still cancel; no refund exists, so the free-cancellation percent and hours (`free_cancel_hours`, `cancel_refund_percent`) stop meaning money; the "free cancellation" badge and notes are removed. DEFAULT: cancelling is always free and just releases the room.
- Charge currency / owner so'm price logic (R16) that existed for charging: prices stay as the display (all four currencies) but nothing is charged online; the exchange-rate task stays for the "≈" display.

## Order and cost
Stage 1 (about half a day) -> Stage 2 (about a day) -> Stage 3 (the largest: 40 backend files, 15+ frontend files, about 40 test files to delete or rewrite). Each stage: tests first, full backend and frontend suites, browser check at 1440 and 390 px, its own PR.

## Risks
- Stage 3 deletes tests of payment behaviour on purpose (not weakening: the behaviour is removed by the owner's decision); each deleted file is named in the PR. Every other test stays.
- Real Payme/Click/Visa integration later means re-adding the code from git history (it stays recoverable in git).
- Auto-cancelling confirmed bookings is only as good as the hotel pressing "Guest arrived": hotels must be told (launch checklist) or arriving guests get cancelled. Alternative if the owner prefers: the task only FLAGS the booking for the hotel and never cancels. DEFAULT = cancel as the owner said.

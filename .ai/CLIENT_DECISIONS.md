# CLIENT DECISIONS needed (sent to the client as a Word file, 2026-10-12)

Status: ANSWERED in part (2026-10-12, by the owner). Recommendations are mine.

## Answers received
1. Cancelling a paid booking: option A (by rate plan); the refund is 50%. Open points: does 50% apply at any time before check-in, and is there a free-cancellation window? Default until told otherwise: 50% at any time, a rate plan may override percent and window.
2. Who refunds: not decided by the owner, asked for advice. My advice: super-admin only, reason mandatory (cancellation and no-show refunds become automatic rules, so manual refunds are exceptions).
3. No-show: option A (keep 50%, 7 days, staff decide).
4. VIP: option B (a flag on the room type, set by the hotel owner, approved by an admin). No separate search filter was chosen.
5. NEW and undecided: how hotels are paid. The owner has no plan yet: either each hotel registers its own card/merchant (like Uzum Market sellers) and money goes to it, or all money goes to the platform account and the admin pays the hotels monthly. My advice: platform account first, monthly payouts (one provider contract, simple refunds); needs commission, a per-hotel balance ledger, monthly statement, "paid" records and CSV, owner balance screen. Needs an accountant/lawyer opinion on holding third-party funds. Needs its own approved plan before any code.

## Original questions

| # | Decision | Today | Options | Recommendation | Answer |
|---|---|---|---|---|---|
| 1 | Cancelling a paid booking (N-16) | The guest can cancel any non-terminal booking at any time; inventory is released (`Booking.cancel_booking`); no refund is created (staff can refund by hand) | A by rate plan: free-cancellation deadline + refund percent; B one rule for all; C no cancellation after payment | A, default 100% refund until 48 h before check-in, then 0%, per rate plan; amount computed on the backend | |
| 2 | Who may refund (N-14) | Any `is_staff` user creates a refund (`payments/views.py:327`); retry/mark-done are super-admin only | A super-admin only; B staff up to a limit, above that super-admin; C all staff but reason mandatory and logged | B, reason always mandatory; audit logging is added anyway (step 2a) | |
| 3 | "Kelmadi" (no-show) rules | Owner reports within 7 days (`NO_SHOW_REPORT_WINDOW_DAYS`), staff decide, guest gets 50% (`NO_SHOW_REFUND_PERCENT`) | A keep; B other percent/window | A first, review after real cases | |
| 4 | VIP room | No such concept | A price tier; B room-type flag set by owner, approved by admin; C bundle of extra services; D search filter and list | B + D; services later | |
| 5 | Other | n/a | commission and payment model; map service (Google/Yandex/OpenStreetMap); logo files; Telegram bot token; discount types (R10b); register form fields (client asked for name, phone, email: is a password needed?) | n/a | |

What each answer changes in the code is planned in `.ai/PLAN_*.md` when the answer arrives (money rules need an approved plan first).

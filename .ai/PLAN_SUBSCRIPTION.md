# Plan: monthly hotel fee, reminders and the Telegram question (needs approval: it is about money)

Hotels pay the platform a fixed monthly fee. Today nothing tracks it. This plan adds the tracking, the reminders and the "did they pay?" question to the super admin in Telegram. Payment itself stays outside the site (cash or transfer); the super admin only records it. No card payment, no SMS (paid service): reminders go by in-app notice and e-mail.

## Decided by the owner
- One amount for every hotel (a setting the super admin can change; a change counts for the fees created after it).
- The fee is due on the 1st of each month.
- The first month is free.

## Rules (proposal, please confirm the marked ones)
1. **Free period (confirm):** 30 days from the day the hotel becomes `active`. The first fee is due on the first 1st-of-the-month after those 30 days. Example: approved 15 Oct, free until 14 Nov, first fee due 1 Dec. Hotels that are already active when this ships get the same 30 days from the deploy day.
2. **Fee row:** on the 1st a daily task creates one fee per active hotel whose free period has ended (amount copied from the setting, so history never changes). One row per hotel and month.
3. **Reminders to the owner** (in-app notice, plus e-mail once SMTP exists): on the due day, 3 days later, and on day 5 as the last warning ("your hotel will be hidden").
4. **Waiting time:** 5 full days after the due date nothing happens to the hotel. The super admin can confirm in the panel at any time in this window.
5. **The question (day 6, still unpaid):** the bot sends the super admin one message: hotel name, city and address, owner name, phone and e-mail, the amount and months unpaid, the number of upcoming bookings, a map location pin, and two inline buttons: **[Ha, to'lagan]** / **[Yo'q, to'lamagan]**.
6. **No answer:** the hotel is never hidden on its own. The bot repeats the question every 24 hours until somebody answers.
7. **Ha:** the fee becomes `paid` (who, when, via Telegram). If the hotel was hidden for this fee it is shown again.
8. **Yo'q (confirm: hide, do not delete):** the hotel gets the existing `suspended` status (not shown in search, no new bookings), the owner is told by notice and e-mail. Nothing is deleted, so paying later restores everything. Bookings already confirmed stay valid and stay visible to the owner and the guest (confirm).
9. Only a hotel suspended by this rule is restored automatically on payment; a hotel suspended by moderation stays suspended.

## Backend (new app `subscriptions`, additive migration, reversible)
- `FeeSettings` (single row): `monthly_amount` (whole UZS).
- `HotelFeeAccount`: `property` (one to one), `free_until`. Created when a hotel is approved (and for existing active hotels by a one-time command).
- `MonthlyFee`: `property`, `month` (first day), `amount`, `status` (`due`, `paid`), `paid_at`, `confirmed_by` (nullable user), `confirmed_via` (`panel`, `telegram`), `note`, `reminders_sent`, `asked_at`, `suspended_property` (bool). Unique on property and month.
- Daily Celery beat task (06:00 Tashkent): create fees, send reminders, send/repeat the question. Idempotent: a re-run sends nothing twice.
- Service module `subscriptions/services.py` holds every rule; views, the task and the bot handler stay thin.
- Notification codes (ids, amounts and dates only, as `accounts.notify` requires): `fee_due`, `fee_overdue`, `fee_last_warning`, `fee_paid`, `property_hidden_unpaid`. Texts in uz/ru/en.
- Telegram: new `TELEGRAM_ADMIN_CHAT_ID` and `TELEGRAM_WEBHOOK_SECRET`. Webhook `POST /api/v1/subscriptions/telegram/webhook/`: the secret header is compared in constant time; only taps from the admin chat are accepted; the button data carries the fee id and the answer only; a second tap is answered with the first result (idempotent). A management command sets the webhook. It needs a public https address, so the live bot test happens after the domain; until then tests post fake Telegram payloads.
- Super admin API (`/api/v1/admin-panel/fees/`): list by month (search, status filter), confirm paid, undo a confirmation, read and change the amount. Every change goes to the admin access log. Staff may only list.
- Owner API (`/api/v1/partner/fees/`): own hotels' fee state and history (read only).

## Frontend
- **Super admin:** new "Payments" tab: month picker, table (hotel, city, owner contact, amount, status, days late), search and status filter, a map with the hotels and their state, "Mark as paid" and "Undo", the amount setting. All texts through i18n (uz/ru/en), loading, empty and error states, works at 390 and 1440 px.
- **Helper admin (staff):** same list, read only, plus a "Send reminder" button (once per 24 hours per fee). They cannot confirm money. Also worth adding for them later: a daily to-do (hotels waiting for approval, reviews to moderate, unpaid hotels).
- **Hotel owner:** new "My payments" tab: amount, status, due date, end of the free period, history, and a banner with the days left when late.

## Tests first (examples)
Free period and first due date; one fee per hotel and month, none twice; reminder days; nothing happens during the 5 days; the question only on day 6; repeated daily, never auto-hide; "Ha" and "Yo'q" through a fake webhook (wrong secret, wrong chat, a repeated tap, an unknown fee); hiding removes the hotel from search and blocks new bookings but keeps confirmed ones; restore only for fee-caused suspensions; permission matrix (super admin, staff, owner, guest, anonymous); the amount is never taken from a request.

## Delivery in three pull requests
1. Models, daily task, owner notices, super admin Payments tab (confirm by hand). No bot yet.
2. Telegram question, buttons, hide and restore.
3. Owner "My payments" tab and the staff read-only view with reminders.

## Not in this plan
Card payment, SMS, invoices or receipts, refunds, a different amount per hotel, several people answering in the bot.

## Needed from the owner's side
- The amount in UZS.
- A bot from @BotFather (free) and the super admin's chat id.
- SMTP for e-mail (until then reminders are in-app only), and the domain for the live bot.
- A short written agreement with the hotels about the monthly fee and the hiding rule (lawyer).

## Decide
1. Free period as in rule 1?
2. Hide, not delete (rule 8)? Confirmed bookings stay valid?
3. Bot messages go to one super admin chat (proposed)?
4. Reminder days 0, +3, +5 fine?

# Plan: monthly ad renewal, reminders and the Telegram question (replaces the monthly hotel fee plan)

A hotel pays the platform once, when it joins the site (outside the site, nothing to track here). What repeats every month is the **ad** in the banner (`Promotion`, R10): a hotel asks the super admin, the super admin creates a paid period for it. This plan adds the renewal: when the ad's month ends the owner is told, the super admin is asked whether the hotel paid again, and the ad is removed if nobody confirms in 5 days. Hotels are never hidden or deleted by any of this.

## Decided by the owner (2026-10-29)
- The hotel pays for the site once, at the start. No monthly hotel fee, no free month, nothing about hiding or deleting a hotel.
- The ad is paid monthly. An ad is created by the super admin on the hotel's request (as today).
- **The ad's end day:** the owner is told, the super admin is asked in Telegram "did this hotel pay for the next month?" with **[Ha]** / **[Yo'q]**. The ad **stays visible for 5 more days** while the answer is open.
- **Ha:** the same ad's end date moves one month on. **Yo'q**, or no confirmation within 5 days: the ad is removed from the banner automatically (status `cancelled`, reason "Not renewed"). The hotel itself is untouched.
- Telegram message: hotel name, place, owner contact, the ad's region and dates, the agreed amount, a map location pin.

## My defaults (tell me if you want them different)
- Owner reminders (in-app notice, plus e-mail once SMTP exists): on the end day and on day 3 ("2 days left").
- One month = the next calendar month: an ad that ends on the last day of a month moves to the last day of the next month, any other end day moves to the same day next month (31 Oct to 30 Nov, 15 Nov to 15 Dec).
- Only ads that were paid and are running (`scheduled` or `active`) are asked about. Paused, cancelled, ended or never paid ads are not.
- If the extension would overlap another ad of the same hotel, the confirmation is refused with a clear message.
- The super admin can also confirm or remove in the panel at any time in the 5 days. Staff only look.

## Backend (app `promotions`, additive migration, reversible)
- New model `AdRenewal`: `promotion`, `ends_on` (the end date being renewed), `deadline` (`ends_on` + 5 days), `status` (`pending`, `renewed`, `declined`, `expired`), `reminder_stage`, `decided_by`, `decided_via` (`panel`, `telegram`, `auto`), `decided_at`. Unique on (`promotion`, `ends_on`): a second run never asks twice.
- `promotions/renewals.py` holds every rule: `open_due(today)`, `send_reminders(today)`, `expire_overdue(today)`, `confirm(renewal, actor, via)` (extends the end date), `decline(renewal, actor, via)` (cancels the ad), `run_daily(today)`.
- A pending renewal keeps the ad visible: `shown_now()` / `is_shown_now()` also accept an ad whose end date passed while its renewal is pending and `deadline` has not; `tidy_statuses()` does not mark such an ad `ended`.
- Daily Celery beat task at 00:05 Asia/Tashkent (just before the 00:10 tidy): opens the renewals, sends the notices, expires the overdue ones. Idempotent.
- Notification codes (ids and dates only): `ad_ending`, `ad_last_warning`, `ad_renewed`, `ad_removed`. Texts in uz/ru/en.
- Super admin API under `/api/v1/admin-panel/promotions/renewals/`: list (`?status=`, default `pending`, nearest deadline first), `POST .../<id>/confirm/`, `POST .../<id>/decline/`. Audit log rows for both. Staff may list.
- Telegram (step 2): new `TELEGRAM_ADMIN_CHAT_ID` and `TELEGRAM_WEBHOOK_SECRET`; webhook `POST /api/v1/promotions/telegram/webhook/`: secret header compared in constant time, only the admin chat accepted, button data holds the renewal id and the answer only, a repeated tap answers with the first result. The live bot needs the domain; until then tests post fake payloads.

## Frontend
- Admin panel, Promotions area: a "Renewals" section: ads waiting for an answer (hotel, place, dates, deadline and days left, agreed amount, owner contact, a map link), buttons **Paid, extend one month** and **Remove ad now**, a status filter for the history. Texts through i18n (uz/ru/en), loading, empty and error states, 390 and 1440 px.
- Hotel owner: the notices appear on the notifications page (new codes). A "My ads" view for owners is a later step.

## Tests first (examples)
Renewal opened once on the end day, not before, not twice; only paid running ads; reminder days; the ad is still shown on days 1 to 5 and gone after the deadline; confirm moves the end date (month-end rule, overlap refused); decline and expiry cancel the ad and notify; tidy does not end an ad with a pending renewal; the fake Telegram webhook (wrong secret, wrong chat, repeated tap, unknown id); permission matrix; nothing touches the hotel's own status.

## Delivery in three pull requests
1. Renewal model, rules, daily task, notices, super admin API and the Renewals section (no bot).
2. Telegram question and buttons.
3. Staff read-only view and a "My ads" view for owners.

## Not in this plan
Card payment, SMS (paid service), tracking the one-time hotel payment, invoices, refunds, hiding or deleting hotels.

## Needed from the owner's side
A bot from @BotFather (free) and the super admin's chat id; SMTP for e-mail (until then the notices are in-app only); the domain for the live bot; a short written agreement with advertisers about the monthly payment and the removal rule.

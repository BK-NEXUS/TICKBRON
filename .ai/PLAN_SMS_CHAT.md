# PLAN: SMS when support answers a user (and the base for other SMS later)

Status: DRAFT 2026-11-08. No code changed. It touches money (SMS cost), personal data (phone numbers) and a migration, so the owner must approve it before any code is written.

## What the owner asked
When the platform's staff answers a user in the support chat, the user also gets an SMS on the phone, like a marketplace order notice. It should work for the website and for the Android (and later iOS) app: the SMS is sent by the server, so no app change is needed.

## What exists today (facts)
- The chat is a support chat: one `Conversation` per user with the team (`chat/models.py`: `Conversation.user` is one-to-one, `Message.from_staff`). Hotel owners are not part of it. "A hotel answers a guest" does not exist as a feature; it would be a new chat feature and is NOT part of this plan.
- A staff reply already sends an e-mail notice that carries a link and never the text (`chat/notify.py: notice_for`, queued by `chat/tasks.py: send_chat_notice`). One notice per run of unread messages (`_first_unread`).
- `User.phone_number` exists, is required at sign-up, stored in E.164 form (`users/serializers.py: validate_phone_number_format`), is NOT verified and several accounts may share a number ("Stored only (no SMS, no code)").
- No SMS provider, no SMS setting and no SMS code exist. `accounts.Notification.sent_via_sms` is an unused flag.
- Errors, throttles and Celery queue patterns to reuse: `common/alerts.py`, `common/tasks.py: send_telegram_message`, `chat/throttles.py`.

## Design
1. One small module `common/sms.py` with `send_sms(phone, text)` and two backends chosen by setting `SMS_BACKEND`: `console` (logs a masked number, used in development and tests) and `eskiz` (or the provider the owner picks). Nothing else in the code knows the provider.
2. `chat/notify.py` gets one more step in `send_notice`: after the e-mail logic, for a staff reply (`message.from_staff`), the same `_first_unread` rule, an active user, a phone number and the user's opt-in (below), queue `send_sms_task`. A failing SMS must never stop the e-mail (same pattern as Telegram).
3. The text is fixed, short and carries no message content, only a link, like the e-mail: `TICKBRON: sizga yangi xabar bor. tickbron.com/support` (Latin letters only so it stays one SMS part). Decision for the owner: Uzbek only, or by language (no language field exists on the user; a new field would need a migration).
4. Opt-in: a new boolean `sms_notifications` on the user (default off, a checkbox in the profile and at sign-up), so nobody receives an SMS to a number they did not choose. Migration: one new column, reversible.
5. Limits (all settings, all enforced on the server):
   - `SMS_ENABLED` master switch (default False; production turns it on only when the provider works).
   - Per user: at most `SMS_PER_USER_PER_DAY` (default 3) and one per 10 minutes.
   - Whole site: `SMS_DAILY_LIMIT` (default 300). When it is reached, no more SMS that day and one Telegram alert to the team. This caps the money that can be spent whatever happens.
6. Only Uzbek, Kazakh and similar real numbers the provider accepts; the number must pass `parse_phone_number`. The number is never written to logs in full (last 2 digits only) and never in an error message.
7. A small table `SmsDelivery` (user, kind, status, provider message id, created_at) for the daily counters, support questions ("was it sent?") and audit. New migration, reversible. No message text and no number are stored there.
8. Provider failures: Celery retry with back-off (3 tries), then status `failed`; never an error for the person who wrote the reply.
9. Android and iOS: nothing to change. (Alternative with no per-message cost: web push in the app. It needs a service worker push handler, VAPID keys and permission prompts; a separate plan if the owner wants it.)

## Security and privacy
- Anyone can type any number at sign-up, so SMS goes only after the user turns the opt-in on; the opt-in screen shows the number. Number verification by a code (cost per user) is a later step the owner can choose; the daily limits make abuse cost bounded until then.
- No SMS to staff or to users who are not active; no text of the chat in an SMS.
- The provider token lives only in the server `.env` (`SMS_*` variables), never in git, never in the frontend. The app refuses to start in production with `SMS_BACKEND=eskiz` and a missing token.
- Delivery receipts from the provider are not used in the first version (no public webhook to protect).

## Money
Each SMS costs the provider's tariff (the owner must ask the provider; do not assume a price). The cost is bounded by `SMS_DAILY_LIMIT` times the tariff per day.

## Tests (written first)
- `send_sms`: console backend masks the number; eskiz backend builds the right request and handles an error answer, a timeout and an expired token (mocked HTTP, no real calls).
- Staff reply with opt-in, phone, SMS enabled: one SMS queued; second reply while the first is unread: none; user reply: none; no opt-in: none; no phone: none; inactive user: none; `SMS_ENABLED` false: none.
- Limits: per-user daily cap, ten-minute gap, site daily cap with one alert.
- SMS failure does not stop the e-mail and does not fail the reply request.
- The opt-in field: profile read/write, sign-up default, permissions (a user changes only their own).
- Migration reversible (existing migration test pattern).
- Frontend: the checkbox in the profile and at sign-up, uz/ru/en keys, 390 px and 1440 px, error states.

## Contract and docs
`.ai/API_CONTRACT.md`: the new profile field `sms_notifications`. `.ai/HANDOFF.md`: a short note. `deploy/docker.env.example` and `deploy/env.production.example`: the `SMS_*` variables with comments. `.ai/DEPLOY_DOCKER.md`: one step to test an SMS.

## The provider (the owner must do this, no code can)
Uzbek providers such as Eskiz.uz and Play Mobile offer an HTTP API with a token. The owner opens the account (a person or a company, the provider says which documents), asks for the API login and the approved sender name, and the tariff. Sender-name rules differ by mobile operator (registration is required on at least one operator in Uzbekistan from August 2026 according to the SMS providers' own notes); the provider tells what applies. I do not open accounts or enter credentials.

## Open questions for the owner
1. Provider: Eskiz.uz, Play Mobile or another? (Needed before the real backend is written; the console backend and tests can be built first.)
2. Opt-in by checkbox (recommended) or SMS to every user with a phone number?
3. Text language: Uzbek only, or Uzbek and Russian by a new language field?
4. Daily site limit and per-user limit (defaults above).
5. Other SMS later (booking confirmed, booking cancelled)? Not in this plan; the same module would carry them.
6. A hotel answering a guest directly: a separate new chat feature, to be planned on its own if wanted.

## Not in this plan
Chat between hotel owners and guests, booking SMS, SMS codes for sign-in (the project deliberately has none), delivery receipts, web push.

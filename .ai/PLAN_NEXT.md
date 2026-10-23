# Next steps after the cash-only launch work (plan, 2026-10-22)

State: everything from PLAN_CASH_ONLY, owner photos, country/region pictures, the four-currency prices and the Dependabot upgrades is merged (Django 5.2, React 19, Vite 8). This plan lists what is left, in the order I recommend. Nothing here is started. Each step: tests first, full backend and frontend suites, browser check at 1440 and 390 px, its own PR (rules in CLAUDE.md).

## Step 0: confirm master is green (15 minutes)
- The master CI runs for #75, #76 and #77 were still running when this was written. Read them first; fix anything red before new work.
- Evidence of the earlier red runs: the `pip-audit` step (fixed in #74), not tests.

## Step 1: full browser pass on the merged master (about half a day, no new features)
Why: the Playwright E2E flows and the screenshots were last run before the cash flow, pictures, four currencies, React 19 and Vite 8 were merged together. Unit tests pass, but nothing has driven the real stack since.
- Start the dev stack (Postgres, backend with `seed_demo`, Vite), run `npm run test:e2e` (28 flows) with the demo guest's bookings cancelled first (the 5-upcoming cap).
- Screenshots at 1440 and 390 px of: home "Where to?", search with prices in the chosen currency, booking form with arrival time, confirmed page, My bookings (arrival notice, free cancel), owner arrivals and "Guest arrived", owner photo manager, admin Geography pictures, admin create-owner (phone and place), Status revenue.
- Output: a list of real defects (if any) under "Found" in HANDOFF; fix the small ones in the same PR, put the rest in this plan.
- Exit: all 28 E2E flows pass, no horizontal scroll at 390 px on the screens above.

## Step 2: owners can name and edit their hotel (about 1 to 1.5 days) - needs one decision
Why: today an owner cannot give a hotel a name (the cards show the address instead) and cannot edit a hotel after creating it (HANDOFF "Found, not fixed"; `PartnerPropertyWizard` has no name field, the partner serializer only reads `display_name()`). A hotel without a name is the first thing a guest sees.
- Backend: `PATCH /partner/properties/{id}/` accepts the hotel name in uz/ru/en (stored as `PropertyTranslation`), description, address and the basic fields; the account's assigned place stays locked (already enforced); same permission rules (own hotels only, 404 otherwise), same input rules (letters/digits rules from #66).
- Frontend: a name field (three languages) in the wizard, and an "Edit hotel" screen in the partner dashboard.
- Tests: another owner's hotel is 404, a guest is 403, a name with HTML is refused, a changed place is refused, translations saved and shown on cards.
- Decision needed: which fields may an owner edit after the hotel is active (name and description only, or also address and room counts)? Does an edit of an active hotel need staff approval again? Default if you do not decide: name, description and address editable at once, no re-approval.

## Step 3: small decisions already open (about half a day together)
- Owner arrivals list shows only the last 4 digits of the guest phone. A hotel taking cash needs the full number to call a late guest. If you agree: show the full phone only for today's and tomorrow's arrivals of that hotel, log nothing extra. Decision: yes / no / other rule.
- Cap of 5 upcoming bookings per guest (`MAX_UPCOMING_BOOKINGS_PER_GUEST`): keep 5, change the number, or remove. One setting, plus a test.
- Commission model with cash payment: no code until you decide (see LAUNCH_DAY section 1).

## Step 4: guest "My bookings" pagination and the Geography table on phones (about 1 day)
- `GET /bookings/` returns a plain array today; add the page structure the other lists use and a "Load more" in `BookingsPage` (contract change in API_CONTRACT).
- Admin Geography table: stop sideways scrolling at 390 px (stack the row as a card) and load the country list once for all moderation cards (15 cards = 15 requests today).

## Step 5: technical debt that does not block launch (pick as time allows, each is its own small PR)
- ~~`Booking.from_db()` must accept the `fetch_mode` argument~~ done (2026-10-23): it takes `**kwargs` and passes them on; no more warning on Django 6.1.
- Rename or drop the payment tables and `PaymentAuditLog` (needs a backup and a reversible migration; do it only after the owner is sure there is no online payment coming back).
- `charge_*` booking fields are really "the price in so'm"; rename in a migration, together with the previous item.
- Repo-wide `black`, `isort`, `flake8` pass (a pure formatting PR; they are not run in CI today).
- ~~Remaining flake8 `F` findings in tests and `scripts/checkpoint_checks/`~~ done (2026-10-23): `flake8 --select=F` is clean, `backend/.flake8` added.

## Not in this plan (outside the code)
Hosting, domain, TLS, SMTP, Telegram, logos, lawyer review of the arrival rule, native uz/ru review: see `LAUNCH_DAY.md`.

## How I will work when you say "start"
1. Step 0 immediately (read-only).
2. Step 1 next, report the findings in 10 lines, then wait for your decisions on Steps 2 and 3.
3. Steps 2 to 4 one PR each, each with the full suites run before the push; I will tell you when a PR is ready to merge and I will not merge anything myself.

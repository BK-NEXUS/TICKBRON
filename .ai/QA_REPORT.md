# QA REPORT (full project pass, started 2026-10-10)

Method: static gates, the existing suites, scripted black-box tests of the running stack (Playwright, Chromium, seeded dev DB), API probes. Every defect: failing test first, fix, targeted tests. Evidence is command output or file:line.

## Gates (Q0)
| Gate | Result |
|---|---|
| `tsc --noEmit` | clean |
| `eslint src` | 0 errors, 3 warnings (react-refresh); the old "160 problems" baseline in the notes is stale |
| `npm audit --omit=dev` | 0 vulnerabilities |
| `bandit -ll` | 2 high: MD5 in `payments/adapters.py:445` (the Click protocol mandates an MD5 signature, not fixable on our side); a deliberate bidi character in `promotions/tests/test_security.py:24` (security test) |
| `flake8` (E9,F63,F7,F82,F811,F841,F401) | 408 findings, almost all unused imports/variables; one real: F821 undefined name in an unused helper (see QA-1) |

## Defects
| ID | Severity | Where | What | Status |
|---|---|---|---|---|
| QA-1 | low | `common/query_optimization.py` `bulk_update_with_optimization` | Unused helper that raises `NameError` (`obj` undefined in the dict comprehension) if anyone calls it | fixed: removed (no callers, no tests) |
| QA-2 | medium | booking create/cancel, favorites, reviews, partner rooms/rates/inventory serializers | Free-text fields had no length limit: a 200,000-character `special_requests` and a 200,000-character favorite note were accepted (201) and stored; `guest_full_name` longer than its 300-character column would hit the database | fixed: limits (special requests 1000, guest name 300, cancellation reason 1000, favorite note 500, review comment 2000, room/rate description 2000, cancellation policy 2000, inventory note 500); tests `bookings/tests/test_qa_input_limits.py`, `common/tests/test_text_limits.py` |
| QA-3 | medium | admin Statistics, Customers, dashboard title (CSS) | Page scrolled sideways: Statistics 12-45 px at 390 px (12-month chart, wider in ru/uz), dashboard title 32 px in Russian ("администратора" does not wrap), Customers table 48 px wider than a 1440 px screen in Russian | fixed (`styles/index.css`); regression tests `frontend/e2e/mobile-layout.e2e.ts` (5) |
| QA-4 | medium | `BookingPage.tsx` price summary | The page computed a "Deposit (N%)" amount in the browser (`total * percent / 100`), breaking the rule that money is computed on the backend only; the backend never charges a deposit, so the line also misled | fixed: line and unused i18n key `booking.deposit` removed; test in `BookingPage.test.tsx` |
| QA-5 | medium | `Header.tsx`, dashboard views, `EmptyState` | Accessibility: the header brand was an `h1`, so every page had 2-3 `h1` (admin and partner dashboards 3); the "sign in required" screens of Profile and Bookings had none. Screen-reader users get no single page title | fixed: brand is a `span`; dashboard view titles are `h2`; `EmptyState` takes `headingLevel` and the full-screen ones use 1; tests `Header.test.tsx`, `EmptyState.test.tsx`, `frontend/e2e/headings.e2e.ts` (3 flows over public pages, owner tabs, admin views) |
| QA-6 | high | `RoomSelection`, `AvailabilityCalendar`, `DateRangeCalendar`, `SearchForm`, `PartnerRoomCalendar` | The frontend took "today" from the browser's time zone while the backend judges dates in Asia/Tashkent (UTC+5). Between 19:00 and 24:00 UTC (00:00-05:00 in Tashkent) a guest west of Tashkent was offered a day already past there: `GET /properties/{id}/availability/` answered 400 "check_in cannot be in the past" and the calendar stayed empty (found when flows B and E failed at 19:05 UTC) | fixed: `businessToday()` in `utils/dates.ts` (Intl, Asia/Tashkent) used for every booking date minimum; tests `utils/dates.test.ts`; `RoomSelection.test.tsx` helper `localDate` now counts from the business date (assertions unchanged) |
| QA-7 | medium | `payments/views.py` (my own N-5 change) | The "one active payment per booking" rule refused a retry after a failed confirmation with 409, so the guest's "Retry payment" could not work (flow B failed) | fixed: a retry or double click with the SAME provider resumes the one active transaction (200, no second charge); another provider or an already completed payment still gets 409; a completed payment always wins; tests `TestOneActivePaymentPerBooking` (8) |
| QA-8 | medium | `properties/search.py` `_apply_text_search` | A multi-word query matched properties containing ANY word ("Pricey Street" matched every property on any "Street") | fixed: every word must match (words may match different fields); tests `properties/tests/test_qa_text_search.py` |
| QA-9 | low | `Footer`, `i18n/messages/*` | Copyright year hardcoded "2024" | fixed: `{year}` filled with the current year; `Footer.test.tsx` asserted the literal "2024 TICKBRON" and now asserts the current year |
| QA-10 | low | `frontend/e2e/status.e2e.ts` | The Status e2e flow was stale and failed on four assertions that no longer match the product: revenue chart currency (`USD`; since R6 `seed_demo_stats` prices Uzbekistan hotels in UZS), summary card "Bookings" (R12a renamed it to "Counted"/"Stayed bookings"), `totals.bookings` (now `totals.counted`/`totals.stayed`), and an ambiguous "Users" button (dashboard nav and status tile) | fixed in the test only (no product change): the assertions now name the current labels and fields and the same API-vs-screen number check; changed lines listed in HANDOFF |
| QA-11 | low | `bookings/tests/test_booking_logic.py::test_check_in_today_is_allowed` | The test took "today" from `timezone.localdate()` (UTC) but the booking rule judges check-in against the business date (Tashkent), so the test failed every day between 19:00 and 24:00 UTC (seen in the final full run at ~20:00 UTC); the product was right | fixed in the test: `business_today()`; same assertion |

## Black-box probes (all green after the fixes above)
- API probes against the running stack, 65 checks: guest/owner IDOR on bookings, payments, favorites, reviews, partner properties/rooms/bookings/no-show (all 403/404), admin endpoints refused for anonymous/guest/owner, 22 hostile booking bodies and 6 malformed JSON bodies (no 5xx), every GET endpoint of the OpenAPI schema for 4 roles with ids 1/huge/abc (612 requests, no 5xx), POST without CSRF refused.
- Race: three guests book the last room at once, exactly one 201, inventory 1/1 (consistent).
- Money: quote total == booking total, UZS charge is whole so'm, paying the exact charge accepted, 1 less refused, wrong currency refused (31 checks on 6 stays).
- Accessibility crawl (4 roles, en, desktop): unnamed buttons/links, unlabelled fields, images without alt, duplicate ids, missing `lang`: none found; only the heading problem (QA-5).
- Existing e2e flows (user-flows A-H, calendar, promotions, navigation, status): after cleaning data my probes had left behind and fixing QA-6/QA-7 they pass; the earlier failures of A/C/F were data pollution (7 pending bookings, a favorite) and B/E were QA-7 and QA-6.
- UI crawl: 4 roles x uz/ru/en x light x desktop/mobile plus dark (en/uz): console errors, failed requests, raw i18n keys, undefined/NaN text, broken images, overflow. Only QA-3 found.

## Final gates (2026-10-10, finished code)
Backend full suite 2919 tests (1 time-of-day test fixed afterwards, its file 20/20); frontend 1741 tests, `tsc` clean, `eslint` 0 errors (3 react-refresh warnings), `vite build` ok; e2e: user-flows A-H, calendar, promotions, navigation, status, mobile-layout (5), headings (3) all pass.

## Found, not fixed
- Tests that take "today" from the machine clock (`date.today()`, `timezone.localdate()`) can fail between 19:00 and 24:00 UTC; only the one above failed in a full run, others may exist.
- Payments: MD5 in the Click signature (`payments/adapters.py:445`) is mandated by the provider protocol.
- Dev stack: Celery is not running, so pending bookings are never expired in dev (the 15-minute expiry task exists).
- Demo data (dev only): the three `seed_demo` hotels were found `suspended` in the dev database (cause not traced; I set them back to `active` to test); the 12 `seed_demo_stats` hotels have no inventory rows, so they appear in search but cannot be booked ("not available").
- Unused imports/variables across the backend (flake8 F401/F841), cosmetic.

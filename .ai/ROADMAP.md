===== ROADMAP =====
Rules for every item: inspect first; proof test first; never weaken or skip tests; PostgreSQL; full suites with --create-db before merging to master; commit and push every 15–20 minutes (this computer is wiped at shutdown); one item may have several commits; prefixes "kolya - backend:" / "kolya - frontend:" / "kolya - docs:"; frontend uses brand colors (gold/ink/cream), one primary button per screen, no emoji icons; never log or commit secrets; stop only on a real merge conflict. Short reports.

R1 Test database fix + merge fix/geography-mapping into master.
R2 Geography: finish .ai/GEOGRAPHY_PLAN.md from the first step not DONE.
R3 Phase 3 steps 3.6–3.8 from .ai/PHASE3_PLAN.md (owner calendar, external booking blocks UI, bulk price edit, E2E).
R4 Security and reliability review: re-run the permission matrix including all new endpoints; admin audit log (who viewed which customer profile and when — audit #21); confirm OTP, lockout and rate limits are intact; refund with optional cancel_booking flag (fix plan item #6) if not done yet; python manage.py check --deploy with production-like settings; pip-audit and npm audit (fix high/critical); no PII or secrets in logs; document server-level headers (clickjacking/CSP) in .ai/RELEASE_CHECKLIST.md.
R5 Languages uz/ru/en: a real i18n system (react-i18next or equivalent), language selector working and remembered, all UI strings translated, geography names in the chosen language. E2E flow H must pass.
R6 Currency: UZS added; amounts formatted like "1 250 000 so'm"; daily exchange rate from the Central Bank of Uzbekistan (cbu.uz) via a scheduled task; exchange rate snapshot saved on each booking; UZS default for Uzbek users.
R7 Phone country selector with SVG flags, if not finished in R2.
R8 Card payment form in TEST MODE only: number (16 digits, Luhn), expiry, CVV, cardholder; card data never stored or sent to our backend; clearly marked so production uses Payme/Click tokenization instead.
R9 VIP rooms: category flag on room types, badge, separate price via rate plans, "VIP only" filter.
R10 Home page (Uzum + Booking.com style): top carousel of promoted and discounted hotels; hotel card grid; sidebar filters; Country > Region > City picker; promotions model managed by super-admin (paid placement, start/end dates, priority, "Reklama" label, impressions and clicks counted); discounts on rate plans for date ranges.
R11 Property page (Booking.com style): large gallery with full-screen lightbox, detailed room info, reviews with category scores, grouped amenities, policies, "free cancellation" badge where true, total price for the selected nights, map with Leaflet + OpenStreetMap (no API key).
R12 Status additions: comparison with the previous period (+/- %), cancellation rate, occupancy rate, average booking value and stay length, CSV/Excel export, owner panel "arriving today/tomorrow", owner's anonymous rank within the region.
R13 Design pass: replace emoji with an SVG icon set (e.g. lucide-react), shadow/elevation tokens, spacing and typography cleanup, mobile layouts, dark mode (follows system setting, toggle remembered, contrast checked); Playwright screenshots of every page at 1440px and 390px, review them and fix the top problems.
R14 Performance: index review, N+1 checks, Redis caching for search, filter options and geography, image thumbnails and compression; a load test (Locust or k6, about 200 concurrent users on search and booking) with p95 times reported.
R15 Final: full backend and frontend suites, full E2E + crawl, update .ai/RELEASE_CHECKLIST.md.

Waiting for owner decisions (do not implement): commission percentage, payment model (pay at hotel or through the platform), settlement report, Telegram notifications (needs a bot token), real Payme/Click/Visa and Eskiz credentials, legal texts reviewed by a lawyer, hosting and deployment, transparent and horizontal logo files from the client.
===== END OF ROADMAP =====

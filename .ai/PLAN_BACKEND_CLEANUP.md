# Plan: clearer backend code and a safe way to add features

Status: APPROVED by the owner (2026-10-14). Step 2.1 (`users/views.py` split) is done; the rest follows one step at a time.

## 1. Rules for every new feature (how we work)
1. Write the idea in `.ai/PLAN_<item>.md` first: what changes, which endpoints, which data, how it can be abused.
2. Failing test first, then the code, then the full suite.
3. Money, security and migrations wait for approval (existing gate in `.ai/README.md`).
4. One small commit per step; push after every commit; never to master.

## 2. Backend cleanup (small steps, behaviour must not change)
Each step is one commit and must keep the whole suite green without changing any assertion.
1. DONE: `users/views.py` (about 600 lines) split into `views/auth.py`, `views/otp.py`, `views/profile.py`, `views/password.py` and move the throttle classes into `users/throttles.py`. Views stay thin: they call `users/services.py`.
2. `users/serializers.py`: keep phone helpers in `users/validators.py`; one serializer per use; remove helpers that nothing calls any more (the registration change left `validate_unique_phone_number` used only by the profile).
3. Replace remaining long functions with small named ones (find them with `flake8 --max-complexity 10`).
4. Remove dead code, commented code and unused imports (`flake8`, `isort`, `black`), one app at a time: users, bookings, payments, properties, partner, admin_panel.
5. Docstrings say why, not what; remove noise comments.
Not in scope: renaming public endpoints, changing responses, models or migrations.

## 3. Security (checked in every step)
- Server-side validation for all input; permissions on every endpoint (the permission matrix test fails when a route is unclassified).
- Money, totals and availability are computed only on the backend.
- No personal data or secrets in logs; rate limits and CSRF stay as they are.
- Registration: e-mail, name and password only; e-mail verification link before first booking is the next candidate (needs approval: security).

## 4. Design (frontend)
- Look at 3-4 real booking sites (layout of sign-up, search, hotel page) and write the findings in this file before building.
- Icons: inline SVG only (lucide-react), never emoji or sticker images.
- Reuse the existing design tokens and components; each screen checked at 390px and 1440px; loading, empty and error states; keyboard and contrast.
- Plain, human copy (short sentences, no marketing filler), texts through i18n keys.

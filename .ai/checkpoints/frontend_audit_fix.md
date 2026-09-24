# CHECKPOINT: Frontend audit fixes (F1–F4)

Checkpoint: frontend audit fix (not numbered, so Baxram's frontend_NN sequence stays his)
Owner: Kolya, with Baxram's permission to change `frontend/` for this task
Commit: `668e91b` (backend, master), `6255c63`..`d043043` + this commit (branch `fix/frontend-audit`)
Status: READY for review. Merge into master is Baxram's call. The UI booking and review flows stay blocked by F20/F21 (report only, out of scope)

## Implemented
- Backend (master): `GET /api/v1/auth/csrf/` returns `{"csrf_token"}`; `/auth/me` returns read-only `is_staff`
- F1: `export default` on every lazy-loaded page and `AdminCustomerProfile`
- F3: `utils/errorHandler.readApiError` reads all four backend error shapes and gives per-status messages; every adapter uses it
- F2: `utils/api.apiFetch` sends `X-CSRFToken` on POST/PUT/PATCH/DELETE (token from `/auth/csrf/`, cached, cleared on login/OTP/register/logout, one retry on CSRF 403); every adapter uses it
- Item 4: `npm run build` = `tsc && vite build`; remaining tsc errors fixed
- F4: review create sends `property`, `booking` and flat `*_rating` fields

## Tests
- Backend: `users/tests/test_csrf.py` (7); full suite on PostgreSQL 855 passed, 2 skipped
- Frontend: new `App.test.tsx`, `utils/api.test.ts`, `build.test.ts`; extended `errorHandler`, adapter and `ReviewForm` tests. 863 passed, 19 failed. The 19 failed before these changes too (same 4 files: `AdminCustomerProfile`, `AdminCustomersList`, `AdminStatisticsDashboard`, `SupportLookupPage`, rendered without a Router)
- `tsc` 0 errors, `npm run build` passes, lint 276 (was 277)
- E2E on a separate PostgreSQL db `tickbron_e2e` with the real backend and Chrome: see `.ai/frontend-audit-report.md` "2-bosqich"

## Security
- CSRF stays enforced; the token endpoint is public, just like Django's own cookie. The cookie stays HttpOnly
- The CSRF retry happens only on "CSRF Failed" 403s (Django rejects those before the view runs)
- `is_staff` is read-only and cannot be set through `/auth/me/update/` (tested)
- Server text for 5xx responses is not shown to users

## API/contract changes
- New: `GET /api/v1/auth/csrf/`; `/auth/me` gets `is_staff`. Documented in `contracts/auth.md` and `API_CONTRACT.md`
- No other contract changes. F4 follows the existing serializer

## Files changed
- backend/users/{views,urls,serializers}.py, backend/users/tests/test_csrf.py
- frontend/src/adapters/*Adapter.ts (+tests), src/utils/{api,errorHandler}.ts (+tests), src/pages/*.tsx and components/AdminCustomerProfile.tsx (default exports), components/ReviewForm.tsx (+test), App.test.tsx, build.test.ts, test/setup.ts, package.json, tsconfig.json

## Known issues
- F20–F32 in `.ai/frontend-audit-report.md` (API mismatches, report only). F20 and F21 block the booking and review flows in the UI
- Contract text in HANDOFF (`category_ratings` for reviews) still disagrees with the serializer

## Next checkpoint
- F20–F23, then F24–F25

## Handoff
- See the note for Baxram at the end of `.ai/HANDOFF.md`

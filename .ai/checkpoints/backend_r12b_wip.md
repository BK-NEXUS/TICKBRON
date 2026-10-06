# CHECKPOINT (WIP): R12 phase 3 / R12b (no-show reports + refund)

Branch: feat/r12b-noshow (from feat/r12-status 7644857). NOT merged. Full suite NOT run on this branch yet.

## Done (code + tests written, new tests pass)
- Source: bookings/noshow.py (service), noshow_serializers.py, views_noshow.py, NoShowReport model + Booking.no_show_refund_percent (migration bookings/0010, admin_panel/0008), settings (NO_SHOW_REFUND_PERCENT, NO_SHOW_FLAG_*, throttle 20/hour), parse_percent, state machine reverse transitions, completion skips pending reports, metrics no_show_reported, quote/booking disclosure fields, notification code no_show_marked_no_refund, URLs (partner + admin-panel).
- Tests: bookings/tests/test_r12b_{noshow,refund,metrics,access_and_queries,migration}.py + r12b_helpers.py; matrix entries added to admin_panel and partner test_access_matrix.py. Last run of the first four files: all passed (254); migration test passed.

## Remaining
1. Run the full suite: `cd backend; venv\Scripts\python.exe -m pytest --create-db -q -n 8` (about 13 min). Fix failures without weakening assertions (likely: tests that list notification codes, serializer field sets, Booking snapshot field lists, drf-spectacular operationId collisions / `manage.py check --deploy`).
2. TDD proof is already in git (tests commit before source failed on import).
3. Docs: API_CONTRACT.md section "R12b" (endpoints, error codes not_reportable_status / too_early / window_closed / report_exists / not_pending / not_decided / booking_not_reportable / inventory_unavailable, disclosure fields, refund rules, needs_manual in real mode); PLAN_R12.md status; HANDOFF.md "Frontend needs" (owner "Guest did not arrive" button + comment dialog on bookings list [arrivals only list today/tomorrow, reports start the day after check-in: maybe add day=yesterday], owner "My reports" + withdraw, staff "No-show reports" queue with approve/reject/reverse showing refund_preview, refund statement on payment step / confirmation / My bookings from no_show_refund_text_key + params, new status labels) and the line "READY FOR FRONTEND: R12b - <endpoints, fields>".
4. Checkpoint .ai/checkpoints/backend_r12b.md (counts, changed expectations if any), RELEASE_CHECKLIST (partial refunds unverified with Payme/Click/Visa -> needs_manual; lawyer review of the statement).
5. Extra tests worth adding: report throttle at 20/hour default, concurrent double approve (threads, like test_concurrency), admin/partner OpenAPI schema generation still works.
6. Push after every commit; merge into master only with the suite green and permission (the owner merges).

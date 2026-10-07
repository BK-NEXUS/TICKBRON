# CLAUDE.md

TICKBRON is a Booking.com-style hotel booking platform for Uzbekistan / Central Asia.

- `backend/`: Django + DRF (PostgreSQL, Redis, Celery). Details, commands and architecture: [backend/CLAUDE.md](backend/CLAUDE.md).
- `frontend/`: React + TypeScript + Vite (`npm test`, `npm run lint`, `npm run build`).
- `.ai/`: coordination layer (state, contracts, checkpoints, handoff). Start with `.ai/README.md`; ownership and commit naming are defined there.

## Standing rules

- Git history and `.ai/` are the source of truth, not chat history.
- Always sync (`git fetch` + `git pull --rebase`) before starting work.
- Write a failing test first, then fix, then confirm it passes.
- Never weaken or delete test assertions to make tests pass.
- Run the full test suite before every commit: backend `pytest --create-db`, frontend `npm test`.
- If a git conflict appears, stop and report. Do not resolve it yourself.
- Never commit `.env` or any password.

STANDARD (applies to every task)

QUALITY - build it right the first time. This is a paid client project; there is no "polish later" phase. An item is done only when ALL of these are true:
1. It works end to end and is covered by tests written first (happy path, errors, permissions, edge cases).
2. Secure by default: the backend enforces permissions and validates all input; money, totals and availability are computed only on the backend; no secrets or personal data in code or logs.
3. UI items: loading, empty and error states; works at 390px and 1440px; keyboard and contrast OK; texts through i18n keys once i18n exists.
4. Documented: contract in .ai/API_CONTRACT.md and a short note in .ai/HANDOFF.md.
Do NOT add features, refactors or abstractions beyond the task. Another problem you notice: one line under "Found, not fixed" in HANDOFF.md, then move on.

CODE STYLE
- Small functions with one job; clear names; no dead code, no commented-out code, no debug prints.
- Follow the patterns already in the repo; reuse existing helpers, serializers, components and design tokens; never duplicate logic.
- Comments explain why, not what. TypeScript: real types, no any.
- Business rules live in one module or service; views and components stay thin.

TOKEN ECONOMY
- Use grep or a line range instead of reading whole files; do not re-read what you already know.
- While working run only the tests of the code you touch; run the full suite once, right before the final push.
- Print only the last 15 lines of long command output.
- Write each file completely in one pass; no repeated rewrites; no code explanations in chat.
- Report in 10 lines at most: what changed, test counts, commit hashes, open issues.

GIT AND SAFETY
- Push after every commit. Work on a feature branch; never push or merge to master (I merge Pull Requests myself).
- No force-push, reset --hard, clean or stash drop. Stop on a real merge conflict and show me.
- Never weaken, skip or delete a test. Migrations: new ones only, pg_dump before a dev DB, always reversible.
- Every claim needs evidence (file:line, command output, counts).

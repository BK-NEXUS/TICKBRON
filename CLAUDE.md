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

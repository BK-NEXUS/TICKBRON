# TICKBRON AI Agent Memory

This `.ai` directory is the persistent memory and coordination layer for AI coding agents.

## Source of truth
1. Actual Git repository state
2. `.ai/` state/contracts/checkpoints
3. `docs/` project documentation
4. The TICKBRON plan

Chat history is NOT required to resume work.

## Mandatory cycle
READ → SYNC → AUDIT → (PLAN + APPROVAL, gated items only) → SCOPE LOCK → IMPLEMENT → TEST → SECURITY CHECK → CONTRACT CHECK → CHECKPOINT → COMMIT → PUSH → NEXT ITEM

Next item rule (2026-10-03, approved by Kolya): After an item is merged and pushed, continue with the next BACKEND item in `.ai/ROADMAP.md` automatically. Approval gate: an item that touches money (prices, currencies, payments, refunds), security or database migrations starts with a plan in `.ai/PLAN_<item>.md` (e.g. `PLAN_R6.md`); push it, show the owner a short summary, and WAIT for the owner's explicit approval before changing code. Everything else continues without waiting.

## Ownership and workflow
- Backend owner: Kolya. Frontend owner: Baxram.
- Since 2026-09-25 (approved by Kolya and Baxram), Kolya's agent may work on both `backend/` and `frontend/` without asking first.
- GitHub is the shared synchronization point.
- Each agent must pull the latest remote changes before starting.
- Agents must inspect recent commits and `.ai` state before changing code.
- Never overwrite another person's work.
- If a merge/rebase conflict appears, STOP and report BLOCKED. Do not guess a conflict resolution.

## Commit identity
From 2026-09-25, commits by Kolya's agent use:
- Backend work: `kolya - backend: <short description>`
- Frontend work: `kolya - frontend: <short description>`
- Documentation / `.ai` only: `kolya - docs: <short description>`

Earlier commits keep their names: `baxram NN` (frontend checkpoints), `kolya NN project` (backend checkpoints) and `kolya - <summary>`. Do not rewrite them.

## Protected coordination files
Changes to shared contracts/state must be intentional and documented:
- `.ai/API_CONTRACT.md`
- `.ai/HANDOFF.md`
- `.ai/PROJECT_STATE.md`
- `.ai/BACKEND_STATE.md`
- `.ai/FRONTEND_STATE.md`

## Account switching
When changing AI accounts, the next agent must:
1. `git pull`
2. inspect recent Git history
3. read `.ai/README.md`
4. read the relevant state/progress/checkpoint files
5. verify the last checkpoint in the actual repository
6. run relevant tests
7. continue only from the exact next checkpoint

## Running the E2E tests (Playwright)
Run Playwright from `C:\Users\MicroStar\Desktop\TICKBRON\frontend` with a **capital D** in `Desktop`. From the lowercase path (`...\desktop\...`) Windows loads `@playwright/test` twice and every run ends with "Playwright Test did not expect test() to be called here" and "No tests found". Start the backend (`seed_demo`, `seed_demo_stats`, `runserver 8000` with `THROTTLE_ANON_RATE` / `THROTTLE_USER_RATE` set to `100000/hour`) and `npm run dev` first; see `frontend/playwright.config.ts`.

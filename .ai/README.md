# TICKBRON AI Agent Memory

This `.ai` directory is the persistent memory and coordination layer for AI coding agents.

## Source of truth
1. Actual Git repository state
2. `.ai/` state/contracts/checkpoints
3. `docs/` project documentation
4. The TICKBRON plan

Chat history is NOT required to resume work.

## Mandatory cycle
READ → SYNC → AUDIT → SCOPE LOCK → IMPLEMENT → TEST → SECURITY CHECK → CONTRACT CHECK → CHECKPOINT → COMMIT → PUSH → STOP

An agent must never silently continue into another checkpoint.

## Two-computer workflow
- Backend owner: Kolya
- Frontend owner: Baxram
- GitHub is the shared synchronization point.
- Each agent must pull the latest remote changes before starting.
- Agents must inspect recent commits and `.ai` state before changing code.
- Never overwrite another person's work.
- If a merge/rebase conflict appears, STOP and report BLOCKED. Do not guess a conflict resolution.

## Commit identity
Frontend commits MUST use:
`baxram 01`, `baxram 02`, ... `baxram 20`

Backend commits MUST use:
`kolya 01 project`, `kolya 02 project`, ... `kolya 20 project`

No alternative commit message is allowed for checkpoint commits.

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

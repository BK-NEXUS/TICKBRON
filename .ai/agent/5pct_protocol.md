# 5% AGENT PROTOCOL

Every prompt represents exactly one checkpoint.

1. READ
2. SYNC with GitHub
3. AUDIT actual repository and `.ai`
4. SCOPE LOCK to this checkpoint only
5. IMPLEMENT
6. TEST
7. SECURITY CHECK
8. CONTRACT CHECK
9. UPDATE `.ai` checkpoint/state/handoff
10. COMMIT using the owner's exact checkpoint name
11. PUSH to GitHub
12. REPORT READY or BLOCKED
13. STOP

If any hard-stop condition occurs, do not continue.

Hard stops:
- missing dependency/contract
- Git conflict
- unexplained regression
- critical/high security problem
- unsafe migration
- required external service unavailable
- another owner's protected work would need to be overwritten

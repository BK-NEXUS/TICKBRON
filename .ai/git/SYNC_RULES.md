# GIT SYNC RULES

## Before work
1. `git status`
2. `git fetch origin`
3. `git pull --rebase`
4. inspect `git log --oneline -20`
5. inspect `.ai/` state
6. run relevant tests

## Before commit
1. `git status`
2. `git diff`
3. tests
4. security check
5. contract check
6. update checkpoint/state/handoff
7. commit using the exact required message

## After commit
1. `git push`
2. verify push succeeded
3. confirm clean working tree
4. STOP

## Conflict rule
Any merge/rebase conflict = BLOCKED.
Do not auto-resolve by guessing.

# BACKEND ↔ FRONTEND HANDOFF

GitHub is the communication channel for implementation state.

## Backend → Frontend
When an API/contract becomes usable, record:
- endpoint
- request shape
- response shape
- auth requirements
- error format
- pagination/filter/sort behavior
- test status
- READY/BLOCKED status

## Frontend → Backend
When UI is ready but an API is missing, record:
- exact endpoint needed
- exact fields needed
- expected states/errors
- mock/stub status
- READY/BLOCKED status

## Hard rule
If a dependency is missing, the agent stops at the boundary. It does not invent an API or silently implement unrelated work.

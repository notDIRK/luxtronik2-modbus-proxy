---
status: partial
phase: 01-core-proxy
source: [01-VERIFICATION.md]
started: 2026-04-05T07:20:00Z
updated: 2026-04-05T07:20:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Modbus reads from real controller (SC1)
expected: Connect modpoll to proxy while polling real Luxtronik 2.0; data returns and port 8889 is not held open between cycles
result: [pending]

### 2. Write reaches real controller (SC2)
expected: Write HeatingMode=2, controller state changes; write value 99, exception code 3 returned, no controller change
result: [pending]

### 3. Docker build and container startup (SC3)
expected: docker build succeeds, container logs structured startup/shutdown events, SIGTERM via tini propagates cleanly
result: passed (verified automatically 2026-04-05)

### 4. HA BenPru coexistence (SC5)
expected: Proxy and HA BenPru integration share port 8889 at 30s poll interval without connection errors
result: [pending]

## Summary

total: 4
passed: 1
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps

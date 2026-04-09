---
status: partial
phase: 05-coordinator-config-flow
source: [05-VERIFICATION.md]
started: 2026-04-09
updated: 2026-04-09
---

## Current Test

[awaiting human testing]

## Tests

### 1. End-to-end config flow UI
expected: Navigate to Settings > Integrations, search "Luxtronik", enter reachable IP, confirm single-step creation with only the IP field shown
result: [pending]

### 2. Poll cycles in executor without event loop blocking
expected: Monitor HA logs for 2-3 cycles; confirm no "Detected blocking call" warnings from HA's loop blocker
result: [pending]

### 3. asyncio.Lock serializes concurrent read + write
expected: Trigger a write and a read simultaneously; confirm no connection errors from the controller
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps

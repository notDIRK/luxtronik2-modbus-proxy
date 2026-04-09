---
status: partial
phase: 07-control-entities-translations
source: [07-VERIFICATION.md]
started: 2026-04-09
updated: 2026-04-09
---

## Current Test

[awaiting human testing]

## Tests

### 1. German locale rendering
expected: HA renders "Heizmodus", "Warmwassermodus", "SG-Ready", temperature setpoint names in German when locale is set to German
result: [pending]

### 2. Rate limiting under timing
expected: Second write to same parameter within 60s is silently deferred with a log warning visible in HA logs
result: [pending]

### 3. SG-Ready atomic write observable
expected: Selecting an SG-Ready mode updates both HeatingMode and HotWaterMode entity states to match the selected mode combination
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps

---
status: partial
phase: 02-integration-ready-register-map
source: [02-VERIFICATION.md]
started: 2026-04-05T21:00:00Z
updated: 2026-04-05T21:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. evcc end-to-end read test
expected: Start proxy + evcc, confirm the `heatsources:` YAML snippet in `docs/en/evcc-integration.md` works against a real or simulated controller without raw register knowledge. evcc reads power/temperature/mode from the proxy.
result: [pending]

### 2. SG-ready mode map hardware validation
expected: Write modes 0-3 to register 5000 and observe the Luxtronik controller's HeatingMode and HotWaterMode parameters change to the expected values. Mode mapping matches `SG_READY_MODE_MAP` on actual hardware.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps

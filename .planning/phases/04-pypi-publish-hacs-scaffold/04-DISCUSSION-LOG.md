# Phase 4: PyPI Publish & HACS Scaffold - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-09
**Phase:** 04-PyPI Publish & HACS Scaffold
**Mode:** auto (all decisions auto-selected)
**Areas discussed:** PyPI publishing, HACS skeleton structure, manifest.json config, brand icon, CI validation

---

## PyPI Publishing

| Option | Description | Selected |
|--------|-------------|----------|
| GitHub Actions trusted publishing (OIDC) | Modern, no API tokens, triggers on tag | ✓ |
| Manual twine upload | Simple but requires local credentials | |
| GitHub Actions with API token | Works but token management overhead | |

**User's choice:** GitHub Actions trusted publishing (auto-selected recommended)
**Notes:** OIDC is the PyPI-recommended approach since 2023. No long-lived secrets.

| Option | Description | Selected |
|--------|-------------|----------|
| Version 1.1.0 | Matches v1.1 milestone | ✓ |
| Version 1.0.0 | First PyPI release | |

**User's choice:** 1.1.0 (auto-selected per milestone convention)

## HACS Skeleton Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Monorepo: custom_components/ at root | Single repo, single PR for both | ✓ |
| Separate repo for integration | Clean separation but coordination overhead | |

**User's choice:** Monorepo (pre-decided in STATE.md)

## manifest.json Configuration

| Option | Description | Selected |
|--------|-------------|----------|
| Requirements: luxtronik only | HA integration bypasses pymodbus | ✓ |
| Requirements: luxtronik + pymodbus | Would be needed if HA used Modbus | |

**User's choice:** luxtronik==0.3.14 only (auto-selected per architecture decision)

| Option | Description | Selected |
|--------|-------------|----------|
| iot_class: local_polling | Connects locally, polls periodically | ✓ |
| iot_class: local_push | Would need callback mechanism | |

**User's choice:** local_polling (auto-selected, matches coordinator pattern)

## Brand Icon

| Option | Description | Selected |
|--------|-------------|----------|
| Custom SVG heat pump icon | Unique, recognizable | ✓ |
| Generic HVAC icon | Quick but less distinctive | |
| Text-based placeholder | Minimal effort | |

**User's choice:** Custom heat pump icon (auto-selected recommended)

## CI Validation

| Option | Description | Selected |
|--------|-------------|----------|
| hacs/action@main + hassfest | Full validation pipeline | ✓ |
| hacs/action only | HACS checks but no manifest validation | |

**User's choice:** Full validation (auto-selected recommended)

## Claude's Discretion

- Exact icon design details
- PyPI metadata formatting
- Exact HA minimum version in hacs.json
- MANIFEST.in vs pyproject.toml package discovery

## Deferred Ideas

None.

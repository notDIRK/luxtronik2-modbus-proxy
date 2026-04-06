---
phase: 03-documentation-and-release
plan: 02
subsystem: docs
tags: [documentation, docker, systemd, quickstart, user-guide, modbus]

requires:
  - phase: 01-core-proxy
    provides: "luxtronik2-modbus-proxy CLI entrypoint, config.example.yaml, pyproject.toml"
  - phase: 02-register-database
    provides: "full register map, SG-ready virtual register, config fields (enable_writes, write_rate_limit)"

provides:
  - "docs/en/quickstart.md — developer quickstart: clone, install, configure, run, verify, test"
  - "docs/en/user-guide.md — end-user Docker installation guide with plain-language config reference"
  - "docs/en/systemd.md — Linux systemd deployment guide with service management commands"
  - "contrib/luxtronik2-modbus-proxy.service — systemd unit file template (non-root, restart policy)"

affects:
  - 03-03-german-docs
  - 03-04-release

tech-stack:
  added: []
  patterns:
    - "All docs use 192.168.x.x placeholder — no real IPs anywhere in repository"
    - "Docs directory structure: docs/en/ for English, docs/de/ for German (parallel)"
    - "systemd service uses dedicated non-root user luxtronik-proxy, EnvironmentFile pattern for overrides"

key-files:
  created:
    - docs/en/quickstart.md
    - docs/en/user-guide.md
    - docs/en/systemd.md
    - contrib/luxtronik2-modbus-proxy.service
  modified: []

key-decisions:
  - "127.0.0.1 (localhost) used in modpoll verification example — acceptable in public docs as it is a loopback constant, not an infrastructure IP"
  - "0.0.0.0 retained in bind_address config example — it is a standard wildcard, not a real IP; matches config.example.yaml"
  - "systemd service uses cap_net_bind_service for port 502 rather than running as root — documented in troubleshooting"
  - "StartLimitIntervalSec=60 + StartLimitBurst=3 included in service file to prevent restart loops (threat T-03-06)"

patterns-established:
  - "Documentation cross-links: quickstart -> user-guide, user-guide <-> systemd, both -> evcc-integration, ha-coexistence"
  - "Config field documentation pattern: field name, YAML snippet, plain-language explanation, when to change"

requirements-completed:
  - DOCS-02
  - DOCS-03
  - DEPLOY-02

duration: 15min
completed: 2026-04-06
---

# Phase 03 Plan 02: English Guides and systemd Service Summary

**Three EN documentation guides and a production-ready systemd unit file covering developer quickstart, Docker end-user install, and systemd deployment paths.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-04-06T09:55:00Z
- **Completed:** 2026-04-06T10:10:00Z
- **Tasks:** 3
- **Files created:** 4

## Accomplishments

- Developer quickstart guide: clone-to-running in 9 sequential steps with exact commands for install, configure, run, verify, test, and Docker alternative
- End-user guide: plain-language config reference for all 10 config fields, Docker install walkthrough, troubleshooting section, links to evcc and HA guides
- systemd guide: complete deployment path with dedicated system user, service file install, journalctl usage, environment variable overrides, and port 502 capability fix
- systemd service file template: follows Linux best practices — non-root user, restart-on-failure with loop protection, optional EnvironmentFile, journald output

## Task Commits

1. **Task 1: Developer quickstart guide (EN)** - `8c26b88` (feat)
2. **Task 2: End-user guide and systemd guide (EN)** - `675f105` (feat)
3. **Task 3: systemd service file template** - `ac5ba70` (feat)

## Files Created/Modified

- `docs/en/quickstart.md` — Developer quickstart: 9-section guide from clone to running, including modpoll verification and pytest
- `docs/en/user-guide.md` — End-user Docker install guide with per-field config documentation and troubleshooting
- `docs/en/systemd.md` — Linux systemd deployment: system user creation, service install, journalctl, env overrides, troubleshooting
- `contrib/luxtronik2-modbus-proxy.service` — systemd unit file with Type=simple, non-root user, Restart=on-failure, StartLimitBurst, EnvironmentFile

## Decisions Made

- Used `127.0.0.1` in the modpoll verification example in quickstart.md — this is a loopback constant acceptable in public docs (not an infrastructure IP)
- Included `0.0.0.0` in bind_address config examples — matches the existing `config.example.yaml` pattern; standard wildcard, not a real IP
- Documented `cap_net_bind_service` as the recommended approach for port 502 binding without root, rather than running the service as root
- Included `StartLimitIntervalSec=60` and `StartLimitBurst=3` in the service file to address threat T-03-06 (restart loops consuming system resources)

## Deviations from Plan

None - plan executed exactly as written.

## Threat Surface Scan

All three threat mitigations from the plan's `<threat_model>` are implemented:

| Threat ID | Mitigation | Status |
|-----------|------------|--------|
| T-03-04 | All examples use `192.168.x.x` placeholder | Verified — no real IPs in docs/en/ or contrib/ |
| T-03-05 | Service runs as `luxtronik-proxy` non-root user | Confirmed in service file (`User=luxtronik-proxy`) |
| T-03-06 | `StartLimitIntervalSec=60` + `StartLimitBurst=3` | Confirmed in service file |

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required by this plan.

## Next Phase Readiness

- English documentation complete for developer and end-user tracks
- systemd service file ready for users to copy
- Plan 03-03 (German translations) can begin — all EN source files are final
- Plan 03-04 (release) can reference these docs in README and GitHub releases

---
*Phase: 03-documentation-and-release*
*Completed: 2026-04-06*

## Self-Check: PASSED

- FOUND: docs/en/quickstart.md
- FOUND: docs/en/user-guide.md
- FOUND: docs/en/systemd.md
- FOUND: contrib/luxtronik2-modbus-proxy.service
- FOUND commit: 8c26b88 (Task 1 — quickstart.md)
- FOUND commit: 675f105 (Task 2 — user-guide.md + systemd.md)
- FOUND commit: ac5ba70 (Task 3 — service file)

# Roadmap: luxtronik2-modbus-proxy

## Overview

Three phases deliver the project in dependency order. Phase 1 builds the architecturally correct async proxy — all five critical pitfalls must be solved here before anything else is built on top. Phase 2 expands the register map to cover all evcc and HA essentials and adds the SG-ready virtual register, which depends on a validated write path from Phase 1. Phase 3 completes the user-facing surface: bilingual documentation, systemd service, and a GitHub Pages homepage — artifacts that require stable register addresses and a tested evcc configuration snippet.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Core Proxy** - Async protocol bridge with write safety, curated defaults, Docker, and logging
- [ ] **Phase 2: Integration-Ready Register Map** - Full parameter database, SG-ready virtual register, and evcc/HA integration docs
- [ ] **Phase 3: Documentation and Release** - Bilingual user and developer guides, systemd service, and GitHub Pages

## Phase Details

### Phase 1: Core Proxy
**Goal**: A working Modbus TCP proxy runs against real hardware, handles reads and writes safely, coexists with the HA BenPru integration, and ships in a Docker container — architecturally correct with no deferred pitfalls
**Depends on**: Nothing (first phase)
**Requirements**: PROTO-01, PROTO-02, PROTO-03, PROTO-04, PROTO-05, REG-01, WRITE-01, WRITE-02, WRITE-03, OBS-01, OBS-02, DEPLOY-01, DEPLOY-03
**Success Criteria** (what must be TRUE):
  1. A Modbus client (e.g., modpoll) can read temperature and operating mode registers from the proxy while it polls a real Luxtronik controller without holding the port 8889 socket open between cycles
  2. A Modbus write to the operating mode register reaches the Luxtronik controller and is rejected with Modbus exception code 3 if the value is out of the allowed range
  3. The proxy starts and stays running via `docker compose up` with only a config.example.yaml-derived config file — no hardcoded IPs or credentials anywhere in the repository
  4. Structured log output shows connection events, poll cycles, register reads, and write attempts with contextual fields (register address, parameter name, value)
  5. The HA BenPru/luxtronik HACS integration continues to function normally while the proxy polls at 30 s intervals on the same controller
**Plans:** 4 plans

Plans:
- [x] 01-01-PLAN.md — Project scaffold, config, logging, register definitions and map
- [x] 01-02-PLAN.md — Register cache with write validation, Luxtronik client wrapper
- [x] 01-03-PLAN.md — Modbus TCP server, polling engine, main entry point
- [x] 01-04-PLAN.md — Docker deployment, config.example.yaml, integration test

### Phase 2: Integration-Ready Register Map
**Goal**: The proxy covers all registers needed by evcc and Home Assistant, including the SG-ready virtual register, the full parameter database is accessible by name in YAML config, and a tested evcc YAML snippet is ready for documentation
**Depends on**: Phase 1
**Requirements**: REG-02, REG-03, REG-04, REG-05, INTEG-01, INTEG-02
**Success Criteria** (what must be TRUE):
  1. An evcc instance reads heat pump power, temperatures, and operating mode from the proxy using the documented YAML configuration snippet without any raw register number knowledge
  2. The SG-ready virtual register accepts integer 0–3 and the proxy translates each value to the correct Luxtronik parameter combination, confirmed by observing controller state change
  3. A user can add any of the 1,126 Luxtronik parameters to the register map by name in config.yaml without needing to look up raw parameter indices
  4. Calculation registers (251 entries) and visibility registers (355 entries) are accessible as read-only input registers in their dedicated address ranges
**Plans:** 3 plans

Plans:
- [x] 02-01-PLAN.md — Full parameter/calculation/visibility databases and RegisterMap extension
- [x] 02-02-PLAN.md — User-selectable parameters via config, fuzzy validation, list-params CLI
- [x] 02-03-PLAN.md — SG-ready virtual register, evcc integration docs, HA coexistence docs

### Phase 3: Documentation and Release
**Goal**: A non-technical user can install, configure, and validate the proxy from published documentation alone, in either English or German, without needing to read source code
**Depends on**: Phase 2
**Requirements**: DOCS-01, DOCS-02, DOCS-03, DOCS-04, DEPLOY-02
**Success Criteria** (what must be TRUE):
  1. A German-speaking user with no Python background can follow the end-user guide (DE) to install via Docker or systemd and have the proxy communicating with their Luxtronik controller within one session
  2. A developer can follow the quickstart guide (EN) to clone, build, and run the proxy against a test controller in under 15 minutes
  3. The GitHub Pages homepage clearly explains what the project does, who it is for, and links to both language tracks of the documentation
  4. README.md and README.de.md give an accurate project overview and architecture description that match the shipped v1 behavior
**Plans:** 4 plans

Plans:
- [x] 03-01-PLAN.md — MkDocs scaffold, i18n config, homepage content, GitHub Actions workflow
- [x] 03-02-PLAN.md — EN documentation: quickstart, user guide, systemd guide, service file
- [x] 03-03-PLAN.md — DE translations of all documentation files
- [x] 03-04-PLAN.md — README.md and README.de.md with badges, architecture diagram, links

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Proxy | 4/4 | Complete | - |
| 2. Integration-Ready Register Map | 0/3 | Planned | - |
| 3. Documentation and Release | 0/4 | Planned | - |

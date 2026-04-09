# Roadmap: luxtronik2-modbus-proxy

## Milestones

- ✅ **v1.0 MVP** — Phases 1-3 (shipped 2026-04-08) — [Archive](milestones/v1.0-ROADMAP.md)
- **v1.1 HACS Integration** — Phases 4-7 (active)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-3) — SHIPPED 2026-04-08</summary>

- [x] Phase 1: Core Proxy (4/4 plans) — Async protocol bridge with write safety, curated defaults, Docker, and logging
- [x] Phase 2: Integration-Ready Register Map (3/3 plans) — Full parameter database, SG-ready virtual register, and evcc/HA integration docs
- [x] Phase 3: Documentation and Release (4/4 plans) — Bilingual user and developer guides, systemd service, and GitHub Pages

</details>

**v1.1 HACS Integration**

- [ ] **Phase 4: PyPI Publish & HACS Scaffold** — Proxy package on PyPI, repo skeleton with hacs.json + manifest.json + brand icon + CI validation action
- [ ] **Phase 5: Coordinator & Config Flow** — DataUpdateCoordinator with connect-per-call, asyncio.Lock, config flow UI (IP entry, connection test, BenPru conflict warning)
- [ ] **Phase 6: Sensor Entities** — Read-only temperature, mode, power, and status sensors; entity registry exposes full 1,126-parameter database
- [ ] **Phase 7: Control Entities & Translations** — HeatingMode/HotWaterMode/SG-Ready select entities, temperature setpoint numbers, write rate limiting, EN+DE translations

## Phase Details

### Phase 4: PyPI Publish & HACS Scaffold
**Goal**: The proxy package is on PyPI and the repo has a valid, HACS-discoverable integration skeleton
**Depends on**: Nothing (first v1.1 phase; v1.0 proxy is the input)
**Requirements**: HACS-04, HACS-01, HACS-03
**Success Criteria** (what must be TRUE):
  1. `pip install luxtronik2-modbus-proxy==1.1.0` succeeds from PyPI
  2. HACS can add the repository as a custom integration without validation errors
  3. GitHub Actions validate.yml runs the HACS action on every push and reports pass/fail
  4. `hacs.json`, `manifest.json`, `const.py`, and brand icon exist and are schema-valid
**Plans:** 2 plans
Plans:
- [x] 04-01-PLAN.md — Version bump to 1.1.0, PyPI metadata, and trusted publishing workflow
- [x] 04-02-PLAN.md — HACS integration skeleton (hacs.json, manifest, const, icon) and CI validation workflow
**UI hint**: yes

### Phase 5: Coordinator & Config Flow
**Goal**: Users can add the integration in HA's UI by entering only an IP address, and HA polls the heat pump correctly without blocking the event loop
**Depends on**: Phase 4
**Requirements**: ARCH-01, ARCH-02, ARCH-03, SETUP-02, SETUP-03, SETUP-04
**Success Criteria** (what must be TRUE):
  1. User navigates to Settings > Integrations, searches "Luxtronik", enters IP, and the integration is created in one step
  2. Entering an unreachable IP shows an error message in the config flow UI instead of hanging
  3. Adding a duplicate IP (already configured for BenPru/luxtronik) shows a conflict warning in the config flow
  4. HA logs show coordinator poll cycles completing in executor threads (no event loop blocking)
  5. Two simultaneous write+read calls do not produce a connection error (asyncio.Lock serializes them)
**Plans:** 2 plans
Plans:
- [x] 05-01-PLAN.md — LuxtronikCoordinator with connect-per-call, executor dispatch, asyncio.Lock
- [x] 05-02-PLAN.md — Config flow (IP entry, connection test, BenPru conflict), __init__.py wiring, manifest update
**UI hint**: yes

### Phase 6: Sensor Entities
**Goal**: After entering the IP, users immediately see heat pump values as HA sensor entities — no further configuration required
**Depends on**: Phase 5
**Requirements**: SETUP-01, SENS-01, SENS-02, SENS-03, SENS-04
**Success Criteria** (what must be TRUE):
  1. Installing via HACS and entering the IP produces sensor entities for outside temp, flow temp, return temp, hot water temp, and source in/out temps with correct units
  2. Operating mode and compressor/pump running state appear as sensor entities with meaningful state strings
  3. Power consumption sensor appears when the calculation is available from the controller
  4. User can navigate to the entity registry and enable additional sensors from the full parameter database without code changes
**Plans:** 2 plans
Plans:
- [ ] 06-01-PLAN.md — sensor.py with core + bulk entity descriptions, entity class, platform registration
- [ ] 06-02-PLAN.md — Unit tests for sensor descriptions and value conversion
**UI hint**: yes

### Phase 7: Control Entities & Translations
**Goal**: Users can control heating mode, hot water mode, SG-ready state, and temperature setpoints from HA, with write protection guarding the controller NAND flash — and all UI text is available in EN and DE
**Depends on**: Phase 6
**Requirements**: CTRL-01, CTRL-02, CTRL-03, CTRL-04, HACS-02
**Success Criteria** (what must be TRUE):
  1. HeatingMode and HotWaterMode select entities offer all valid options and update the heat pump when the user picks one
  2. SG-Ready select entity accepts modes 0-3 and writes the correct parameter combination to the controller
  3. Temperature setpoint number entities accept values within validated ranges and reject out-of-range inputs
  4. Rapid repeated writes are rate-limited: the second write to the same register within the protection window is silently deferred, not sent to the controller
  5. Config flow form labels, error messages, and entity names display in German when HA is set to German locale
**Plans**: TBD
**UI hint**: yes

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Core Proxy | v1.0 | 4/4 | Complete | 2026-04-05 |
| 2. Integration-Ready Register Map | v1.0 | 3/3 | Complete | 2026-04-06 |
| 3. Documentation and Release | v1.0 | 4/4 | Complete | 2026-04-06 |
| 4. PyPI Publish & HACS Scaffold | v1.1 | 0/2 | Not started | - |
| 5. Coordinator & Config Flow | v1.1 | 0/2 | Not started | - |
| 6. Sensor Entities | v1.1 | 0/2 | Not started | - |
| 7. Control Entities & Translations | v1.1 | 0/? | Not started | - |

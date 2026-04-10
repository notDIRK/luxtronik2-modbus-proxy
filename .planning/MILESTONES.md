# Milestones

## v1.0 MVP (Shipped: 2026-04-08)

**Phases completed:** 3 phases, 11 plans, 15 tasks

**Key accomplishments:**

- Async Modbus TCP proxy translating Luxtronik binary protocol (port 8889) to standard Modbus TCP (port 502) with connect-per-call pattern for HA coexistence
- Write validation with enable_writes gate, writability checks, value range enforcement, and per-register rate limiting to protect controller NAND flash
- Full parameter database (1,126 parameters, 251 calculations, 355 visibilities) with user-selectable registers via YAML config
- SG-ready virtual register (address 5000) translating evcc modes 0-3 to Luxtronik HeatingMode + HotWaterMode combinations
- Docker multi-stage build (python:3.12-slim, tini, non-root) with integration tests and config.example.yaml
- Bilingual documentation (EN + DE): developer quickstart, end-user guide, systemd service, MkDocs site with GitHub Pages deployment

---

## v1.1 HACS Integration (Code-complete: 2026-04-09)

**Phases completed:** 4 phases, 9 plans (Phases 4-7)

**Key accomplishments:**

- PyPI package `luxtronik2-modbus-proxy==1.1.0` build + trusted-publishing workflow (Phase 4)
- HACS integration scaffold: `hacs.json`, `manifest.json`, `const.py`, brand icon, CI validation action (Phase 4)
- `LuxtronikCoordinator` (DataUpdateCoordinator) with connect-per-call pattern, `asyncio.Lock` enforcing the single-connection constraint, executor offload for the synchronous `luxtronik` library (Phase 5)
- Config flow (IP entry + connection test) and Options flow for reconfiguration (Phase 5)
- Sensor platform: 6 curated temperature/status sensors enabled by default, full 1,126-parameter database exposed as disabled registry entries (Phase 6)
- Control platform: `HeatingMode`, `HotWaterMode`, `SG-Ready` select entities + `HotWaterSetpoint`, `HeatingCurveOffset` number entities with write rate limiting (Phase 7)
- Full EN+DE translations for all entities, config flow, and options flow (Phase 7)
- Parameter backup button + backup viewer (quick task 260409-m53)

**Known open items:**

- 6 human UAT items in `06-VERIFICATION.md` require live-HA verification (temperature sensors, operating mode, compressor/pump, power, entity registry browsability)
- SG-Ready mode mapping still marked `[ASSUMED]` — needs hardware validation on Alpha Innotec MSW 14
- PyPI package not yet published (trusted-publishing setup pending)

**Design evolution:**

- Monorepo with `custom_components/luxtronik2_modbus_proxy/` alongside `src/` — single PR updates both
- HA integration bypasses the Modbus proxy entirely and talks directly to Luxtronik via `luxtronik==0.3.14`
- Python bifurcation: proxy stays on 3.12, integration runs on HA 2026.4.x's Python 3.14.2

---

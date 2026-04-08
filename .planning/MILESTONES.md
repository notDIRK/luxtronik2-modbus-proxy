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

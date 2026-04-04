# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-04)

**Core value:** Owners of Luxtronik 2.0 heat pumps can integrate them into evcc and modern energy management systems via standard Modbus TCP, without needing to understand the proprietary protocol or Modbus register numbers.
**Current focus:** Phase 1 — Core Proxy

## Current Position

Phase: 1 of 3 (Core Proxy)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-04-04 — Roadmap created, phases derived from requirements

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: —
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: —
- Trend: —

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: 3 coarse phases derived from 24 v1 requirements
- Architecture: All five critical pitfalls (asyncio starvation, socket corruption, single-connection, write validation, register addressing) must be resolved in Phase 1 before any feature work

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 2 (SG-ready): Exact Luxtronik parameter ID combinations for SG-ready modes 0–3 need hardware validation; community sources agree on concept but differ on Boost mode values
- Phase 2 (register convention): evcc Modbus YAML addressing (0-based vs. 1-based) must be confirmed against a running evcc instance before register addresses are locked

## Session Continuity

Last session: 2026-04-04
Stopped at: Roadmap written, STATE.md initialized, REQUIREMENTS.md traceability updated
Resume file: None

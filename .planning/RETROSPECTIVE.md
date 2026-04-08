# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-04-08
**Phases:** 3 | **Plans:** 11

### What Was Built
- Async Modbus TCP proxy translating Luxtronik binary protocol to standard Modbus TCP
- Write validation with range checks, writability enforcement, NAND flash rate limiting
- Full parameter database (1,126 parameters, 251 calculations, 355 visibilities)
- SG-ready virtual register for evcc integration (modes 0-3)
- Docker multi-stage build + systemd service
- Bilingual documentation (EN + DE) with MkDocs Material site

### What Worked
- Coarse 3-phase structure kept complexity manageable — 24 requirements across 11 plans
- Connect-per-call pattern for Luxtronik coexistence was architecturally correct from the start
- Full parameter database in Phase 2 was a natural extension of Phase 1's curated defaults
- Bilingual docs in Phase 3 benefited from stable register addresses locked in Phase 2

### What Was Inefficient
- Several SUMMARY.md files had empty one-liner fields — extraction tooling produced "One-liner:" placeholders
- REQUIREMENTS.md traceability table was never updated from "Pending" during execution
- STATE.md progress bar showed 0% despite all plans being complete (stale state)

### Patterns Established
- Register definitions as Python dataclasses with validation metadata
- ProxyHoldingDataBlock subclass pattern for write-through to Luxtronik
- Config via pydantic-settings with YAML + env var override for Docker

### Key Lessons
1. Summary one-liners should be enforced during plan completion — empty fields cause downstream issues in milestone archival
2. Traceability table updates should happen at phase transitions, not deferred to milestone
3. The single-connection constraint drove every architectural decision — identifying it early was critical

### Cost Observations
- Model mix: primarily sonnet (executor) + opus (planner)
- Timeline: 3 days from project init to full MVP
- Notable: coarse granularity kept plan count low (11 plans for 24 requirements)

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 3 | 11 | Initial project — established patterns |

### Cumulative Quality

| Milestone | Tests | Key Metric |
|-----------|-------|------------|
| v1.0 | 10+ unit + 4 integration | Write validation bypass caught by integration test |

### Top Lessons (Verified Across Milestones)

1. Identify the dominant constraint early — it simplifies every downstream decision
2. Coarse phases with clear dependency order reduce planning overhead

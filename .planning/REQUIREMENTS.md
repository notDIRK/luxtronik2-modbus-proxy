# Requirements: luxtronik2-modbus-proxy

**Defined:** 2026-04-08
**Core Value:** Owners of Luxtronik 2.0 heat pumps can integrate them into evcc and modern energy management systems via standard Modbus TCP, without needing to understand the proprietary protocol or Modbus register numbers.

## v1.1 Requirements

Requirements for HACS Custom Integration milestone. Each maps to roadmap phases.

### Setup & Installation

- [ ] **SETUP-01**: User can install the integration via HACS (custom repository)
- [ ] **SETUP-02**: User can add the integration via HA Config Flow by entering only the heat pump IP address
- [ ] **SETUP-03**: Config Flow tests the connection and shows an error if the controller is unreachable
- [ ] **SETUP-04**: Config Flow warns if a BenPru/luxtronik integration is already configured for the same IP

### Sensor Entities

- [ ] **SENS-01**: Integration creates sensor entities for core temperatures (outside, flow, return, hot water, source in/out)
- [ ] **SENS-02**: Integration creates sensor entities for operating mode and compressor/pump status
- [ ] **SENS-03**: Integration creates sensor entities for heat pump power consumption (if available via calculations)
- [ ] **SENS-04**: User can enable additional sensors from the full parameter database (1,126 parameters) via entity registry

### Control Entities

- [ ] **CTRL-01**: Integration provides select entities for HeatingMode and HotWaterMode
- [ ] **CTRL-02**: Integration provides an SG-Ready select entity (modes 0-3) translating to correct parameter combinations
- [ ] **CTRL-03**: Integration provides number entities for temperature setpoints (flow, hot water)
- [ ] **CTRL-04**: Write operations are rate-limited to protect controller NAND flash

### HACS Publication

- [ ] **HACS-01**: Repository has valid hacs.json, manifest.json, and brand icon
- [ ] **HACS-02**: Integration has translations for EN and DE (strings.json + translations/)
- [ ] **HACS-03**: GitHub Actions validate HACS compliance on every push
- [ ] **HACS-04**: Proxy package published to PyPI for manifest.json requirements

### Architecture

- [ ] **ARCH-01**: Integration uses DataUpdateCoordinator with connect-per-call pattern (no persistent socket)
- [ ] **ARCH-02**: All luxtronik library calls run via async_add_executor_job (non-blocking)
- [ ] **ARCH-03**: asyncio.Lock serializes all read/write operations (single-connection constraint)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Configuration

- **CONF-10**: Options Flow to reconfigure poll interval, enabled entities
- **CONF-11**: Diagnostics download for troubleshooting

### Integration

- **INTEG-10**: HACS default store submission (after community validation)
- **INTEG-11**: evcc upstream heater template PR

### Entities

- **ENT-10**: Climate entity for heating/cooling control
- **ENT-11**: Binary sensor entities for error states and alarms

## Out of Scope

| Feature | Reason |
|---------|--------|
| Options Flow (reconfigure poll interval) | v1.2 — keep v1.1 simple, default 30s is correct |
| Diagnostics download | v1.2 — nice to have, not MVP |
| HACS default store submission | Requires community validation first; start as custom repo |
| Climate entity | Complex UX for heat pumps — unclear value over select entities |
| Persistent Luxtronik connection | Breaks HA coexistence, violates single-connection constraint |
| Weather-forecast-based optimization | v2+ feature |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| HACS-04 | Phase 4 | Pending |
| HACS-01 | Phase 4 | Pending |
| HACS-03 | Phase 4 | Pending |
| ARCH-01 | Phase 5 | Pending |
| ARCH-02 | Phase 5 | Pending |
| ARCH-03 | Phase 5 | Pending |
| SETUP-02 | Phase 5 | Pending |
| SETUP-03 | Phase 5 | Pending |
| SETUP-04 | Phase 5 | Pending |
| SETUP-01 | Phase 6 | Pending |
| SENS-01 | Phase 6 | Pending |
| SENS-02 | Phase 6 | Pending |
| SENS-03 | Phase 6 | Pending |
| SENS-04 | Phase 6 | Pending |
| CTRL-01 | Phase 7 | Pending |
| CTRL-02 | Phase 7 | Pending |
| CTRL-03 | Phase 7 | Pending |
| CTRL-04 | Phase 7 | Pending |
| HACS-02 | Phase 7 | Pending |

**Coverage:**
- v1.1 requirements: 19 total
- Mapped to phases: 19 (100%)
- Unmapped: 0

---
*Requirements defined: 2026-04-08*
*Last updated: 2026-04-08 after roadmap creation for v1.1*

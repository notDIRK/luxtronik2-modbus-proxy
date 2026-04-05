# Phase 2: Integration-Ready Register Map - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-05
**Phase:** 02-integration-ready-register-map
**Areas discussed:** Parameter database design, SG-ready virtual register, Register address scheme, evcc/HA config snippets

---

## Parameter Database Design

### Storage approach
| Option | Description | Selected |
|--------|-------------|----------|
| Embedded Python dicts | Expand existing parameters.py/calculations.py pattern | ✓ |
| External YAML/JSON data file | Ship register_database.yaml alongside package | |
| Auto-generated from luxtronik library | Introspect library at startup | |

**User's choice:** Embedded Python dicts
**Notes:** Continues the pattern established in Phase 1

### Parameter selection method
| Option | Description | Selected |
|--------|-------------|----------|
| Named list in config.yaml | Users add parameter names under `registers:` section | ✓ |
| Preset groups + individual names | Named presets like `evcc_essentials` + individual overrides | |
| Expose all by default | Map all 1,126 parameters automatically | |

**User's choice:** Named list in config.yaml

### Metadata depth
| Option | Description | Selected |
|--------|-------------|----------|
| Full metadata | luxtronik_id, human name, data_type, writable, validation | ✓ |
| Minimal (name + index) | Just mapping from name to Luxtronik index | |
| You decide | Claude determines appropriate level | |

**User's choice:** Full metadata

### Data source
| Option | Description | Selected |
|--------|-------------|----------|
| Luxtronik library introspection | Extract from library internals | |
| BenPru HA integration as source | Parse BenPru const.py to bootstrap | |
| Manual curation from community docs | Build from forum posts and docs | |

**User's choice:** Both Luxtronik library and BenPru — Luxtronik as default, BenPru supplements
**Notes:** "bitte Luxtronik und BenPru verfuegbar machen via multi select auswahl fuer die ansicht von vorschlaegen. defaultmaessig Luxtronik"

### Curated defaults relationship
| Option | Description | Selected |
|--------|-------------|----------|
| Curated defaults always active | Phase 1 essentials always mapped, extras added via config | ✓ |
| Everything via config only | No hardcoded defaults | |
| Defaults as a preset group | Named preset + extras | |

**User's choice:** Curated defaults always active

### Visibilities support
| Option | Description | Selected |
|--------|-------------|----------|
| Yes, as a third register type | Add visibilities.py, map to dedicated address range | ✓ |
| Skip visibilities for now | Focus on parameters and calculations only | |
| You decide | Claude determines | |

**User's choice:** Yes, as a third register type

### Parameter discovery
| Option | Description | Selected |
|--------|-------------|----------|
| CLI command to list/search | `list-params [--search term]` command | ✓ |
| Commented YAML reference file | Ship register_reference.yaml | |
| Documentation only | Markdown table in docs | |

**User's choice:** CLI command to list/search

### Invalid parameter handling
| Option | Description | Selected |
|--------|-------------|----------|
| Fail fast at startup | Refuse to start, suggest "did you mean?" | ✓ |
| Warn and skip | Start but log warnings | |

**User's choice:** Fail fast at startup

---

## SG-Ready Virtual Register

### Mode mapping
| Option | Description | Selected |
|--------|-------------|----------|
| Hardcoded mapping with community consensus | Standard SG-ready modes hardcoded in Python | |
| Configurable mapping in YAML | Users define which params each mode sets | |

**User's choice:** Both — hardcoded community consensus as default, with configurable YAML override
**Notes:** "default with mapping with community consensus and in addition well documented Configurable mapping in YAML"

### Address placement
| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated virtual register range | Place at address 5000+ outside physical range | ✓ |
| Next available holding register | Place after last mapped parameter | |

**User's choice:** Dedicated virtual register range

### Read/write behavior
| Option | Description | Selected |
|--------|-------------|----------|
| Read-write | evcc writes mode, reads back current mode | ✓ |
| Write-only, separate status register | Separate registers for write and read | |

**User's choice:** Read-write

### Error handling
| Option | Description | Selected |
|--------|-------------|----------|
| Return Modbus exception + log | Exception code 4, keep last good mode | ✓ |
| Retry then fail | Retry 3 times before exception | |

**User's choice:** Return Modbus exception + log

### Transition validation
| Option | Description | Selected |
|--------|-------------|----------|
| Accept any mode 0-3 | No transition validation, evcc manages state | ✓ |
| Validate transitions | Only allow valid SG-ready transitions | |

**User's choice:** Accept any mode 0-3

---

## Register Address Scheme

### Address mapping strategy
| Option | Description | Selected |
|--------|-------------|----------|
| Keep identity mapping | Modbus address == Luxtronik index | |
| Compact contiguous mapping | Sequential addresses for mapped params only | |
| You decide | Claude determines | ✓ |

**User's choice:** You decide (Claude's discretion)

### evcc addressing base
| Option | Description | Selected |
|--------|-------------|----------|
| 0-based | evcc uses 0-based addresses | ✓ |
| 1-based | evcc uses 1-based addresses | |
| Not sure | Needs testing | |

**User's choice:** 0-based (user believes, flagged for hardware validation)

### Visibilities address range
| Option | Description | Selected |
|--------|-------------|----------|
| Separate input register block at offset | Visibilities at input registers 1000-1354 | ✓ |
| Discrete inputs (FC2) | Use FC2 for boolean visibilities | |

**User's choice:** Separate input register block at offset

---

## evcc/HA Config Snippets

### evcc documentation form
| Option | Description | Selected |
|--------|-------------|----------|
| Ready-to-paste YAML snippet | Complete evcc YAML block for copy-paste | ✓ |
| Full walkthrough with context | Step-by-step guide with explanations | |
| Both snippet + walkthrough | Quick-start + detailed explanation | |

**User's choice:** Ready-to-paste YAML snippet

### HA coexistence docs
| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated section in docs | "Running alongside HA" with practical advice | ✓ |
| FAQ format | Common questions with quick answers | |

**User's choice:** Dedicated section in docs

### evcc target config type
| Option | Description | Selected |
|--------|-------------|----------|
| Custom Modbus template (heater) | Proper evcc heater template YAML | ✓ |
| Generic Modbus meter config | Generic Modbus meter configuration | |

**User's choice:** Custom Modbus template (heater)

---

## Claude's Discretion

- Register address scheme: identity mapping vs reorganization (user said "you decide")
- Input register block sizing for calculations + visibilities
- SG-ready exact virtual register address within 5000+ range

## Deferred Ideas

None — discussion stayed within phase scope

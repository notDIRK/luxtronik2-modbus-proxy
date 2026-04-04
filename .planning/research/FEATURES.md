# Feature Research

**Domain:** Modbus TCP proxy for Luxtronik 2.0 heat pump controllers
**Researched:** 2026-04-04
**Confidence:** MEDIUM-HIGH (core proxy features HIGH; ecosystem integration features MEDIUM)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Modbus TCP server on port 502 | Modbus clients (evcc, HA) connect to standard port | LOW | pymodbus makes this straightforward |
| Read holding registers (FC03) | evcc and HA use FC03 for most register reads | LOW | pymodbus server handles this natively |
| Read input registers (FC04) | Some clients prefer input registers for read-only data | LOW | Map Luxtronik calculations to input registers |
| Write single register (FC06) | evcc writes operating modes via single-register writes | LOW | Required for SG-ready / mode switching |
| Write multiple registers (FC16) | Some clients batch-write multiple setpoints | MEDIUM | Needed for robust client compatibility |
| Temperature registers for key sensors | Users expect to read flow, return, hot water, outside temps | MEDIUM | Scaling from Luxtronik tenths-of-degree to 16-bit integer |
| Operating mode read + write | evcc must read current mode and write boost/normal/reduced | MEDIUM | Maps to ID_Ba_Hz_akt, ID_Ba_Bw_akt; values are enumerations |
| Hot water temperature setpoint read + write | HA and evcc control DHW target temp | MEDIUM | Maps to ID_Soll_BWS_akt; scale 0.1°C per unit |
| Power consumption register | evcc needs power in Watts for PV optimization decisions | MEDIUM | Luxtronik calculation parameter; map to 32-bit holding registers |
| Single-connection safety (connect-poll-disconnect) | Luxtronik 2.0 allows only one TCP connection | HIGH | Proxy must not hold connection open; HA BenPru integration coexists |
| Configurable polling interval | Different users tolerate different latency; HA and evcc each poll differently | LOW | Config file value, default 30–60 s; governs how often proxy refreshes its cache |
| YAML configuration file | All serious local-network tools use YAML config | LOW | Must include host, port, poll_interval, register mappings |
| Docker container | Standard deployment target for home automation add-ons | LOW | Dockerfile + docker-compose.yml required |
| Structured logging | Diagnose proxy behavior, register reads/writes, connection events | MEDIUM | JSON-structured or leveled text log; essential for debugging first deployments |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Curated default register set (evcc/HA essentials) | Users get working evcc integration without studying 1,126 Luxtronik parameter IDs | MEDIUM | Pre-mapped ~20 registers: temps, modes, power, hot water, SG-ready analog; zero-config starting point |
| Full parameter database (all 1,126 parameters browsable by name) | Power users can expose any Luxtronik parameter by name in config, not by raw parameter number | HIGH | Embed Bouni/python-luxtronik parameter definitions as lookup table; config references "ID_Soll_BWS_akt" not "parameter 10" |
| SG-ready operating mode abstraction | Lets evcc send SG-ready signals (boost / normal / reduced) via a single write to a virtual register | MEDIUM | Maps SG-ready int (0–3) to Luxtronik mode combinations: 0=Off, 1=Normal(Auto), 2=Boost(Party+DHW raise), 3=Reduced |
| Coexistence proof with BenPru/luxtronik HACS | Only proxy that explicitly documents and tests alongside HA BenPru integration | MEDIUM | Polling interval tuning + integration test; documented in user guide |
| evcc-ready YAML snippet in docs | Users paste the evcc config block and are done | LOW | Documentation effort, not code; high perceived value |
| Bilingual documentation (EN + DE) | German-speaking community is primary audience (haustechnikdialog.de, evcc forum) | MEDIUM | Two doc tracks: developer quickstart + end-user guide |
| Human-readable register names in logs | Logs show "ID_Ba_Hz_akt = Party" not "register 47 = 2" | LOW | Use parameter database for log enrichment |
| systemd service unit | Users not running Docker want systemd install | LOW | Service file + install script; important for Raspberry Pi users |
| Health endpoint / status command | Operators check proxy liveness without reading logs | MEDIUM | Simple HTTP /health or CLI --status; last poll time, connection state, error count |
| Hot water boost via single register write | evcc can force DHW boost (solar surplus to hot water) via one write | MEDIUM | Maps to ID_Ba_Bw_akt = "Party"; documented as primary use case |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Authentication / access control on Modbus port | Users worry about security | Modbus protocol has no auth layer; adding TLS wrapper breaks all standard Modbus clients; local network isolation is the correct model | Document that proxy is LAN-only; use firewall rules if needed |
| Persistent TCP connection to Luxtronik | Lower latency reads | Luxtronik 2.0 allows exactly one connection; holding it blocks HA BenPru integration and the Luxtronik app | Use connect-poll-disconnect pattern with configurable interval |
| Real-time sub-second polling | Users want live data | Luxtronik binary protocol takes ~200 ms per full read; sub-second polling starves other clients and causes controller instability | 30 s default; 10 s minimum documented limit |
| Expose all 1,126 parameters by default | "More is better" | Modbus address space collision; unmapped registers confuse clients; massive log noise | Curated default set + optional per-param config to add more |
| Firmware modification / upgrade path | Users want Luxtronik 2.1 features | Hardware limitation; no upgrade path exists for 2.0 controllers | Out of scope; proxy bridges the gap without firmware changes |
| Weather-forecast optimization | Advanced energy management | Requires external API, adds non-trivial complexity, belongs in evcc/HA automations not in the proxy | Proxy is a dumb protocol bridge; optimization lives in evcc |
| Alerting / push notifications | Operators want error alerts | Complexity disproportionate to v1 value; proxy should log errors, HA/evcc handle alerting | Use HA or evcc alerting on top of the proxy's metrics |
| Web UI for register browser | Nice for discovery | Adds a dependency (web framework), attack surface, and maintenance burden for a tool that is configured once and forgotten | Provide CLI --list-parameters command and documentation |
| Multi-device support (multiple Luxtronik controllers) | Rare multi-unit sites | Adds configuration and connection management complexity; edge case for v1 | Single-device focus; multiple proxy instances solve multi-device need |
| Modbus RTU / serial output | Some legacy devices need RTU | Target audience uses TCP-connected HA/evcc; RTU adds hardware dependency | TCP only; document RTU gateways as external solution |

---

## Feature Dependencies

```
[Modbus TCP Server (FC03/FC04/FC06/FC16)]
    └──requires──> [Luxtronik binary protocol client (polling loop)]
                       └──requires──> [Single-connection safety logic]
                                          └──requires──> [Configurable polling interval]

[Curated default register set]
    └──requires──> [Modbus TCP Server]
    └──requires──> [Parameter database (name -> parameter ID -> register address)]

[Full parameter database]
    └──enhances──> [Curated default register set]
    └──enables──>  [Human-readable log enrichment]
    └──enables──>  [User-configurable register additions via YAML]

[SG-ready abstraction register]
    └──requires──> [Operating mode write (FC06)]
    └──requires──> [Parameter database] (to know which parameter IDs to write)

[Hot water boost via single register write]
    └──requires──> [Operating mode write (FC06)]
    └──is-a──>     [SG-ready abstraction (mode 2 = boost)]

[Docker container]
    └──requires──> [YAML configuration file]
    └──enhances──> [systemd service unit] (alternative deployment, not both required)

[Health endpoint]
    └──requires──> [Polling loop state tracking]
    └──enhances──> [Docker container] (enables healthcheck: directive in compose)

[Coexistence with BenPru HACS]
    └──requires──> [Single-connection safety logic]
    └──requires──> [Configurable polling interval]

[evcc-ready YAML snippet]
    └──requires──> [Curated default register set] (register addresses must be stable)
    └──is-a──>     [Documentation artifact, not code]

[Bilingual documentation]
    └──enhances──> [evcc-ready YAML snippet]
    └──enhances──> [Coexistence documentation]
```

### Dependency Notes

- **Single-connection safety requires polling interval config:** The connect-poll-disconnect loop must be tunable; the safety constraint and the tuning knob are inseparable.
- **Curated default set requires parameter database:** Register numbers must be derived from known parameter IDs, not hardcoded magic numbers; the database is the mapping layer.
- **SG-ready abstraction requires operating mode write:** Writing a virtual SG-ready register triggers writes to one or more Luxtronik parameters; FC06 must already work.
- **Health endpoint enhances Docker:** Docker Compose `healthcheck:` can call the health endpoint; graceful SIGTERM handling is a precondition for clean container shutdown.
- **Full parameter database conflicts with "expose all by default":** The database enables selective exposure, not mass exposure; keep default register count small.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] Modbus TCP server (FC03, FC04, FC06, FC16) — without this, nothing works
- [ ] Luxtronik binary protocol polling client with connect-poll-disconnect — core protocol bridge
- [ ] Configurable polling interval (default 30 s) — required for coexistence with BenPru
- [ ] Curated default register set covering evcc essentials: flow temp, return temp, outside temp, hot water temp, operating mode, DHW setpoint, electrical power — zero-config starting point
- [ ] Operating mode write (heating circuit + DHW circuit) — evcc needs to switch modes
- [ ] SG-ready virtual register (maps 0–3 to Luxtronik mode combinations) — primary evcc integration point
- [ ] YAML configuration file (host, port, poll interval, optional extra registers) — no hardcoded values
- [ ] Docker container + docker-compose.yml — standard deployment
- [ ] Structured logging (connection events, register reads/writes, errors) — essential for first-deployment debugging
- [ ] EN + DE user guide (install, configure, evcc YAML snippet) — target audience is German-speaking

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] Full parameter database (all 1,126 parameters browsable by name in config) — add when users request parameters beyond the default set
- [ ] Human-readable register names in logs — add when debugging feedback shows raw IDs are confusing
- [ ] systemd service unit — add when users report Docker is unavailable on their hardware
- [ ] Health endpoint (/health HTTP or CLI --status) — add when Docker healthcheck or monitoring requests come in
- [ ] evcc upstream PR (template definition in evcc repo) — submit after proxy is stable and register map is validated

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Web UI register browser — defer; CLI and docs serve the same need with less complexity
- [ ] Alerting / push notifications — defer; HA and evcc handle this layer
- [ ] Weather-forecast optimization hooks — defer; out of scope for a protocol bridge
- [ ] Multi-device support — defer; edge case, multiple instances solve this

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Modbus TCP server (FC03/04/06/16) | HIGH | LOW | P1 |
| Connect-poll-disconnect safety logic | HIGH | MEDIUM | P1 |
| Configurable polling interval | HIGH | LOW | P1 |
| Curated default register set | HIGH | MEDIUM | P1 |
| Operating mode write (heating + DHW) | HIGH | MEDIUM | P1 |
| SG-ready virtual register abstraction | HIGH | MEDIUM | P1 |
| YAML configuration file | HIGH | LOW | P1 |
| Docker container | HIGH | LOW | P1 |
| Structured logging | HIGH | MEDIUM | P1 |
| EN + DE user documentation | HIGH | MEDIUM | P1 |
| Full parameter database (name lookup) | MEDIUM | HIGH | P2 |
| Human-readable register names in logs | MEDIUM | LOW | P2 |
| systemd service unit | MEDIUM | LOW | P2 |
| Health endpoint | MEDIUM | MEDIUM | P2 |
| evcc upstream PR | HIGH | MEDIUM | P2 |
| Web UI register browser | LOW | HIGH | P3 |
| Multi-device support | LOW | HIGH | P3 |
| Alerting / notifications | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | modbus-proxy (tiagocoutinho) | ha-modbusproxy (Akulatraxas) | evcc modbusproxy (built-in) | Our Approach |
|---------|-------------------------------|-------------------------------|------------------------------|--------------|
| Protocol translation | None (transparent TCP proxy) | None (transparent TCP proxy) | None (transparent TCP proxy) | Full translation: Luxtronik binary -> Modbus TCP |
| Register mapping | None | None | None | Curated default set + user-configurable names |
| Single-connection safety | Via serialization queue | Via serialization queue | Via serialization queue | Connect-poll-disconnect with configurable interval |
| Heat pump domain knowledge | None | None | None | Embedded: parameter IDs, data types, scaling, SG-ready mapping |
| SG-ready abstraction | None | None | None | Virtual register (0–3 int) mapped to mode combinations |
| Docker deployment | Yes | Yes (HA addon) | Built into evcc | Yes, plus systemd |
| YAML config | Yes | Yes | Yes | Yes |
| Bilingual docs | No | No | EN only | EN + DE |
| evcc integration docs | None | None | Native | Explicit YAML snippet + upstream PR planned |
| Authentication | None | None | None | None (LAN-only by design) |
| Target hardware | Any Modbus TCP device | Any Modbus TCP device | Any Modbus TCP device | Luxtronik 2.0 controllers specifically |

---

## Sources

- [evcc heat pump device documentation](https://docs.evcc.io/en/docs/devices/heating) — evcc operating mode model and SG-ready integration
- [evcc modbusproxy configuration reference](https://docs.evcc.io/en/docs/reference/configuration/modbusproxy) — proxy feature set and read-only options
- [evcc issue #19993: Support for Luxtronik Heatpumps](https://github.com/evcc-io/evcc/issues/19993) — required Luxtronik parameters for evcc; closed "not planned" April 2025
- [evcc issue #20760: Alpha Innotec / Luxtronik Modbus support](https://github.com/evcc-io/evcc/issues/20760) — register mapping discussion for ait heat pumps
- [evcc discussion #7153: Wärmepumpe mit Modbus/TCP](https://github.com/evcc-io/evcc/discussions/7153) — concrete register addresses: power (70-71), energy (68), hot water temp (11), power setpoint (125)
- [evcc discussion #17257: HA and evcc Modbus Proxy](https://github.com/evcc-io/evcc/discussions/17257) — coexistence problem statement and proxy approach
- [BenPru/luxtronik GitHub](https://github.com/BenPru/luxtronik) — writable parameters (~18), HA entity model, no connection-conflict documentation
- [Bouni/python-luxtronik GitHub](https://github.com/Bouni/python-luxtronik) — parameter categories, key writable IDs (ID_Ba_Hz_akt, ID_Ba_Bw_akt, ID_Soll_BWS_akt)
- [openHAB LuxtronikHeatpump binding](https://www.openhab.org/addons/bindings/luxtronikheatpump/) — full channel inventory: temperatures, operating modes, energy meters, smart grid hooks
- [modbus-proxy PyPI package](https://pypi.org/project/modbus-proxy/) — competing transparent proxy: YAML config, Docker, systemd, unit ID remapping
- [PyModbus documentation](https://www.pymodbus.org/docs/function-codes) — FC03/04/06/16 function codes, register types

---
*Feature research for: Modbus TCP proxy for Luxtronik 2.0 heat pump controllers*
*Researched: 2026-04-04*

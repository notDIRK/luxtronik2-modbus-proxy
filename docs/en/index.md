# luxtronik2-modbus-proxy

**luxtronik2-modbus-proxy** translates the proprietary Luxtronik 2.0 binary protocol (TCP port 8889)
into standard Modbus TCP (port 502), allowing evcc, Home Assistant, and any other Modbus-capable
energy management system to read and control older heat pumps that have no native Modbus interface.
It targets heat pumps from Alpha Innotec, Novelan, Buderus, Nibe, Roth, Elco, and Wolf equipped
with a Luxtronik 2.0 controller — thousands of units with no firmware upgrade path.

## Features

- **Modbus TCP server on port 502** — exposes heat pump state and controls via standard Modbus
  holding registers (FC3 read, FC6/FC16 write)
- **Connect-and-release polling** — connects to the Luxtronik controller briefly, reads or writes,
  then disconnects; coexists safely with Home Assistant's BenPru integration on the same controller
- **SG-ready virtual register** — write modes 0–3 via a single Modbus register; evcc uses this
  to shift heat pump load into solar surplus windows
- **Configurable register map** — expose additional Luxtronik parameters by symbolic name in
  `config.yaml`; all 1,126 parameters are available
- **Docker and systemd deployment** — run as a container or a native system service; configuration
  via `config.yaml` with environment variable overrides for Docker

## Getting Started

Choose your track:

- **Developer / contributor:** [Quick Start](quickstart.md) — clone, install, run from source
- **End user / non-technical:** [User Guide](user-guide.md) — Docker setup, no Python knowledge required

## Integration Guides

- [evcc Integration](evcc-integration.md) — configure evcc to use the proxy as a Modbus heat pump
- [HA Coexistence](ha-coexistence.md) — run the proxy alongside the HA BenPru/luxtronik integration

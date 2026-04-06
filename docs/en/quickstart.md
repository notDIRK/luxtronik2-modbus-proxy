# Quick Start

Get luxtronik2-modbus-proxy running from source in under 15 minutes.

## Prerequisites

- Python 3.10 or newer
- `pip` (comes with Python)
- `git`
- Docker (optional, for the Docker track in [Docker Alternative](#docker-alternative))

## Clone and Install

```bash
git clone https://github.com/OWNER/PUBLIC-luxtronik2-modbus-proxy.git
cd PUBLIC-luxtronik2-modbus-proxy
pip install -e ".[dev]"
```

The `[dev]` extra installs `pytest`, `ruff`, and `mypy` for development work. Omit it if you only want to run the proxy.

## Configure

```bash
cp config.example.yaml config.yaml
```

Open `config.yaml` in your editor and set `luxtronik_host` to your heat pump's IP address:

```yaml
luxtronik_host: "192.168.x.x"   # Replace with your heat pump IP
```

All other defaults are suitable for most installations. See the [User Guide](user-guide.md) for a full description of every config field.

## Run

```bash
luxtronik2-modbus-proxy --config config.yaml
```

On startup you will see structured log output. Expected events:

```
{"event": "proxy_starting", "modbus_port": 502, "luxtronik_host": "192.168.x.x", ...}
{"event": "proxy_running", "poll_interval": 30, ...}
```

After the first poll cycle completes:

```
{"event": "poll_cycle_complete", "registers_updated": 12, ...}
```

The proxy is now listening on port 502 for Modbus TCP clients.

## Verify

Use `modpoll` (a command-line Modbus client) to confirm the proxy is responding:

```bash
modpoll -m tcp -a 1 -r 1 -c 5 -t 4:int 127.0.0.1
```

This reads 5 holding registers starting at address 1, which correspond to temperature values. You should see five integer values in the output.

Install modpoll: `pip install modpoll` or download from [https://www.modbusdriver.com/modpoll.html](https://www.modbusdriver.com/modpoll.html).

## Run Tests

```bash
pytest
```

With coverage report:

```bash
pytest --cov=src
```

The test suite uses `pytest-asyncio` with `asyncio_mode = auto`; no additional flags are needed for async tests.

## Docker Alternative

If you prefer to run in a container rather than from source:

```bash
docker compose up -d
docker compose logs -f proxy
```

The container reads `config.yaml` from the current directory. Make sure you have created and configured it before starting.

## Next Steps

- **[User Guide](user-guide.md)** — complete configuration reference, Docker install walkthrough, and troubleshooting
- **[evcc Integration Guide](evcc-integration.md)** — configure evcc to control your heat pump via SG-ready
- **[HA Coexistence Guide](ha-coexistence.md)** — run the proxy alongside the BenPru Home Assistant integration without connection conflicts

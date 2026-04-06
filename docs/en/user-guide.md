# User Guide

Install and configure luxtronik2-modbus-proxy to connect your Luxtronik 2.0 heat pump to evcc or Home Assistant.

## What Does This Proxy Do?

Your heat pump controller speaks a proprietary binary protocol that only Luxtronik-specific software understands. Tools like evcc and Home Assistant use a completely different standard called Modbus. This proxy sits between the two: it talks to your heat pump in its native language, and it talks to evcc or Home Assistant in Modbus. You do not need to understand either protocol. Once the proxy is running, your heat pump appears to evcc and Home Assistant like any other Modbus device.

## Prerequisites

- **Docker** (recommended): Install Docker Desktop or Docker Engine from [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)
- **Alternative without Docker**: See the [systemd Service Guide](systemd.md) for running on Linux without containers
- Your heat pump must be reachable on your local network (you need its IP address)

## Installation (Docker)

### Step 1: Download the configuration template

```bash
cp config.example.yaml config.yaml
```

If you installed via Docker without cloning the repository, download the example file directly:

```bash
curl -o config.yaml https://raw.githubusercontent.com/OWNER/PUBLIC-luxtronik2-modbus-proxy/main/config.example.yaml
```

### Step 2: Edit the configuration

Open `config.yaml` in a text editor. Here is a description of every field:

#### `luxtronik_host`

```yaml
luxtronik_host: "192.168.x.x"
```

The IP address of your heat pump controller. This is the most important setting. Find your heat pump's IP in your router's device list, or look in the Luxtronik web interface under Settings > Network.

#### `luxtronik_port`

```yaml
luxtronik_port: 8889
```

The port used by the Luxtronik binary protocol. Leave this at 8889 unless you have specifically reconfigured your controller to use a different port. Almost no one needs to change this.

#### `modbus_port`

```yaml
modbus_port: 502
```

The port the proxy listens on for incoming Modbus TCP connections. Port 502 is the Modbus standard. Change this only if another service is already using port 502 on your system.

#### `bind_address`

```yaml
bind_address: "0.0.0.0"
```

The network interface the proxy listens on. Leave at `0.0.0.0` to allow connections from any device on your network. Set to a specific IP address (e.g., `192.168.x.x`) to restrict access to connections arriving on a single interface.

#### `poll_interval`

```yaml
poll_interval: 30
```

How often the proxy reads data from your heat pump, in seconds. The proxy connects to the heat pump, reads all mapped registers, updates its internal state, and then disconnects. A value of 30 seconds is recommended for most setups, especially if you are also running the Home Assistant BenPru integration. Setting this too low can cause connection conflicts.

#### `log_level`

```yaml
log_level: "INFO"
```

Controls how much information the proxy logs. Use `INFO` for normal operation. Set to `DEBUG` when troubleshooting a problem — it produces much more detailed output. Other options are `WARNING` and `ERROR` for quieter logs.

#### `enable_writes`

```yaml
enable_writes: false
```

Set to `true` if you want evcc to be able to control your heat pump (for example, to switch between SG-ready modes for load shifting). When this is `false`, the proxy is read-only and evcc cannot change any settings. Start with `false` and test carefully before enabling writes.

#### `write_rate_limit`

```yaml
write_rate_limit: 60
```

The minimum number of seconds that must pass between write commands to the same register. This protects the NAND flash memory inside your heat pump controller from excessive writes. The default of 60 seconds is appropriate for SG-ready mode switching. Do not set this below 10 seconds.

#### `registers.parameters` (optional, advanced)

```yaml
# registers:
#   parameters:
#     - ID_Einst_WK_akt
#     - ID_Ba_Hz_MK3_akt
```

Additional Luxtronik parameters to expose as Modbus registers, beyond the curated default set. The defaults cover all registers needed for evcc and Home Assistant. Use `luxtronik2-modbus-proxy list-params --search <term>` to browse the full list of 1,126 available parameters.

#### `sg_ready_mode_map` (optional, advanced)

```yaml
# sg_ready_mode_map: ...
```

Custom SG-ready mode mapping for non-standard heat pump configurations. Leave this commented out unless you know your heat pump uses non-default parameter IDs for SG-ready signaling.

### Step 3: Start the proxy

```bash
docker compose up -d
```

### Step 4: Check the logs

```bash
docker compose logs -f proxy
```

## Verifying It Works

After starting, you should see log messages like these:

```
{"event": "proxy_starting", "modbus_port": 502, ...}
{"event": "proxy_running", "poll_interval": 30, ...}
```

After the first poll cycle (within `poll_interval` seconds):

```
{"event": "poll_cycle_complete", "registers_updated": 12, ...}
```

You should see a new `poll_cycle_complete` message every 30 seconds (or at whatever `poll_interval` you set). If the event never appears, see the Troubleshooting section below.

## Connecting evcc

See the [evcc Integration Guide](evcc-integration.md) for the complete YAML configuration to add to your evcc setup.

## Connecting Home Assistant

See the [HA Coexistence Guide](ha-coexistence.md) for running the proxy alongside the BenPru integration without connection conflicts.

## Troubleshooting

### "Connection refused" or "Could not connect" on port 8889

The proxy cannot reach your heat pump. Check:
- The IP address in `config.yaml` is correct
- The heat pump controller is powered on
- Your computer or server can reach the heat pump on your network (try `ping 192.168.x.x`)
- No firewall is blocking port 8889

### "Address already in use" on port 502

Another service is already listening on Modbus port 502. Either stop that service, or change `modbus_port` to a different port (e.g., 5020) in `config.yaml` and update your evcc/HA config accordingly.

### "Poll cycle failed" in logs

A transient connection error occurred when reading from the heat pump. The proxy will retry on the next poll cycle. If this happens repeatedly, check the `luxtronik_host` setting and network connectivity.

### The proxy starts but registers show zero or stale values

The first poll cycle may not have completed yet. Wait up to `poll_interval` seconds after startup. If values remain zero after a full cycle, enable `DEBUG` logging to see detailed read output.

## Alternative: systemd Service

If you prefer running without Docker, see the [systemd Service Guide](systemd.md) for installing the proxy as a native Linux service.

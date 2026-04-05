# evcc Integration Guide

This guide explains how to configure [evcc](https://evcc.io/) to control your Luxtronik 2.0
heat pump via the luxtronik2-modbus-proxy. The proxy exposes a Modbus TCP interface on port 502,
which evcc uses to read operating state and write SG-ready mode commands.

## Prerequisites

- luxtronik2-modbus-proxy running and reachable from the evcc host
- evcc installed and running (see [evcc documentation](https://docs.evcc.io/))
- Network connectivity between evcc and the proxy (TCP port 502)
- `enable_writes: true` set in the proxy `config.yaml` (required for SG-ready writes)

## evcc Configuration

Add the following to your `evcc.yaml`. Replace `192.168.x.x` with the IP address of the
machine running the proxy.

```yaml
# evcc.yaml — Luxtronik2 Modbus Proxy integration
# Add this block to your evcc.yaml heatsources or chargers section

heatsources:
  - name: heat_pump
    type: custom

    # SG-ready mode write (FC6 write holding register 5000)
    setmode:
      source: modbus
      uri: 192.168.x.x:502   # Replace with your proxy host IP and Modbus port
      id: 1
      register:
        address: 5000         # SG-ready virtual register (0-based)
        type: writeholding
        decode: uint16

    # SG-ready mode read (FC3 read holding register 5000)
    getmode:
      source: modbus
      uri: 192.168.x.x:502   # Replace with your proxy host IP and Modbus port
      id: 1
      register:
        address: 5000         # SG-ready virtual register (0-based)
        type: holding
        decode: uint16

    # Optional: read current heat pump power consumption (input register 257)
    power:
      source: modbus
      uri: 192.168.x.x:502
      id: 1
      register:
        address: 257          # Heat output (watts, input register, 0-based)
        type: input
        decode: uint16
```

> **Note:** All register addresses are 0-based (the Modbus wire address). evcc uses
> the same 0-based convention. Do not add 1 to these addresses.

## SG-Ready Mode Mapping

The proxy translates evcc's SG-ready mode (0–3) to Luxtronik HeatingMode and HotWaterMode
parameter writes:

| evcc Mode | Name | HeatingMode (param 3) | HotWaterMode (param 4) | Description |
|-----------|------|-----------------------|------------------------|-------------|
| 0 | EVU Lock | Off (4) | Off (4) | Grid operator lock — heat pump blocked |
| 1 | Normal | Automatic (0) | Automatic (0) | Normal operation |
| 2 | Recommended | Party (2) | Automatic (0) | Increased consumption recommended |
| 3 | Force On | Automatic (0) | Party (2) | Maximum consumption (surplus energy) |

Reading register 5000 returns the last successfully applied mode. The register is
initialized to mode 1 (Normal) at proxy startup.

## Important Notes

### Writes must be enabled

SG-ready writes require `enable_writes: true` in the proxy `config.yaml`:

```yaml
# config.yaml
enable_writes: true
write_rate_limit: 60   # Minimum seconds between writes to the same register
```

Without this setting, all write commands are rejected with a Modbus exception.

### Mode mapping is assumed

The mode-to-parameter mapping is based on community consensus from evcc and Home Assistant
forums and is marked **[ASSUMED]**. Validate the behavior on your specific hardware
(especially the EVU lock mode 0) before relying on it in production.

### Custom mode mapping

If your heat pump requires different parameter values, configure a custom mode map in
`config.yaml`:

```yaml
# config.yaml — Custom SG-ready mode map example
sg_ready_mode_map:
  0: {3: 4, 4: 4}   # EVU lock: HeatingMode=Off, HotWaterMode=Off
  1: {3: 0, 4: 0}   # Normal: HeatingMode=Auto, HotWaterMode=Auto
  2: {3: 2, 4: 0}   # Recommended: HeatingMode=Party, HotWaterMode=Auto
  3: {3: 0, 4: 2}   # Force on: HeatingMode=Auto, HotWaterMode=Party
```

Keys are Luxtronik parameter indices (3 = HeatingMode, 4 = HotWaterMode).
Values are the raw integer values from the Luxtronik library enums.

### Write rate limiting

Each register is limited to one write per `write_rate_limit` seconds (default: 60s).
Rapid SG-ready mode changes from evcc are rate-limited on the underlying parameters
(addresses 3 and 4). The SG-ready virtual register (address 5000) itself is not
rate-limited — the rate limit applies to the Luxtronik controller writes.

## Additional Registers

Beyond SG-ready, the proxy exposes the following registers that evcc or other tools
can read for monitoring:

### Temperature Registers (input registers, FC4, unit: °C × 10)

| Address | Parameter | Unit | Description |
|---------|-----------|------|-------------|
| 10 | Flow temperature | °C × 10 (int16) | Heat carrier supply temperature |
| 11 | Return temperature | °C × 10 (int16) | Heat carrier return temperature |
| 15 | Outside temperature | °C × 10 (int16) | Outside air temperature |
| 17 | Hot water temperature | °C × 10 (int16) | Hot water actual temperature |

Divide the raw register value by 10 to get degrees Celsius. Example: value 215 = 21.5 °C.

### Operating State Registers (input registers, FC4)

| Address | Parameter | Unit | Description |
|---------|-----------|------|-------------|
| 80 | Operating mode | uint16 | Current heat pump operating state |
| 257 | Heat output | watts (uint16) | Current heat output |

### Writable Mode Registers (holding registers, FC3/FC6)

| Address | Parameter | Allowed Values | Description |
|---------|-----------|----------------|-------------|
| 3 | HeatingMode | 0–4 | 0=Auto, 1=Second heater, 2=Party, 3=Holiday, 4=Off |
| 4 | HotWaterMode | 0–4 | 0=Auto, 1=Second heater, 2=Party, 3=Holiday, 4=Off |
| 5000 | SG-ready mode | 0–3 | Virtual register: translates to modes above |

## Troubleshooting

### Write rejected (Modbus exception response)

**Symptom:** evcc reports a write error when setting SG-ready mode.

**Cause 1:** `enable_writes` is `false` in proxy config.
**Fix:** Set `enable_writes: true` in `config.yaml` and restart the proxy.

**Cause 2:** Mode value outside 0–3.
**Fix:** Verify evcc is sending integer values 0, 1, 2, or 3 only.

### Illegal data address (Modbus exception code 2)

**Symptom:** Modbus client reports "Illegal data address" for a register.

**Cause:** The register address is outside the proxy's mapped range, or a 1-based
address is being used where a 0-based address is expected.
**Fix:** Verify that the register address is 0-based. The proxy uses 0-based addressing.
Register 5000 (0-based) is the SG-ready register.

### Connection refused

**Symptom:** evcc cannot connect to the proxy.

**Cause:** Proxy is not running, or wrong host/port configured.
**Fix:** Verify the proxy is running (`docker ps` or `systemctl status`) and that
port 502 is reachable from the evcc host. Check proxy logs for startup errors.

### Rate limit warning in proxy logs

**Symptom:** Proxy logs show `write_rate_limited` warnings.

**Cause:** evcc sent multiple SG-ready mode changes within the `write_rate_limit`
window (default: 60 seconds).
**Fix:** This is normal behavior — the rate limit protects the controller's NAND flash.
The last mode change will be applied on the next unrestricted write opportunity.
If you need faster response, reduce `write_rate_limit` (minimum: 10 seconds).

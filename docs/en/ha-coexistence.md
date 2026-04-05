# Running Alongside Home Assistant

This guide explains how to run luxtronik2-modbus-proxy alongside the
[Home Assistant BenPru/luxtronik integration](https://github.com/BenPru/luxtronik)
(also known as the HA HACS integration). Both can share a single Luxtronik 2.0 controller
without conflict, as long as you understand the single-connection constraint.

## Background: The Single-Connection Constraint

Luxtronik 2.0 controllers (port 8889) allow **exactly one TCP connection at a time**. Any
second connection attempt while the port is held will be refused. This is a hardware
limitation that cannot be changed via configuration or firmware.

Both the proxy and the HA BenPru integration handle this correctly by using a
**connect-read/write-disconnect** pattern: each tool connects briefly, reads or writes
what it needs, then immediately disconnects. Neither tool holds the connection open
between operations.

## How Coexistence Works

```
Timeline:

[proxy]     CONNECT → READ → DISCONNECT ... (idle 30s) ... CONNECT → READ → DISCONNECT
[HA BenPru]                       CONNECT → READ → DISCONNECT ... (idle 30s) ...
```

Because both systems disconnect immediately after each operation, they naturally
interleave without blocking each other. The connection is typically held for less
than a second per cycle.

**Port separation:**

- The proxy connects **outbound** to the Luxtronik controller on port 8889.
- The proxy serves Modbus TCP clients **inbound** on port 502.
- HA BenPru connects **outbound** to the Luxtronik controller on port 8889.
- HA Modbus integration (if used) connects **inbound** to the proxy on port 502.

There is no port conflict: port 8889 is shared (briefly, sequentially); port 502 is
served only by the proxy.

## What Each System Reads and Writes

| System | Role | Port | Data Types |
|--------|------|------|------------|
| Proxy | Outbound client to Luxtronik | 8889 (outgoing) | Parameters (read/write), Calculations (read-only), Visibilities (read-only) |
| HA BenPru | Outbound client to Luxtronik | 8889 (outgoing) | Parameters, Calculations |
| evcc | Inbound Modbus client to proxy | 502 (incoming to proxy) | Holding registers (SG-ready, modes) |
| HA Modbus integration | Inbound Modbus client to proxy | 502 (incoming to proxy) | Holding + input registers |

The proxy and HA BenPru both read from port 8889 on the Luxtronik controller. The proxy
additionally caches the values and serves them to Modbus clients on port 502.

## Recommended Configuration

### Proxy `poll_interval`

The proxy polling interval controls how often it connects to port 8889. The default (30s)
is designed to leave plenty of room for HA BenPru to interleave.

```yaml
# config.yaml
poll_interval: 30   # Recommended for coexistence with HA BenPru
```

- **30 seconds**: Default, good for most setups. Leaves ~29 seconds idle per cycle.
- **60 seconds**: Conservative; use this if you see repeated connection errors in proxy logs.
- **15 seconds**: Minimum recommended for coexistence. Below this, collisions become likely.
- **10 seconds**: Absolute minimum (proxy enforces this floor). Not recommended with HA BenPru.

### HA BenPru scan interval

The BenPru integration polls on its own schedule (typically 30–60 seconds by default).
You do not need to change this. As long as both systems use the connect-disconnect pattern
(which they do), the timing naturally staggers over time.

If you want to guarantee they never overlap, stagger the startup times (start the proxy
a few seconds before HA) so their polling cycles are offset. This is optional.

## Write Conflict Guidance

Both the proxy (via evcc) and HA BenPru can write Luxtronik parameters. Writing the same
parameter from two systems simultaneously can lead to unpredictable behavior — each
system's value overwrites the other.

### Recommended write separation

| System | Should Write | Should Not Write |
|--------|-------------|------------------|
| Proxy (via evcc SG-ready) | HeatingMode (param 3), HotWaterMode (param 4) | — |
| HA BenPru automations | Operating modes for schedules, setpoints | HeatingMode, HotWaterMode if proxy/evcc manages SG-ready |

**Rule of thumb:** Assign each writable parameter to exactly one controller. If evcc
manages SG-ready (which writes HeatingMode and HotWaterMode), do not also write those
parameters from HA automations.

### SG-ready specific guidance

When evcc sends an SG-ready mode command to the proxy, the proxy writes to:
- Parameter 3 (HeatingMode)
- Parameter 4 (HotWaterMode)

If HA simultaneously writes to either of these parameters, the last write wins and the
system may be in an inconsistent state. Choose one of:

1. **evcc owns SG-ready**: evcc writes mode via proxy. HA BenPru reads-only. HA
   automations do not write HeatingMode or HotWaterMode while evcc is active.

2. **HA owns operating modes**: HA BenPru writes HeatingMode and HotWaterMode directly.
   evcc SG-ready is not used. The proxy is read-only from evcc's perspective.

3. **Coordinated via HA**: HA receives both the Tibber/grid signal and the heat pump
   state. HA automation decides which mode to apply, either directly via BenPru or
   by writing the SG-ready register via the proxy's Modbus interface. This gives full
   control in one place.

## Troubleshooting Connection Issues

### Proxy logs show repeated connection errors

**Symptom:** Proxy logs contain `poll_cycle_failed` with connection refused errors
every 30 seconds.

**Cause:** HA BenPru is holding the Luxtronik socket at the same time the proxy
attempts to connect. This is rare but can happen if HA's polling cycle aligns with
the proxy's.

**Fix:**
1. Increase proxy `poll_interval` from 30s to 60s to reduce collision probability.
2. Restart the proxy a few seconds after HA to stagger the cycles.
3. Check if any HA automation holds the BenPru integration's connection open by
   triggering many rapid reads.

The proxy is resilient to connection errors — it logs the failure, marks its cache as
stale, and retries on the next cycle. A few missed polls do not cause data loss.

### HA BenPru shows entity as "unavailable"

**Symptom:** HA entities from the BenPru integration show "unavailable" periodically.

**Cause:** The proxy connected to the Luxtronik socket at the same time HA BenPru
attempted its poll. BenPru's connection was refused, causing a temporary unavailability.

**Fix:** This is usually transient (one missed poll = ~30s unavailability). If it
happens frequently, increase the proxy `poll_interval` to 60s to reduce overlap.

The proxy releases the socket within a fraction of a second per cycle, so long-term
blocking of HA BenPru should not occur with `poll_interval >= 30s`.

### Both systems show stale data

**Symptom:** Both the proxy cache and HA BenPru entities show outdated values.

**Cause:** The Luxtronik controller is unreachable (network issue, controller restart,
or power outage).

**Fix:** Verify the Luxtronik controller is reachable on port 8889 from both the proxy
host and the HA host. Check controller power and network cable. The proxy marks its
cache as stale when reads fail — check proxy logs for connection errors.

## Architecture Summary

```
                        ┌─────────────────┐
                        │  Luxtronik 2.0  │
                        │  Controller     │
                        │  port 8889      │
                        └────────┬────────┘
                                 │  (one connection at a time)
              ┌──────────────────┴──────────────────┐
              │                                     │
      connect-read-disconnect               connect-read-disconnect
              │                                     │
   ┌──────────▼──────────┐              ┌──────────▼──────────┐
   │  luxtronik2-        │              │  HA BenPru          │
   │  modbus-proxy       │              │  integration        │
   │  (port 502 server)  │              │  (reads only)       │
   └──────────┬──────────┘              └─────────────────────┘
              │
     Modbus TCP port 502
              │
    ┌─────────┴──────────┐
    │                    │
    ▼                    ▼
  evcc              HA Modbus
  (SG-ready         integration
  mode writes)      (read registers)
```

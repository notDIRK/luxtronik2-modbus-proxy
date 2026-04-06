# systemd Service

Run luxtronik2-modbus-proxy as a systemd service on Linux.

## When to Use systemd

Use **systemd** if:
- You have a Linux server (Raspberry Pi, NAS, home server) that does not run Docker
- You prefer native service management with `systemctl`
- You want the proxy to start automatically at boot without a container runtime

Use **Docker** if:
- You already use Docker on your server
- You want container isolation and easy updates
- You prefer a single-file deployment with `docker compose`

See the [User Guide](user-guide.md) for the Docker installation path.

## Prerequisites

- A Linux system with systemd (most modern Linux distributions)
- Python 3.10 or newer
- `pip`
- `sudo` access to install the service file

## Install the Proxy

Install from PyPI:

```bash
pip install luxtronik2-modbus-proxy
```

Or install directly from the GitHub repository:

```bash
pip install git+https://github.com/OWNER/PUBLIC-luxtronik2-modbus-proxy.git
```

After installation, verify the command is available:

```bash
luxtronik2-modbus-proxy --version
```

## Create System User

Run the proxy as a dedicated non-root system user for security:

```bash
sudo useradd -r -s /bin/false luxtronik-proxy
```

This creates a system account (`-r`) with no login shell (`-s /bin/false`). The proxy process will run as this user.

## Install Configuration

Create the configuration directory and copy the example file:

```bash
sudo mkdir -p /etc/luxtronik2-modbus-proxy
sudo cp config.example.yaml /etc/luxtronik2-modbus-proxy/config.yaml
sudo nano /etc/luxtronik2-modbus-proxy/config.yaml
```

At minimum, set `luxtronik_host` to your heat pump's IP address:

```yaml
luxtronik_host: "192.168.x.x"   # Replace with your heat pump IP
```

See the [User Guide](user-guide.md) for a description of all configuration fields.

Give the service user read access to the config file:

```bash
sudo chown root:luxtronik-proxy /etc/luxtronik2-modbus-proxy/config.yaml
sudo chmod 640 /etc/luxtronik2-modbus-proxy/config.yaml
```

## Install Service File

Copy the provided service file template to the systemd directory:

```bash
sudo cp contrib/luxtronik2-modbus-proxy.service /etc/systemd/system/
```

If you installed from PyPI without cloning the repository, download the service file directly:

```bash
sudo curl -o /etc/systemd/system/luxtronik2-modbus-proxy.service \
  https://raw.githubusercontent.com/OWNER/PUBLIC-luxtronik2-modbus-proxy/main/contrib/luxtronik2-modbus-proxy.service
```

Reload systemd and enable the service to start at boot:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now luxtronik2-modbus-proxy
```

The `--now` flag starts the service immediately in addition to enabling it at boot.

## Check Status

```bash
sudo systemctl status luxtronik2-modbus-proxy
```

A healthy service shows `active (running)`. If it shows `failed`, check the logs (see below).

## View Logs

Follow live log output:

```bash
journalctl -u luxtronik2-modbus-proxy -f
```

Show the last 50 log lines:

```bash
journalctl -u luxtronik2-modbus-proxy -n 50
```

The proxy uses structlog with JSON output, which journald captures automatically. You should see `proxy_starting`, `proxy_running`, and recurring `poll_cycle_complete` events.

## Environment Variable Overrides

You can override any configuration value using environment variables, without editing `config.yaml`. This is useful when the same config file is shared across environments.

Create an environment file at `/etc/luxtronik2-modbus-proxy/env`:

```bash
sudo nano /etc/luxtronik2-modbus-proxy/env
```

Add `KEY=VALUE` pairs using the `LUXTRONIK_` prefix. For example:

```
LUXTRONIK_HOST=192.168.x.x
LUXTRONIK_POLL_INTERVAL=60
LUXTRONIK_LOG_LEVEL=DEBUG
```

The service file already contains `EnvironmentFile=-/etc/luxtronik2-modbus-proxy/env` (the `-` prefix makes it optional — the service starts even if the file does not exist).

After editing the env file, restart the service:

```bash
sudo systemctl restart luxtronik2-modbus-proxy
```

## Troubleshooting

### Service fails to start

Check the full log output immediately after the failure:

```bash
journalctl -u luxtronik2-modbus-proxy -n 100 --no-pager
```

Look for `error` or `exception` events. Common causes:
- Config file not found: verify `/etc/luxtronik2-modbus-proxy/config.yaml` exists and is readable by the `luxtronik-proxy` user
- Invalid YAML: open the config file and check for indentation or syntax errors
- Python not found at the path in `ExecStart`: run `which luxtronik2-modbus-proxy` as root to find the correct path, then update the service file

### "Permission denied" when binding port 502

Port 502 is a privileged port (below 1024) that requires root or a capability grant. Options:

1. Grant the capability to the Python binary (recommended):
   ```bash
   sudo setcap 'cap_net_bind_service=+ep' $(which python3)
   ```
2. Or change `modbus_port` to a non-privileged port (e.g., 5020) in `config.yaml` and update your evcc/HA config to use that port.

### Config file not found at startup

Verify the path in the service file matches where you placed `config.yaml`:

```bash
grep ExecStart /etc/systemd/system/luxtronik2-modbus-proxy.service
```

If the path differs, edit the service file and reload:

```bash
sudo systemctl daemon-reload
sudo systemctl restart luxtronik2-modbus-proxy
```

### Service restarts too often and gets throttled

systemd rate-limits services that restart repeatedly. The service file includes `StartLimitIntervalSec=60` and `StartLimitBurst=3` to prevent restart loops. If the proxy is failing on startup due to a config error, fix the error first before trying to restart:

```bash
journalctl -u luxtronik2-modbus-proxy -n 50
# Fix the config error, then:
sudo systemctl reset-failed luxtronik2-modbus-proxy
sudo systemctl start luxtronik2-modbus-proxy
```

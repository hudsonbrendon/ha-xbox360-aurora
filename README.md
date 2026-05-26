# Xbox 360 Aurora — Home Assistant integration

Monitor and control a jailbroken (RGH/JTAG) Xbox 360 running the **Aurora** dashboard with the **NOVA** plugin.

## Features

- **Sensors:** current title (title ID), CPU/GPU/case temperature, free RAM.
- **Connectivity:** an `online` binary sensor (on while NOVA responds).
- **Buttons:** reboot and shutdown (via Aurora's FTP `SITE` commands).
- **Service `xbox360_aurora.launch_title`:** launch an executable by `exec` + `path` + `type`.

Power-ON is **not** supported: RGH/JTAG Xbox 360 consoles do not respond to Wake-on-LAN. Use a smart plug or IR blaster separately if you need remote power-on.

## Requirements on the console

1. Aurora dashboard installed with the NOVA plugin (bundled in Aurora 0.7b+).
2. NOVA web server enabled. Note its port (default `9999`) and credentials (default `xboxhttp` / `xboxhttp`).
3. Aurora FTP server enabled (Start → Modules → FTP Server). Default port `21`, credentials `xboxftp` / `xboxftp`.

## Installation (HACS custom repository)

1. HACS → Integrations → ⋮ → Custom repositories.
2. Add `https://github.com/hudsonbrendon/ha-xbox360-aurora` as an Integration.
3. Install "Xbox 360 Aurora", restart Home Assistant.
4. Settings → Devices & Services → Add Integration → "Xbox 360 Aurora".
5. Enter the console IP, NOVA port/credentials, and FTP port/credentials.

## Service example

```yaml
service: xbox360_aurora.launch_title
data:
  exec: default.xex
  path: 'Hdd1:\Games\MyGame'
  type: 0
```

## Development

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-test.txt
.venv/bin/pytest -v
```

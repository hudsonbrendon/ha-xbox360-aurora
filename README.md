<p align="center">
  <img src="assets/xbox360-icon.png" alt="Xbox 360" height="120">
</p>
<p align="center">
  <img src="assets/xbox360-logo.png" alt="Xbox 360" width="360">
</p>

# Xbox 360 Aurora for Home Assistant

[![Tests](https://github.com/hudsonbrendon/ha-xbox360-aurora/actions/workflows/test.yml/badge.svg)](https://github.com/hudsonbrendon/ha-xbox360-aurora/actions/workflows/test.yml)
[![Validate](https://github.com/hudsonbrendon/ha-xbox360-aurora/actions/workflows/validate.yml/badge.svg)](https://github.com/hudsonbrendon/ha-xbox360-aurora/actions/workflows/validate.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![Release](https://img.shields.io/github/v/release/hudsonbrendon/ha-xbox360-aurora)](https://github.com/hudsonbrendon/ha-xbox360-aurora/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Monitor and control a jailbroken (**RGH/JTAG**) Xbox 360 running the
[**Aurora**](https://consolemods.org/wiki/Xbox_360:Aurora) dashboard with the
**NOVA** plugin — the running title, temperatures, free RAM, online status, plus
launch-a-game, reboot, and shutdown.

> Talks to the NOVA REST API (port `9999`, JWT auth) for monitoring and launching,
> and to Aurora's FTP server (port `21`, `SITE` commands) for reboot/shutdown.
> Not affiliated with Microsoft or the Aurora/NOVA developers.

## Features

- 🎮 **Now playing** — Title ID of the running game or app.
- 🌡️ **Temperatures** — CPU, GPU, and case sensors (°C).
- 🧠 **Free RAM** — available memory in MB.
- 📡 **Online status** — a connectivity binary sensor that flips off when the console
  is unreachable.
- 🚀 **Launch titles** — a `launch_title` service to start any executable remotely.
- 🔁 **Reboot / Shutdown** — buttons that issue Aurora FTP `SITE` commands.
- 🏠 **Local polling** — everything runs on your LAN; no cloud, no account.

> ⚡ **Power-ON is not supported.** RGH/JTAG Xbox 360 consoles do not respond to
> Wake-on-LAN. To turn the console on remotely, pair this with a smart plug or an
> IR blaster as a separate device.

## Requirements

**On the console:**

1. [Aurora](https://consolemods.org/wiki/Xbox_360:Aurora) installed with the **NOVA**
   plugin (bundled with Aurora 0.7b+).
2. **NOVA web server enabled** — note its port (default `9999`) and credentials
   (default `xboxhttp` / `xboxhttp`).
3. **Aurora FTP server enabled** (press <kbd>Start</kbd> → **Settings → Network → FTP
   Server**, or **Modules → FTP Server**). Default port `21`, credentials
   `xboxftp` / `xboxftp`.
4. A static IP / DHCP reservation for the console is recommended.

**On Home Assistant:**

- Home Assistant **2024.12** or newer, with network access to the console.

## Installation

### HACS (recommended)

1. In Home Assistant, open **HACS → ⋮ (top right) → Custom repositories**.
2. Add the repository URL `https://github.com/hudsonbrendon/ha-xbox360-aurora`
   and choose the **Integration** category.
3. Search for **Xbox 360 Aurora** in HACS, install it, and **restart Home Assistant**.

### Manual

1. Copy `custom_components/xbox360_aurora/` into your Home Assistant
   `config/custom_components/` directory.
2. Restart Home Assistant.

## Setup

1. Go to **Settings → Devices & Services → Add Integration** and search for
   **Xbox 360 Aurora**.
2. Fill in the form:

   | Field | Default | Notes |
   |---|---|---|
   | Host (IP address) | — | Your console's LAN IP, e.g. `192.168.1.50` |
   | NOVA port | `9999` | NOVA web server port |
   | NOVA username / password | `xboxhttp` / `xboxhttp` | From Aurora's NOVA settings |
   | FTP port | `21` | Aurora FTP server port |
   | FTP username / password | `xboxftp` / `xboxftp` | From Aurora's FTP settings |

3. The credentials are validated against NOVA on submit. On success the device and
   all entities are created immediately.

## Entities

The integration creates a single device, **Xbox 360 (`<host>`)**, with:

| Entity | Type | Description |
|---|---|---|
| `sensor.xbox_360_<host>_current_title` | sensor | Title ID (hex) of the running game/app |
| `sensor.xbox_360_<host>_cpu_temperature` | sensor | CPU temperature (°C) |
| `sensor.xbox_360_<host>_gpu_temperature` | sensor | GPU temperature (°C) |
| `sensor.xbox_360_<host>_case_temperature` | sensor | Case temperature (°C) |
| `sensor.xbox_360_<host>_free_ram` | sensor | Free RAM (MB) |
| `binary_sensor.xbox_360_<host>_online` | binary_sensor | `on` while NOVA responds (connectivity) |
| `button.xbox_360_<host>_reboot` | button | Power-cycle the console (FTP `SITE REBOOT`) |
| `button.xbox_360_<host>_shutdown` | button | Power off the console (FTP `SITE SHUTDOWN`) |

When the console is off or unreachable, the sensors become `unavailable` and the
`online` binary sensor reports `off`.

## Service: `xbox360_aurora.launch_title`

Launch an executable on the console via NOVA.

| Field | Required | Default | Description |
|---|---|---|---|
| `exec` | yes | — | Executable filename, e.g. `default.xex` |
| `path` | yes | — | Aurora drive path to the folder, e.g. `Hdd1:\Games\MyGame` |
| `type` | no | `0` | `-1` none, `0` xex, `1` xbe, `2` xex container, `3` xbe container, `4` XNA |

```yaml
service: xbox360_aurora.launch_title
data:
  exec: default.xex
  path: 'Hdd1:\Games\MyGame'
  type: 0
```

## Automation example

Notify when the console comes online and turn on the TV:

```yaml
automation:
  - alias: Xbox 360 online → turn on TV
    trigger:
      - platform: state
        entity_id: binary_sensor.xbox_360_192_168_1_50_online
        to: "on"
    action:
      - service: media_player.turn_on
        target:
          entity_id: media_player.living_room_tv
```

## Troubleshooting

- **"Failed to connect" during setup** — confirm the console is on the dashboard, the
  NOVA web server is enabled, and the IP/port are reachable from Home Assistant
  (`curl http://<host>:9999/`).
- **"Invalid NOVA username or password"** — check the credentials in Aurora's NOVA
  settings; defaults are `xboxhttp` / `xboxhttp`.
- **Reboot/Shutdown buttons do nothing** — these use FTP, not NOVA. Make sure Aurora's
  FTP server is enabled and the FTP port/credentials in the config match.
- **Entities show `unavailable`** — expected while the console is off or sitting in a
  game that suspends NOVA; they recover on the next successful poll (every 30 s).

## Development

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-test.txt
.venv/bin/pytest -v
```

## Credits

- [Aurora](https://consolemods.org/wiki/Xbox_360:Aurora) and the NOVA plugin by the
  Aurora team.
- NOVA API reference:
  [jrobiche/xbox360-aurora-developer-documentation](https://github.com/jrobiche/xbox360-aurora-developer-documentation).

## License

[MIT](LICENSE) © Hudson Brendon

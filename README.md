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
**NOVA** plugin — the running title, temperatures, RAM, online status, profile,
network bandwidth, hardware diagnostics, plus launch-a-game, pause/resume,
reboot, shutdown, and restart-Aurora.

> Talks to the NOVA REST API (port `9999`, JWT auth) for monitoring and launching,
> and to Aurora's FTP server (port `21`, `SITE` commands) for reboot/shutdown/restart.
> Not affiliated with Microsoft or the Aurora/NOVA developers.

## Features

- 🎮 **Now playing** — the running game's name (resolved from a bundled Title ID
  database of 1700+ titles); the raw `title_id` is kept as an attribute. Unknown
  titles fall back to the hex ID.
- 🌡️ **Temperatures** — CPU, GPU, case, and memory sensors (°C).
- 🧠 **RAM** — free, used, total (MB), and usage (%).
- 📡 **Online status** — a connectivity binary sensor that flips off when the console
  is unreachable.
- 🕹️ **SMC** — disc tray state, video output (HDMI/Component/VGA/Composite),
  console orientation, and SMC firmware version.
- 🖥️ **System diagnostics** — motherboard revision, console type (Retail/Devkit),
  dashboard version, serial number, and console ID.
- 👤 **Profile** — signed-in gamertag, gamerscore, and count of signed-in profiles.
- 🌐 **Network (LiNK)** — real-time download/upload rate and cumulative totals.
- ⏸️ **Game paused switch** — suspend or resume the running title's main thread via
  NOVA `/thread/state` (optimistic).
- 🚀 **Launch titles** — a `launch_title` service to start any executable remotely.
- 🔁 **Reboot / Shutdown / Restart Aurora** — buttons that issue Aurora FTP `SITE`
  commands.
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

## Options

After setup, open the integration's **Configure** menu to adjust:

| Option | Default | Range | Notes |
|---|---|---|---|
| Polling interval | `30` s | 10 – 600 s | How often NOVA is polled for sensor data |

Changes take effect immediately (the integration reloads automatically).

## Diagnostics

Go to **Settings → Devices & Services → Xbox 360 Aurora → Download Diagnostics** to
export a redacted snapshot useful for bug reports. The following fields are always
redacted: NOVA password, FTP password, `cpukey`, `dvdkey`, `serial`, `consoleid`.

## Entities

The integration creates a single device, **Xbox 360 (`<host>`)**, with:

| Entity | Type | Description |
|---|---|---|
| `sensor.xbox_360_<host>_current_title` | sensor | Running game/app name (e.g. `Call of Duty: Black Ops II`); raw ID in the `title_id` attribute. Falls back to the hex ID for unknown titles |
| `sensor.xbox_360_<host>_cpu_temperature` | sensor | CPU temperature (°C) |
| `sensor.xbox_360_<host>_gpu_temperature` | sensor | GPU temperature (°C) |
| `sensor.xbox_360_<host>_case_temperature` | sensor | Case temperature (°C) |
| `sensor.xbox_360_<host>_memory_temperature` | sensor | Memory temperature (°C) |
| `sensor.xbox_360_<host>_free_ram` | sensor | Free RAM (MB) |
| `sensor.xbox_360_<host>_used_ram` | sensor | Used RAM (MB) |
| `sensor.xbox_360_<host>_total_ram` | sensor | Total RAM (MB; diagnostic) |
| `sensor.xbox_360_<host>_ram_usage` | sensor | RAM usage (%) |
| `sensor.xbox_360_<host>_disc_tray` | sensor | Disc tray state (idle/closing/open/opening/closed/error) |
| `sensor.xbox_360_<host>_video_output` | sensor | Video output (HDMI/Component/VGA/Composite; diagnostic) |
| `sensor.xbox_360_<host>_orientation` | sensor | Console orientation (vertical/horizontal; diagnostic) |
| `sensor.xbox_360_<host>_smc_version` | sensor | SMC firmware version (diagnostic) |
| `sensor.xbox_360_<host>_motherboard` | sensor | Motherboard revision, e.g. `Jasper` (diagnostic) |
| `sensor.xbox_360_<host>_console_type` | sensor | Console type: `Retail` or `Devkit` (diagnostic) |
| `sensor.xbox_360_<host>_dashboard_version` | sensor | Aurora dashboard version, e.g. `2.0.17559.0` (diagnostic) |
| `sensor.xbox_360_<host>_serial_number` | sensor | Console serial number (diagnostic; disabled by default) |
| `sensor.xbox_360_<host>_console_id` | sensor | Console ID (diagnostic; disabled by default) |
| `sensor.xbox_360_<host>_gamertag` | sensor | Signed-in gamertag (primary profile) |
| `sensor.xbox_360_<host>_gamerscore` | sensor | Gamerscore (primary profile) |
| `sensor.xbox_360_<host>_signed_in_profiles` | sensor | Number of signed-in profiles |
| `sensor.xbox_360_<host>_network_download` | sensor | LiNK download rate (B/s) |
| `sensor.xbox_360_<host>_network_upload` | sensor | LiNK upload rate (B/s) |
| `sensor.xbox_360_<host>_network_total_download` | sensor | LiNK total bytes downloaded (diagnostic) |
| `sensor.xbox_360_<host>_network_total_upload` | sensor | LiNK total bytes uploaded (diagnostic) |
| `binary_sensor.xbox_360_<host>_online` | binary_sensor | `on` while NOVA responds (connectivity) |
| `switch.xbox_360_<host>_game_paused` | switch | Pause/resume the running game (optimistic; NOVA `/thread/state`) |
| `button.xbox_360_<host>_reboot` | button | Power-cycle the console (FTP `SITE REBOOT`) |
| `button.xbox_360_<host>_shutdown` | button | Power off the console (FTP `SITE SHUTDOWN`) |
| `button.xbox_360_<host>_restart_aurora` | button | Restart the Aurora dashboard (FTP `SITE RESTART`) |

When the console is off or unreachable, the sensors become `unavailable` and the
`online` binary sensor reports `off`.

> **Note on secrets:** `cpukey` and `dvdkey` are cryptographic secrets and are
> **never** exposed as entities. They are also redacted (`**REDACTED**`) in the
> Home Assistant diagnostics download.

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

This project uses [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest -v
```

## Credits

- [Aurora](https://consolemods.org/wiki/Xbox_360:Aurora) and the NOVA plugin by the
  Aurora team.
- NOVA API reference:
  [jrobiche/xbox360-aurora-developer-documentation](https://github.com/jrobiche/xbox360-aurora-developer-documentation).
- Title ID → name database derived from
  [wiredopposite/Xbox360-Game-Database](https://github.com/wiredopposite/Xbox360-Game-Database).

## License

[MIT](LICENSE) © Hudson Brendon

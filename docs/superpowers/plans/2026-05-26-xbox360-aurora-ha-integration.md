# Xbox 360 (Aurora/NOVA) Home Assistant Integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Home Assistant custom integration (`xbox360_aurora`) that monitors and controls a jailbroken (RGH/JTAG) Xbox 360 running the Aurora dashboard with the NOVA plugin.

**Architecture:** A `local_polling` custom component. Monitoring + game launch go through the NOVA REST API (port 9999, JWT auth). Reboot/shutdown go through Aurora's FTP server (port 21) using `SITE` commands, since NOVA has no power endpoints. A `DataUpdateCoordinator` polls NOVA every 30s; entities derive from its data. Power-ON is out of scope (RGH consoles have no Wake-on-LAN).

**Tech Stack:** Python 3.12+, Home Assistant (`config_flow`, `DataUpdateCoordinator`, `CoordinatorEntity`), `aiohttp` (NOVA), `ftplib` in executor (FTP). Tests: `pytest` + `pytest-homeassistant-custom-component` + `aioresponses`.

---

## Background: what the hardware exposes

Verified against the Aurora/NOVA developer documentation (`jrobiche/xbox360-aurora-developer-documentation`, NOVA `0.7b.2 r1622`) and ConsoleMods/Aurora FTP docs.

**NOVA REST API** — base `http://<console_ip>:9999`:
- `POST /authenticate` — `multipart/form-data` with `username` + `password` (defaults `xboxhttp`/`xboxhttp`). Returns JSON `{"token": "<jwt>"}`. Use `Authorization: Bearer <jwt>` on every other request. 401 = bad creds / expired token.
- `GET /title` → JSON: `titleid` (hex string), `mediaid` (hex string), `path` (string), `tuver` (number), `disc` `{count, current}`, `resolution` `{width, height}`, `version` `{base, current}`.
- `GET /temperature` → JSON: `cpu`, `gpu`, `case`, `memory` (numbers), `celsius` (bool — true ⇒ values are °C).
- `GET /memory` → JSON: `free`, `used`, `total` (numbers, bytes).
- `POST /title/launch` — `multipart/form-data`: `exec` (e.g. `default.xex`), `path` (e.g. `Hdd1:\Games\MyGame`), `type` (int: `-1` none, `0` xex, `1` xbe, `2` xex container, `3` xbe container, `4` XNA). Success = HTTP 202.

**Aurora FTP** — `<console_ip>:21`, defaults `xboxftp`/`xboxftp`. Custom `SITE` commands include `REBOOT` (power-cycle), `SHUTDOWN` (power off), `RESTART` (restart Aurora only). We use `SITE REBOOT` and `SITE SHUTDOWN`.

---

## File Structure

```
ha-xbox360-aurora/
├── custom_components/
│   └── xbox360_aurora/
│       ├── __init__.py          # setup/unload entry, coordinator wiring, launch_title service
│       ├── manifest.json        # integration metadata
│       ├── const.py             # DOMAIN, defaults, config keys, service/attr names
│       ├── nova.py              # NOVA REST client (auth + GET endpoints + launch) — no HA imports
│       ├── ftp.py               # FTP SITE command helper (reboot/shutdown) — no HA imports
│       ├── coordinator.py       # DataUpdateCoordinator polling NOVA
│       ├── config_flow.py       # UI setup (host/ports/creds), validates via NOVA auth
│       ├── entity.py            # shared CoordinatorEntity base with DeviceInfo
│       ├── sensor.py            # current title, CPU/GPU/case temps, free RAM
│       ├── binary_sensor.py     # connectivity (online/offline)
│       ├── button.py            # reboot, shutdown
│       ├── services.yaml        # launch_title service schema (UI)
│       ├── strings.json         # config-flow strings
│       └── translations/
│           └── en.json          # English translations (mirror of strings.json)
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_nova.py
│   ├── test_ftp.py
│   ├── test_config_flow.py
│   ├── test_init.py
│   ├── test_sensor.py
│   ├── test_binary_sensor.py
│   └── test_button.py
├── hacs.json
├── pytest.ini
├── requirements-test.txt
└── README.md
```

**Responsibility boundaries:** `nova.py` and `ftp.py` are pure transport clients with **no Home Assistant imports** — fully unit-testable in isolation. Everything HA-aware (coordinator, entities, flow) depends on those clients but not vice versa.

---

### Task 1: Project scaffold, manifest, constants, test harness

**Files:**
- Create: `custom_components/xbox360_aurora/__init__.py` (empty placeholder for now)
- Create: `custom_components/xbox360_aurora/manifest.json`
- Create: `custom_components/xbox360_aurora/const.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `pytest.ini`
- Create: `requirements-test.txt`
- Create: `hacs.json`
- Test: `tests/test_const.py`

- [ ] **Step 1: Initialize the repo**

Run from `/Users/hudsonbrendon/Github/ha-xbox360-aurora`:

```bash
cd /Users/hudsonbrendon/Github/ha-xbox360-aurora
git init
printf '__pycache__/\n*.pyc\n.venv/\n.pytest_cache/\n*.egg-info/\n' > .gitignore
```

- [ ] **Step 2: Create the test requirements file**

`requirements-test.txt`:

```
homeassistant
pytest
pytest-asyncio
pytest-homeassistant-custom-component
aioresponses
```

- [ ] **Step 3: Create the pytest config**

`pytest.ini`:

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 4: Set up the virtualenv and install deps**

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements-test.txt
```

Expected: installs complete without error. `pytest-homeassistant-custom-component` pulls in a matching `homeassistant`.

- [ ] **Step 5: Create `const.py`**

`custom_components/xbox360_aurora/const.py`:

```python
"""Constants for the Xbox 360 Aurora integration."""
from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "xbox360_aurora"

# Config entry keys (host/username/password reuse homeassistant.const CONF_* keys)
CONF_FTP_PORT = "ftp_port"
CONF_FTP_USERNAME = "ftp_username"
CONF_FTP_PASSWORD = "ftp_password"

# Defaults
DEFAULT_NOVA_PORT = 9999
DEFAULT_NOVA_USERNAME = "xboxhttp"
DEFAULT_NOVA_PASSWORD = "xboxhttp"
DEFAULT_FTP_PORT = 21
DEFAULT_FTP_USERNAME = "xboxftp"
DEFAULT_FTP_PASSWORD = "xboxftp"

DEFAULT_SCAN_INTERVAL = 30

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR]

# launch_title service
SERVICE_LAUNCH_TITLE = "launch_title"
ATTR_EXEC = "exec"
ATTR_PATH = "path"
ATTR_TYPE = "type"

# FTP SITE commands
FTP_CMD_REBOOT = "REBOOT"
FTP_CMD_SHUTDOWN = "SHUTDOWN"
```

- [ ] **Step 6: Create `manifest.json`**

`custom_components/xbox360_aurora/manifest.json`:

```json
{
  "domain": "xbox360_aurora",
  "name": "Xbox 360 Aurora",
  "version": "0.1.0",
  "config_flow": true,
  "documentation": "https://github.com/hudsonbrendon/ha-xbox360-aurora",
  "issue_tracker": "https://github.com/hudsonbrendon/ha-xbox360-aurora/issues",
  "codeowners": ["@hudsonbrendon"],
  "iot_class": "local_polling",
  "integration_type": "device",
  "requirements": []
}
```

- [ ] **Step 7: Create empty `__init__.py` placeholder**

`custom_components/xbox360_aurora/__init__.py`:

```python
"""The Xbox 360 Aurora integration."""
```

- [ ] **Step 8: Create `hacs.json`**

`hacs.json`:

```json
{
  "name": "Xbox 360 Aurora",
  "render_readme": true,
  "homeassistant": "2024.1.0"
}
```

- [ ] **Step 9: Create the test harness files**

`tests/__init__.py`:

```python
"""Tests for the Xbox 360 Aurora integration."""
```

`tests/conftest.py`:

```python
"""Fixtures for Xbox 360 Aurora tests."""
import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of custom integrations in all tests."""
    yield
```

- [ ] **Step 10: Write a failing test that const imports cleanly**

`tests/test_const.py`:

```python
"""Sanity tests for constants."""
from custom_components.xbox360_aurora.const import (
    DOMAIN,
    PLATFORMS,
    DEFAULT_NOVA_PORT,
    DEFAULT_FTP_PORT,
)


def test_domain_value():
    assert DOMAIN == "xbox360_aurora"


def test_default_ports():
    assert DEFAULT_NOVA_PORT == 9999
    assert DEFAULT_FTP_PORT == 21


def test_platforms_registered():
    assert len(PLATFORMS) == 3
```

- [ ] **Step 11: Run the test — expect PASS**

Run: `.venv/bin/pytest tests/test_const.py -v`
Expected: 3 passed. (If `enable_custom_integrations` is missing, the plugin isn't installed — re-check Step 4.)

- [ ] **Step 12: Commit**

```bash
git add -A
git commit -m "chore: scaffold xbox360_aurora integration and test harness"
```

---

### Task 2: NOVA client — authentication

**Files:**
- Create: `custom_components/xbox360_aurora/nova.py`
- Test: `tests/test_nova.py`

- [ ] **Step 1: Write the failing test**

`tests/test_nova.py`:

```python
"""Tests for the NOVA REST client."""
import aiohttp
import pytest
from aioresponses import aioresponses

from custom_components.xbox360_aurora.nova import (
    NovaClient,
    NovaAuthError,
    NovaConnectionError,
)

BASE = "http://1.2.3.4:9999"


async def test_authenticate_returns_and_stores_token():
    async with aiohttp.ClientSession() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "xboxhttp", "xboxhttp")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "abc123"})
            token = await client.authenticate()
        assert token == "abc123"
        assert client.token == "abc123"


async def test_authenticate_bad_credentials_raises_auth_error():
    async with aiohttp.ClientSession() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "x", "y")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", status=401)
            with pytest.raises(NovaAuthError):
                await client.authenticate()


async def test_authenticate_connection_failure_raises_connection_error():
    async with aiohttp.ClientSession() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "x", "y")
        with aioresponses() as mock:
            mock.post(
                f"{BASE}/authenticate",
                exception=aiohttp.ClientConnectionError("boom"),
            )
            with pytest.raises(NovaConnectionError):
                await client.authenticate()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_nova.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'custom_components.xbox360_aurora.nova'`

- [ ] **Step 3: Write minimal implementation**

`custom_components/xbox360_aurora/nova.py`:

```python
"""Async client for the Aurora NOVA REST API (no Home Assistant imports)."""
from __future__ import annotations

import aiohttp


class NovaError(Exception):
    """Base error for NOVA client failures."""


class NovaAuthError(NovaError):
    """Authentication with NOVA failed (bad credentials or expired token)."""


class NovaConnectionError(NovaError):
    """Could not reach the NOVA server."""


class NovaClient:
    """Talks to the Aurora NOVA plugin REST API on port 9999."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        username: str,
        password: str,
    ) -> None:
        self._session = session
        self._base = f"http://{host}:{port}"
        self._username = username
        self._password = password
        self._token: str | None = None

    @property
    def token(self) -> str | None:
        """Return the current JWT, if authenticated."""
        return self._token

    async def authenticate(self) -> str:
        """Request a fresh JWT and store it. Returns the token."""
        data = aiohttp.FormData()
        data.add_field("username", self._username)
        data.add_field("password", self._password)
        try:
            async with self._session.post(
                f"{self._base}/authenticate", data=data
            ) as resp:
                if resp.status == 401:
                    raise NovaAuthError("Invalid NOVA credentials")
                resp.raise_for_status()
                payload = await resp.json()
        except aiohttp.ClientResponseError as err:
            raise NovaConnectionError(str(err)) from err
        except aiohttp.ClientError as err:
            raise NovaConnectionError(str(err)) from err

        token = payload.get("token")
        if not token:
            raise NovaAuthError("No token in authentication response")
        self._token = token
        return token
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_nova.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add custom_components/xbox360_aurora/nova.py tests/test_nova.py
git commit -m "feat(nova): add NOVA client authentication"
```

---

### Task 3: NOVA client — authenticated GET requests with 401 re-auth

**Files:**
- Modify: `custom_components/xbox360_aurora/nova.py`
- Test: `tests/test_nova.py`

- [ ] **Step 1: Write the failing tests (append to `tests/test_nova.py`)**

```python
async def test_get_title_sends_bearer_and_returns_json():
    async with aiohttp.ClientSession() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.get(f"{BASE}/title", payload={"titleid": "DEADBEEF"})
            result = await client.get_title()
        assert result == {"titleid": "DEADBEEF"}


async def test_request_reauths_once_on_401():
    async with aiohttp.ClientSession() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            # initial auth, then a stale-token 401, then re-auth, then success
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.get(f"{BASE}/title", status=401)
            mock.post(f"{BASE}/authenticate", payload={"token": "t2"})
            mock.get(f"{BASE}/title", payload={"titleid": "CAFE"})
            result = await client.get_title()
        assert result == {"titleid": "CAFE"}
        assert client.token == "t2"


async def test_request_raises_auth_error_when_401_persists():
    async with aiohttp.ClientSession() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.get(f"{BASE}/title", status=401)
            mock.post(f"{BASE}/authenticate", payload={"token": "t2"})
            mock.get(f"{BASE}/title", status=401)
            with pytest.raises(NovaAuthError):
                await client.get_title()


async def test_get_temperature_and_memory():
    async with aiohttp.ClientSession() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.get(
                f"{BASE}/temperature",
                payload={"cpu": 50, "gpu": 55, "case": 40, "memory": 45, "celsius": True},
            )
            temp = await client.get_temperature()
            mock.get(f"{BASE}/memory", payload={"free": 100, "used": 200, "total": 300})
            mem = await client.get_memory()
        assert temp["cpu"] == 50
        assert mem["total"] == 300
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_nova.py -k "get_title or reauth or 401 or temperature" -v`
Expected: FAIL — `AttributeError: 'NovaClient' object has no attribute 'get_title'`

- [ ] **Step 3: Add the request helper and GET methods to `nova.py`**

Append these methods to the `NovaClient` class (after `authenticate`):

```python
    async def _request(self, method: str, path: str, **kwargs) -> dict | None:
        """Make an authenticated request, re-authenticating once on a 401.

        Returns parsed JSON for JSON responses, otherwise None.
        """
        if self._token is None:
            await self.authenticate()

        url = f"{self._base}{path}"
        extra = {k: v for k, v in kwargs.items() if k != "headers"}

        for attempt in range(2):
            headers = dict(kwargs.get("headers") or {})
            headers["Authorization"] = f"Bearer {self._token}"
            try:
                async with self._session.request(
                    method, url, headers=headers, **extra
                ) as resp:
                    if resp.status == 401:
                        if attempt == 0:
                            await self.authenticate()
                            continue
                        raise NovaAuthError("Authentication failed after retry")
                    resp.raise_for_status()
                    if resp.content_type == "application/json":
                        return await resp.json()
                    return None
            except aiohttp.ClientResponseError as err:
                raise NovaConnectionError(str(err)) from err
            except aiohttp.ClientError as err:
                raise NovaConnectionError(str(err)) from err
        return None

    async def get_title(self) -> dict | None:
        """Get information about the running title."""
        return await self._request("GET", "/title")

    async def get_temperature(self) -> dict | None:
        """Get console component temperatures."""
        return await self._request("GET", "/temperature")

    async def get_memory(self) -> dict | None:
        """Get free/used/total RAM in bytes."""
        return await self._request("GET", "/memory")

    async def get_system(self) -> dict | None:
        """Get general console information."""
        return await self._request("GET", "/system")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_nova.py -v`
Expected: all passed (7 tests total in this file so far).

- [ ] **Step 5: Commit**

```bash
git add custom_components/xbox360_aurora/nova.py tests/test_nova.py
git commit -m "feat(nova): add authenticated GET endpoints with 401 re-auth"
```

---

### Task 4: NOVA client — launch_title

**Files:**
- Modify: `custom_components/xbox360_aurora/nova.py`
- Test: `tests/test_nova.py`

- [ ] **Step 1: Write the failing test (append to `tests/test_nova.py`)**

```python
async def test_launch_title_posts_multipart_fields():
    async with aiohttp.ClientSession() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.post(f"{BASE}/title/launch", status=202)
            # Should not raise on a 202 with no JSON body.
            await client.launch_title("default.xex", r"Hdd1:\Games\MyGame", 0)
        # Confirm the launch endpoint was actually called.
        requests = mock.requests
        assert ("POST", aiohttp.client.URL(f"{BASE}/title/launch")) in requests
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_nova.py -k launch -v`
Expected: FAIL — `AttributeError: 'NovaClient' object has no attribute 'launch_title'`

- [ ] **Step 3: Add `launch_title` to `nova.py`**

Append to the `NovaClient` class:

```python
    async def launch_title(self, executable: str, path: str, title_type: int) -> None:
        """Launch an executable on the console.

        executable: filename, e.g. "default.xex".
        path: Aurora drive path, e.g. r"Hdd1:\\Games\\MyGame".
        title_type: -1 none, 0 xex, 1 xbe, 2 xex container, 3 xbe container, 4 XNA.
        """
        data = aiohttp.FormData()
        data.add_field("exec", executable)
        data.add_field("path", path)
        data.add_field("type", str(title_type))
        await self._request("POST", "/title/launch", data=data)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_nova.py -v`
Expected: all passed.

- [ ] **Step 5: Commit**

```bash
git add custom_components/xbox360_aurora/nova.py tests/test_nova.py
git commit -m "feat(nova): add launch_title"
```

---

### Task 5: FTP client — SITE commands (reboot/shutdown)

**Files:**
- Create: `custom_components/xbox360_aurora/ftp.py`
- Test: `tests/test_ftp.py`

- [ ] **Step 1: Write the failing test**

`tests/test_ftp.py`:

```python
"""Tests for the FTP SITE command helper."""
import ftplib
from unittest.mock import MagicMock, patch

import pytest

from custom_components.xbox360_aurora.ftp import site_command, FtpError


def test_site_command_logs_in_and_sends_site_prefix():
    fake_ftp = MagicMock()
    fake_ftp.sendcmd.return_value = "200 Rebooting"
    with patch("custom_components.xbox360_aurora.ftp.ftplib.FTP") as ftp_cls:
        ftp_cls.return_value.__enter__.return_value = fake_ftp
        result = site_command("1.2.3.4", 21, "xboxftp", "xboxftp", "REBOOT")

    fake_ftp.connect.assert_called_once_with("1.2.3.4", 21)
    fake_ftp.login.assert_called_once_with("xboxftp", "xboxftp")
    fake_ftp.sendcmd.assert_called_once_with("SITE REBOOT")
    assert result == "200 Rebooting"


def test_site_command_wraps_ftp_errors():
    with patch("custom_components.xbox360_aurora.ftp.ftplib.FTP") as ftp_cls:
        ftp_cls.return_value.__enter__.side_effect = OSError("connection refused")
        with pytest.raises(FtpError):
            site_command("1.2.3.4", 21, "xboxftp", "xboxftp", "SHUTDOWN")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_ftp.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'custom_components.xbox360_aurora.ftp'`

- [ ] **Step 3: Write minimal implementation**

`custom_components/xbox360_aurora/ftp.py`:

```python
"""Blocking FTP helper for Aurora SITE commands (no Home Assistant imports).

Run via hass.async_add_executor_job — ftplib is synchronous.
"""
from __future__ import annotations

import ftplib


class FtpError(Exception):
    """Raised when an FTP SITE command fails."""


def site_command(
    host: str,
    port: int,
    username: str,
    password: str,
    command: str,
    timeout: float = 10.0,
) -> str:
    """Connect to the Aurora FTP server and run `SITE <command>`.

    Returns the server's response line. Raises FtpError on any failure.
    """
    try:
        with ftplib.FTP(timeout=timeout) as ftp:
            ftp.connect(host, port)
            ftp.login(username, password)
            return ftp.sendcmd(f"SITE {command}")
    except ftplib.all_errors as err:  # includes OSError, EOFError, ftplib.Error
        raise FtpError(str(err)) from err
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_ftp.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add custom_components/xbox360_aurora/ftp.py tests/test_ftp.py
git commit -m "feat(ftp): add SITE command helper for reboot/shutdown"
```

---

### Task 6: DataUpdateCoordinator

**Files:**
- Create: `custom_components/xbox360_aurora/coordinator.py`
- Test: covered indirectly by `tests/test_init.py` (Task 8). No standalone test here — the coordinator is a thin wrapper and is exercised through entry setup.

- [ ] **Step 1: Write the coordinator**

`custom_components/xbox360_aurora/coordinator.py`:

```python
"""Coordinator that polls the NOVA API and shares data with entities."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .nova import NovaClient, NovaError

_LOGGER = logging.getLogger(__name__)


class XboxAuroraCoordinator(DataUpdateCoordinator[dict]):
    """Polls NOVA for title, temperature, and memory."""

    def __init__(self, hass: HomeAssistant, client: NovaClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        """Fetch the latest data. UpdateFailed marks entities unavailable (offline)."""
        try:
            title = await self.client.get_title()
            temperature = await self.client.get_temperature()
            memory = await self.client.get_memory()
        except NovaError as err:
            raise UpdateFailed(f"Error communicating with NOVA: {err}") from err
        return {
            "title": title or {},
            "temperature": temperature or {},
            "memory": memory or {},
        }
```

- [ ] **Step 2: Verify it imports**

Run: `.venv/bin/python -c "from custom_components.xbox360_aurora.coordinator import XboxAuroraCoordinator; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add custom_components/xbox360_aurora/coordinator.py
git commit -m "feat: add NOVA data update coordinator"
```

---

### Task 7: Config flow

**Files:**
- Create: `custom_components/xbox360_aurora/config_flow.py`
- Create: `custom_components/xbox360_aurora/strings.json`
- Create: `custom_components/xbox360_aurora/translations/en.json`
- Test: `tests/test_config_flow.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_config_flow.py`:

```python
"""Tests for the config flow."""
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant

from custom_components.xbox360_aurora.const import (
    CONF_FTP_PASSWORD,
    CONF_FTP_PORT,
    CONF_FTP_USERNAME,
    DOMAIN,
)
from custom_components.xbox360_aurora.nova import NovaAuthError, NovaConnectionError

USER_INPUT = {
    CONF_HOST: "1.2.3.4",
    CONF_PORT: 9999,
    CONF_USERNAME: "xboxhttp",
    CONF_PASSWORD: "xboxhttp",
    CONF_FTP_PORT: 21,
    CONF_FTP_USERNAME: "xboxftp",
    CONF_FTP_PASSWORD: "xboxftp",
}


async def test_user_flow_success(hass: HomeAssistant):
    with patch(
        "custom_components.xbox360_aurora.config_flow.NovaClient.authenticate",
        new=AsyncMock(return_value="tok"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Xbox 360 (1.2.3.4)"
    assert result2["data"] == USER_INPUT


async def test_user_flow_invalid_auth(hass: HomeAssistant):
    with patch(
        "custom_components.xbox360_aurora.config_flow.NovaClient.authenticate",
        new=AsyncMock(side_effect=NovaAuthError),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_user_flow_cannot_connect(hass: HomeAssistant):
    with patch(
        "custom_components.xbox360_aurora.config_flow.NovaClient.authenticate",
        new=AsyncMock(side_effect=NovaConnectionError),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_config_flow.py -v`
Expected: FAIL — flow handler for `xbox360_aurora` not found (no `config_flow.py`).

- [ ] **Step 3: Write `config_flow.py`**

`custom_components/xbox360_aurora/config_flow.py`:

```python
"""Config flow for Xbox 360 Aurora."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_FTP_PASSWORD,
    CONF_FTP_PORT,
    CONF_FTP_USERNAME,
    DEFAULT_FTP_PASSWORD,
    DEFAULT_FTP_PORT,
    DEFAULT_FTP_USERNAME,
    DEFAULT_NOVA_PASSWORD,
    DEFAULT_NOVA_PORT,
    DEFAULT_NOVA_USERNAME,
    DOMAIN,
)
from .nova import NovaAuthError, NovaClient, NovaError

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_NOVA_PORT): int,
        vol.Required(CONF_USERNAME, default=DEFAULT_NOVA_USERNAME): str,
        vol.Required(CONF_PASSWORD, default=DEFAULT_NOVA_PASSWORD): str,
        vol.Required(CONF_FTP_PORT, default=DEFAULT_FTP_PORT): int,
        vol.Required(CONF_FTP_USERNAME, default=DEFAULT_FTP_USERNAME): str,
        vol.Required(CONF_FTP_PASSWORD, default=DEFAULT_FTP_PASSWORD): str,
    }
)


class XboxAuroraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the UI configuration flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = NovaClient(
                session,
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            try:
                await client.authenticate()
            except NovaAuthError:
                errors["base"] = "invalid_auth"
            except NovaError:
                errors["base"] = "cannot_connect"
            else:
                unique_id = f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Xbox 360 ({user_input[CONF_HOST]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )
```

- [ ] **Step 4: Write `strings.json`**

`custom_components/xbox360_aurora/strings.json`:

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Xbox 360 Aurora",
        "description": "Enter your Xbox 360's network address and the Aurora NOVA + FTP credentials.",
        "data": {
          "host": "Host (IP address)",
          "port": "NOVA port",
          "username": "NOVA username",
          "password": "NOVA password",
          "ftp_port": "FTP port",
          "ftp_username": "FTP username",
          "ftp_password": "FTP password"
        }
      }
    },
    "error": {
      "invalid_auth": "Invalid NOVA username or password.",
      "cannot_connect": "Failed to connect. Check the IP, port, and that Aurora/NOVA is running."
    },
    "abort": {
      "already_configured": "This Xbox 360 is already configured."
    }
  }
}
```

- [ ] **Step 5: Write `translations/en.json` (mirror of strings.json)**

`custom_components/xbox360_aurora/translations/en.json`: copy the exact contents of `strings.json` from Step 4 into this file.

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_config_flow.py -v`
Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
git add custom_components/xbox360_aurora/config_flow.py custom_components/xbox360_aurora/strings.json custom_components/xbox360_aurora/translations/en.json tests/test_config_flow.py
git commit -m "feat: add config flow with NOVA auth validation"
```

---

### Task 8: Entry setup/unload, shared entity base, and launch_title service

**Files:**
- Modify: `custom_components/xbox360_aurora/__init__.py`
- Create: `custom_components/xbox360_aurora/entity.py`
- Create: `custom_components/xbox360_aurora/services.yaml`
- Test: `tests/test_init.py`

- [ ] **Step 1: Write the failing test**

`tests/test_init.py`:

```python
"""Tests for integration setup, unload, and the launch_title service."""
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.xbox360_aurora.const import (
    ATTR_EXEC,
    ATTR_PATH,
    ATTR_TYPE,
    CONF_FTP_PASSWORD,
    CONF_FTP_PORT,
    CONF_FTP_USERNAME,
    DOMAIN,
    SERVICE_LAUNCH_TITLE,
)

ENTRY_DATA = {
    CONF_HOST: "1.2.3.4",
    CONF_PORT: 9999,
    CONF_USERNAME: "xboxhttp",
    CONF_PASSWORD: "xboxhttp",
    CONF_FTP_PORT: 21,
    CONF_FTP_USERNAME: "xboxftp",
    CONF_FTP_PASSWORD: "xboxftp",
}

TEMP_PAYLOAD = {"cpu": 50, "gpu": 55, "case": 40, "memory": 45, "celsius": True}
MEM_PAYLOAD = {"free": 104857600, "used": 200, "total": 300}
TITLE_PAYLOAD = {"titleid": "DEADBEEF", "path": r"Hdd1:\Games\X"}


def _patches():
    return (
        patch(
            "custom_components.xbox360_aurora.NovaClient.authenticate",
            new=AsyncMock(return_value="tok"),
        ),
        patch(
            "custom_components.xbox360_aurora.coordinator.NovaClient.get_title",
            new=AsyncMock(return_value=TITLE_PAYLOAD),
        ),
        patch(
            "custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature",
            new=AsyncMock(return_value=TEMP_PAYLOAD),
        ),
        patch(
            "custom_components.xbox360_aurora.coordinator.NovaClient.get_memory",
            new=AsyncMock(return_value=MEM_PAYLOAD),
        ),
    )


async def _setup_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA, unique_id="1.2.3.4:9999")
    entry.add_to_hass(hass)
    p1, p2, p3, p4 = _patches()
    with p1, p2, p3, p4:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def test_setup_and_unload_entry(hass: HomeAssistant):
    entry = await _setup_entry(hass)
    assert entry.state is ConfigEntryState.LOADED
    assert entry.entry_id in hass.data[DOMAIN]

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert entry.entry_id not in hass.data[DOMAIN]


async def test_launch_title_service_calls_nova(hass: HomeAssistant):
    await _setup_entry(hass)
    assert hass.services.has_service(DOMAIN, SERVICE_LAUNCH_TITLE)

    with patch(
        "custom_components.xbox360_aurora.NovaClient.launch_title",
        new=AsyncMock(),
    ) as mock_launch:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_LAUNCH_TITLE,
            {ATTR_EXEC: "default.xex", ATTR_PATH: r"Hdd1:\Games\X", ATTR_TYPE: 0},
            blocking=True,
        )
    mock_launch.assert_awaited_once_with("default.xex", r"Hdd1:\Games\X", 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_init.py -v`
Expected: FAIL — `async_setup_entry` not implemented (entry won't load).

- [ ] **Step 3: Write `entity.py` (shared base)**

`custom_components/xbox360_aurora/entity.py`:

```python
"""Shared entity base for Xbox 360 Aurora."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_info import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XboxAuroraCoordinator


class XboxAuroraEntity(CoordinatorEntity[XboxAuroraCoordinator]):
    """Base entity with shared DeviceInfo."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: XboxAuroraCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Microsoft",
            model="Xbox 360 (Aurora / NOVA)",
        )
```

- [ ] **Step 4: Write `__init__.py`**

`custom_components/xbox360_aurora/__init__.py`:

```python
"""The Xbox 360 Aurora integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    ATTR_EXEC,
    ATTR_PATH,
    ATTR_TYPE,
    DOMAIN,
    PLATFORMS,
    SERVICE_LAUNCH_TITLE,
)
from .coordinator import XboxAuroraCoordinator
from .nova import NovaClient

LAUNCH_TITLE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_EXEC): cv.string,
        vol.Required(ATTR_PATH): cv.string,
        vol.Optional(ATTR_TYPE, default=0): vol.All(
            vol.Coerce(int), vol.Range(min=-1, max=4)
        ),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Xbox 360 Aurora from a config entry."""
    session = async_get_clientsession(hass)
    client = NovaClient(
        session,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    coordinator = XboxAuroraCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_LAUNCH_TITLE)
    return unload_ok


def _async_register_services(hass: HomeAssistant) -> None:
    """Register the launch_title service once."""
    if hass.services.has_service(DOMAIN, SERVICE_LAUNCH_TITLE):
        return

    async def _handle_launch_title(call: ServiceCall) -> None:
        """Launch a title on every configured console."""
        for coordinator in hass.data[DOMAIN].values():
            await coordinator.client.launch_title(
                call.data[ATTR_EXEC],
                call.data[ATTR_PATH],
                call.data[ATTR_TYPE],
            )

    hass.services.async_register(
        DOMAIN, SERVICE_LAUNCH_TITLE, _handle_launch_title, schema=LAUNCH_TITLE_SCHEMA
    )
```

- [ ] **Step 5: Write `services.yaml`**

`custom_components/xbox360_aurora/services.yaml`:

```yaml
launch_title:
  name: Launch title
  description: Launch an executable on the Xbox 360 via Aurora NOVA.
  fields:
    exec:
      name: Executable
      description: Executable filename.
      required: true
      example: default.xex
      selector:
        text:
    path:
      name: Path
      description: Aurora drive path to the executable's folder.
      required: true
      example: 'Hdd1:\Games\MyGame'
      selector:
        text:
    type:
      name: Type
      description: "-1 none, 0 xex, 1 xbe, 2 xex container, 3 xbe container, 4 XNA."
      required: false
      default: 0
      selector:
        number:
          min: -1
          max: 4
          mode: box
```

- [ ] **Step 6: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_init.py -v`
Expected: 2 passed. (Platforms `sensor`/`binary_sensor`/`button` modules don't exist yet — HA logs a warning per missing platform but entry setup still succeeds. The next tasks add them.)

> If `async_forward_entry_setups` raises because a platform module is missing, comment out `PLATFORMS` entries you haven't built yet, or implement Tasks 9–11 before re-running. Recommended: proceed to Tasks 9–11, then re-run this test.

- [ ] **Step 7: Commit**

```bash
git add custom_components/xbox360_aurora/__init__.py custom_components/xbox360_aurora/entity.py custom_components/xbox360_aurora/services.yaml tests/test_init.py
git commit -m "feat: add entry setup/unload, entity base, launch_title service"
```

---

### Task 9: Sensor platform

**Files:**
- Create: `custom_components/xbox360_aurora/sensor.py`
- Test: `tests/test_sensor.py`

> Temperature unit assumption: NOVA reports `celsius: true` on standard Aurora builds, so temperature sensors use °C. This is a documented limitation; Fahrenheit consoles are not auto-converted in v0.1.0.

- [ ] **Step 1: Write the failing test**

`tests/test_sensor.py`:

```python
"""Tests for sensor entities."""
from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.xbox360_aurora.const import (
    CONF_FTP_PASSWORD,
    CONF_FTP_PORT,
    CONF_FTP_USERNAME,
    DOMAIN,
)

ENTRY_DATA = {
    CONF_HOST: "1.2.3.4",
    CONF_PORT: 9999,
    CONF_USERNAME: "xboxhttp",
    CONF_PASSWORD: "xboxhttp",
    CONF_FTP_PORT: 21,
    CONF_FTP_USERNAME: "xboxftp",
    CONF_FTP_PASSWORD: "xboxftp",
}


async def test_sensors_expose_nova_values(hass: HomeAssistant):
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA, unique_id="1.2.3.4:9999")
    entry.add_to_hass(hass)
    with patch(
        "custom_components.xbox360_aurora.NovaClient.authenticate",
        new=AsyncMock(return_value="tok"),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_title",
        new=AsyncMock(return_value={"titleid": "DEADBEEF"}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature",
        new=AsyncMock(
            return_value={"cpu": 50, "gpu": 55, "case": 40, "memory": 45, "celsius": True}
        ),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_memory",
        new=AsyncMock(return_value={"free": 104857600, "used": 200, "total": 300}),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.xbox_360_1_2_3_4_current_title").state == "DEADBEEF"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_cpu_temperature").state == "50"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_gpu_temperature").state == "55"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_free_ram").state == "100.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_sensor.py -v`
Expected: FAIL — sensor entities are `None` (no `sensor.py`).

- [ ] **Step 3: Write `sensor.py`**

`custom_components/xbox360_aurora/sensor.py`:

```python
"""Sensor platform for Xbox 360 Aurora."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfInformation, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .coordinator import XboxAuroraCoordinator
from .entity import XboxAuroraEntity


@dataclass(frozen=True, kw_only=True)
class XboxSensorDescription(SensorEntityDescription):
    """Sensor description with a value extractor."""

    value_fn: Callable[[dict], StateType]


def _free_mb(data: dict) -> StateType:
    free = (data.get("memory") or {}).get("free")
    if free is None:
        return None
    return round(free / 1048576, 1)


SENSORS: tuple[XboxSensorDescription, ...] = (
    XboxSensorDescription(
        key="current_title",
        translation_key="current_title",
        icon="mdi:gamepad-variant",
        value_fn=lambda data: (data.get("title") or {}).get("titleid"),
    ),
    XboxSensorDescription(
        key="cpu_temperature",
        translation_key="cpu_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (data.get("temperature") or {}).get("cpu"),
    ),
    XboxSensorDescription(
        key="gpu_temperature",
        translation_key="gpu_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (data.get("temperature") or {}).get("gpu"),
    ),
    XboxSensorDescription(
        key="case_temperature",
        translation_key="case_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (data.get("temperature") or {}).get("case"),
    ),
    XboxSensorDescription(
        key="free_ram",
        translation_key="free_ram",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_free_mb,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator: XboxAuroraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        XboxAuroraSensor(coordinator, entry, description) for description in SENSORS
    )


class XboxAuroraSensor(XboxAuroraEntity, SensorEntity):
    """A NOVA-backed sensor."""

    entity_description: XboxSensorDescription

    def __init__(
        self,
        coordinator: XboxAuroraCoordinator,
        entry: ConfigEntry,
        description: XboxSensorDescription,
    ) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> StateType:
        return self.entity_description.value_fn(self.coordinator.data or {})
```

- [ ] **Step 4: Add sensor names to `strings.json` and `translations/en.json`**

Add this `entity` block to **both** `custom_components/xbox360_aurora/strings.json` and `custom_components/xbox360_aurora/translations/en.json` (as a new top-level key alongside `"config"`):

```json
  "entity": {
    "sensor": {
      "current_title": { "name": "Current title" },
      "cpu_temperature": { "name": "CPU temperature" },
      "gpu_temperature": { "name": "GPU temperature" },
      "case_temperature": { "name": "Case temperature" },
      "free_ram": { "name": "Free RAM" }
    }
  }
```

(Remember the comma after the closing brace of the `"config"` block.)

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_sensor.py -v`
Expected: 1 passed.

> Note on entity_ids: `has_entity_name = True` builds slugs from device name + entity name, e.g. `sensor.xbox_360_1_2_3_4_current_title`. If your HA version slugifies the IP differently, adjust the expected entity_ids in the test to match the actual `hass.states.async_entity_ids()` output (print them once to confirm).

- [ ] **Step 6: Commit**

```bash
git add custom_components/xbox360_aurora/sensor.py custom_components/xbox360_aurora/strings.json custom_components/xbox360_aurora/translations/en.json tests/test_sensor.py
git commit -m "feat(sensor): add title, temperature, and RAM sensors"
```

---

### Task 10: Binary sensor platform (connectivity)

**Files:**
- Create: `custom_components/xbox360_aurora/binary_sensor.py`
- Test: `tests/test_binary_sensor.py`

- [ ] **Step 1: Write the failing test**

`tests/test_binary_sensor.py`:

```python
"""Tests for the connectivity binary sensor."""
from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.xbox360_aurora.const import (
    CONF_FTP_PASSWORD,
    CONF_FTP_PORT,
    CONF_FTP_USERNAME,
    DOMAIN,
)
from custom_components.xbox360_aurora.nova import NovaConnectionError

ENTRY_DATA = {
    CONF_HOST: "1.2.3.4",
    CONF_PORT: 9999,
    CONF_USERNAME: "xboxhttp",
    CONF_PASSWORD: "xboxhttp",
    CONF_FTP_PORT: 21,
    CONF_FTP_USERNAME: "xboxftp",
    CONF_FTP_PASSWORD: "xboxftp",
}


async def test_connectivity_on_when_polling_succeeds(hass: HomeAssistant):
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA, unique_id="1.2.3.4:9999")
    entry.add_to_hass(hass)
    with patch(
        "custom_components.xbox360_aurora.NovaClient.authenticate",
        new=AsyncMock(return_value="tok"),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_title",
        new=AsyncMock(return_value={"titleid": "1"}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature",
        new=AsyncMock(return_value={"cpu": 1, "gpu": 1, "case": 1, "memory": 1, "celsius": True}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_memory",
        new=AsyncMock(return_value={"free": 1, "used": 1, "total": 1}),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.xbox_360_1_2_3_4_online")
    assert state is not None
    assert state.state == "on"


async def test_connectivity_off_when_polling_fails(hass: HomeAssistant):
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA, unique_id="1.2.3.4:9999")
    entry.add_to_hass(hass)
    with patch(
        "custom_components.xbox360_aurora.NovaClient.authenticate",
        new=AsyncMock(return_value="tok"),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_title",
        new=AsyncMock(side_effect=NovaConnectionError("offline")),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature",
        new=AsyncMock(side_effect=NovaConnectionError("offline")),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_memory",
        new=AsyncMock(side_effect=NovaConnectionError("offline")),
    ):
        # First refresh fails -> entry setup raises ConfigEntryNotReady.
        # We still want the binary sensor available and "off", so we force a
        # successful setup first, then a failed refresh.
        with patch(
            "custom_components.xbox360_aurora.coordinator.NovaClient.get_title",
            new=AsyncMock(return_value={"titleid": "1"}),
        ), patch(
            "custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature",
            new=AsyncMock(return_value={"cpu": 1, "gpu": 1, "case": 1, "memory": 1, "celsius": True}),
        ), patch(
            "custom_components.xbox360_aurora.coordinator.NovaClient.get_memory",
            new=AsyncMock(return_value={"free": 1, "used": 1, "total": 1}),
        ):
            assert await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()

        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.xbox_360_1_2_3_4_online")
    assert state.state == "off"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_binary_sensor.py -v`
Expected: FAIL — binary_sensor entity is `None`.

- [ ] **Step 3: Write `binary_sensor.py`**

`custom_components/xbox360_aurora/binary_sensor.py`:

```python
"""Binary sensor platform for Xbox 360 Aurora (connectivity)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import XboxAuroraCoordinator
from .entity import XboxAuroraEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the connectivity binary sensor."""
    coordinator: XboxAuroraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([XboxAuroraOnlineSensor(coordinator, entry)])


class XboxAuroraOnlineSensor(XboxAuroraEntity, BinarySensorEntity):
    """Reports whether the console is reachable over NOVA."""

    _attr_translation_key = "online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: XboxAuroraCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_online"

    @property
    def available(self) -> bool:
        """A connectivity sensor must report even when the console is offline."""
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.last_update_success
```

- [ ] **Step 4: Add the binary_sensor name to `strings.json` and `translations/en.json`**

Inside the existing `"entity"` block in **both** files, add a `"binary_sensor"` key alongside `"sensor"`:

```json
    "binary_sensor": {
      "online": { "name": "Online" }
    }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_binary_sensor.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add custom_components/xbox360_aurora/binary_sensor.py custom_components/xbox360_aurora/strings.json custom_components/xbox360_aurora/translations/en.json tests/test_binary_sensor.py
git commit -m "feat(binary_sensor): add connectivity sensor"
```

---

### Task 11: Button platform (reboot/shutdown)

**Files:**
- Create: `custom_components/xbox360_aurora/button.py`
- Test: `tests/test_button.py`

- [ ] **Step 1: Write the failing test**

`tests/test_button.py`:

```python
"""Tests for reboot/shutdown buttons."""
from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.xbox360_aurora.const import (
    CONF_FTP_PASSWORD,
    CONF_FTP_PORT,
    CONF_FTP_USERNAME,
    DOMAIN,
)

ENTRY_DATA = {
    CONF_HOST: "1.2.3.4",
    CONF_PORT: 9999,
    CONF_USERNAME: "xboxhttp",
    CONF_PASSWORD: "xboxhttp",
    CONF_FTP_PORT: 21,
    CONF_FTP_USERNAME: "xboxftp",
    CONF_FTP_PASSWORD: "xboxftp",
}


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA, unique_id="1.2.3.4:9999")
    entry.add_to_hass(hass)
    with patch(
        "custom_components.xbox360_aurora.NovaClient.authenticate",
        new=AsyncMock(return_value="tok"),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_title",
        new=AsyncMock(return_value={"titleid": "1"}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature",
        new=AsyncMock(return_value={"cpu": 1, "gpu": 1, "case": 1, "memory": 1, "celsius": True}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_memory",
        new=AsyncMock(return_value={"free": 1, "used": 1, "total": 1}),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def test_reboot_button_sends_site_reboot(hass: HomeAssistant):
    await _setup(hass)
    with patch(
        "custom_components.xbox360_aurora.button.site_command", return_value="200 OK"
    ) as mock_site:
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.xbox_360_1_2_3_4_reboot"},
            blocking=True,
        )
    mock_site.assert_called_once_with("1.2.3.4", 21, "xboxftp", "xboxftp", "REBOOT")


async def test_shutdown_button_sends_site_shutdown(hass: HomeAssistant):
    await _setup(hass)
    with patch(
        "custom_components.xbox360_aurora.button.site_command", return_value="200 OK"
    ) as mock_site:
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.xbox_360_1_2_3_4_shutdown"},
            blocking=True,
        )
    mock_site.assert_called_once_with("1.2.3.4", 21, "xboxftp", "xboxftp", "SHUTDOWN")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_button.py -v`
Expected: FAIL — button entities are `None`.

- [ ] **Step 3: Write `button.py`**

`custom_components/xbox360_aurora/button.py`:

```python
"""Button platform for Xbox 360 Aurora (reboot/shutdown via FTP)."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_info import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_FTP_PASSWORD,
    CONF_FTP_PORT,
    CONF_FTP_USERNAME,
    DOMAIN,
    FTP_CMD_REBOOT,
    FTP_CMD_SHUTDOWN,
)
from .ftp import site_command


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up reboot and shutdown buttons."""
    async_add_entities(
        [
            XboxAuroraButton(entry, "reboot", "reboot", FTP_CMD_REBOOT),
            XboxAuroraButton(entry, "shutdown", "shutdown", FTP_CMD_SHUTDOWN),
        ]
    )


class XboxAuroraButton(ButtonEntity):
    """A button that issues an Aurora FTP SITE command."""

    _attr_has_entity_name = True

    def __init__(
        self, entry: ConfigEntry, key: str, translation_key: str, command: str
    ) -> None:
        self._entry = entry
        self._command = command
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Microsoft",
            model="Xbox 360 (Aurora / NOVA)",
        )

    async def async_press(self) -> None:
        """Run the SITE command in the executor (ftplib is blocking)."""
        data = self._entry.data
        await self.hass.async_add_executor_job(
            site_command,
            data[CONF_HOST],
            data[CONF_FTP_PORT],
            data[CONF_FTP_USERNAME],
            data[CONF_FTP_PASSWORD],
            self._command,
        )
```

- [ ] **Step 4: Add button names to `strings.json` and `translations/en.json`**

Inside the existing `"entity"` block in **both** files, add a `"button"` key:

```json
    "button": {
      "reboot": { "name": "Reboot" },
      "shutdown": { "name": "Shutdown" }
    }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_button.py -v`
Expected: 2 passed.

- [ ] **Step 6: Run the full suite**

Run: `.venv/bin/pytest -v`
Expected: every test passes (nova, ftp, config_flow, init, sensor, binary_sensor, button, const).

- [ ] **Step 7: Commit**

```bash
git add custom_components/xbox360_aurora/button.py custom_components/xbox360_aurora/strings.json custom_components/xbox360_aurora/translations/en.json tests/test_button.py
git commit -m "feat(button): add reboot and shutdown buttons via FTP SITE"
```

---

### Task 12: README and HACS polish

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`**

`README.md`:

````markdown
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
python3 -m venv .venv
.venv/bin/pip install -r requirements-test.txt
.venv/bin/pytest -v
```
````

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README"
```

---

## Self-Review

**1. Spec coverage:**
- Aurora + NOVA as the API → Tasks 2–4 (NOVA client), Task 6 (coordinator). ✅
- Monitoring (current title, online/offline, temperature, RAM) → Task 9 (sensors), Task 10 (connectivity). ✅
- Launch games/apps → Task 4 (`launch_title` client) + Task 8 (`launch_title` service). ✅
- Reboot/Shutdown → Task 5 (FTP `SITE`) + Task 11 (buttons). ✅
- Power-ON skipped → documented in README and plan header. ✅
- HA custom-component shape (config flow, manifest, HACS) → Tasks 1, 7, 12. ✅

**2. Placeholder scan:** No "TODO/TBD/handle edge cases" left. Error handling is concrete (`NovaAuthError`/`NovaConnectionError`/`FtpError`, `UpdateFailed`). All code steps show full code.

**3. Type/name consistency (checked across tasks):**
- `NovaClient(session, host, port, username, password)` — same signature in Tasks 2, 7, 8. ✅
- Methods `authenticate`, `get_title`, `get_temperature`, `get_memory`, `get_system`, `launch_title(executable, path, title_type)` — consistent in Tasks 2–4, used in 6/8/9/10/11. ✅
- `site_command(host, port, username, password, command, timeout=10.0)` — defined Task 5, called in Task 11 button (positional args match). ✅
- Const names (`DOMAIN`, `CONF_FTP_*`, `ATTR_*`, `SERVICE_LAUNCH_TITLE`, `FTP_CMD_REBOOT/SHUTDOWN`, `PLATFORMS`) — defined Task 1, used consistently throughout. ✅
- `XboxAuroraCoordinator(hass, client)` with `.client` and `.data` keys `{"title","temperature","memory"}` — defined Task 6, consumed in Tasks 9/10. ✅
- Coordinator data is always dict-with-dict (`title or {}`) so `value_fn` `.get` chains in Task 9 are safe. ✅

**Known caveats (intentional, documented):**
- Temperature assumes `celsius: true`; no Fahrenheit conversion in v0.1.0.
- `current_title` shows the raw hex title ID (no friendly-name lookup); a title-ID→name database is a future enhancement.
- `launch_title` applies to all configured consoles (typically one); per-device targeting is a future enhancement.
- Expected entity_ids in tests assume HA's default slugify of device name + IP; confirm against `hass.states.async_entity_ids()` if your HA version differs.
````

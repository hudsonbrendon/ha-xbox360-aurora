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

    async def get_smc(self) -> dict | None:
        """Get System Management Controller info (tray, AV pack, orientation)."""
        return await self._request("GET", "/smc")

    async def get_profile(self) -> list | None:
        """Get the list of signed-in profiles."""
        return await self._request("GET", "/profile")

    async def get_systemlink_bandwidth(self) -> dict | None:
        """Get LiNK network bandwidth usage."""
        return await self._request("GET", "/systemlink/bandwidth")

    async def set_thread_state(self, suspend: bool) -> None:
        """Suspend (pause) or resume the running title's main thread."""
        data = aiohttp.FormData()
        data.add_field("suspend", "1" if suspend else "0")
        await self._request("POST", "/thread/state", data=data)

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

    async def get_achievement(self) -> list | None:
        """Get the running title's achievement definitions (204 if none)."""
        return await self._request("GET", "/achievement")

    async def get_achievement_player(self) -> list | None:
        """Get per-player unlock status for the running title (204 if none)."""
        return await self._request("GET", "/achievement/player")

    async def get_profile_image(self, index: int) -> bytes | None:
        """Download a profile's gamerpic (BMP bytes) by its ProfileEntry index."""
        if self._token is None:
            await self.authenticate()
        url = f"{self._base}/image/profile"
        for attempt in range(2):
            headers = {"Authorization": f"Bearer {self._token}"}
            try:
                async with self._session.get(
                    url, params={"uuid": str(index)}, headers=headers
                ) as resp:
                    if resp.status == 401:
                        if attempt == 0:
                            await self.authenticate()
                            continue
                        raise NovaAuthError("Authentication failed after retry")
                    if resp.status == 404:
                        return None
                    resp.raise_for_status()
                    return await resp.read()
            except aiohttp.ClientResponseError as err:
                raise NovaConnectionError(str(err)) from err
            except aiohttp.ClientError as err:
                raise NovaConnectionError(str(err)) from err
        return None

    async def take_screencapture(self) -> dict | None:
        """Trigger a screen capture of the running title; returns its metadata."""
        return await self._request("GET", "/screencapture/meta")

    async def list_screencaptures(self) -> list | None:
        """List stored screen captures for the running title (204 if none)."""
        return await self._request("GET", "/screencapture/meta/list")

    async def get_update_notification(self) -> dict | None:
        """Get session activity counters (titles, profiles, screencaptures)."""
        return await self._request("GET", "/update/notification")

    async def get_plugin(self) -> dict | None:
        """Get NOVA plugin info (version, features, paths)."""
        return await self._request("GET", "/plugin")

    async def get_dashlaunch(self) -> dict | None:
        """Get DashLaunch settings and version (including kernel)."""
        return await self._request("GET", "/dashlaunch")

    async def get_screencapture_image(self, filename: str) -> bytes | None:
        """Download a stored screen capture (BMP bytes) by its filename."""
        if self._token is None:
            await self.authenticate()
        url = f"{self._base}/image/screencapture"
        for attempt in range(2):
            headers = {"Authorization": f"Bearer {self._token}"}
            try:
                async with self._session.get(
                    url, params={"uuid": filename}, headers=headers
                ) as resp:
                    if resp.status == 401:
                        if attempt == 0:
                            await self.authenticate()
                            continue
                        raise NovaAuthError("Authentication failed after retry")
                    if resp.status == 404:
                        return None
                    resp.raise_for_status()
                    return await resp.read()
            except aiohttp.ClientResponseError as err:
                raise NovaConnectionError(str(err)) from err
            except aiohttp.ClientError as err:
                raise NovaConnectionError(str(err)) from err
        return None

    async def delete_screencapture(self, filename: str) -> None:
        """Delete a stored screen capture by filename."""
        if self._token is None:
            await self.authenticate()
        url = f"{self._base}/screencapture"
        for attempt in range(2):
            headers = {"Authorization": f"Bearer {self._token}"}
            try:
                async with self._session.delete(
                    url, params={"uuid": filename}, headers=headers
                ) as resp:
                    if resp.status == 401:
                        if attempt == 0:
                            await self.authenticate()
                            continue
                        raise NovaAuthError("Authentication failed after retry")
                    resp.raise_for_status()
                    return
            except aiohttp.ClientResponseError as err:
                raise NovaConnectionError(str(err)) from err
            except aiohttp.ClientError as err:
                raise NovaConnectionError(str(err)) from err

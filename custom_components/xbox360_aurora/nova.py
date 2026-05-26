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

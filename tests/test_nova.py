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


def _make_session() -> aiohttp.ClientSession:
    """Create a ClientSession that does not spawn background threads.

    Use ThreadedResolver to avoid the pycares AsyncResolver, which starts a
    persistent daemon thread (``_run_safe_shutdown_loop``) that the
    pytest-homeassistant-custom-component ``verify_cleanup`` fixture rejects.
    """
    connector = aiohttp.TCPConnector(resolver=aiohttp.ThreadedResolver())
    return aiohttp.ClientSession(connector=connector)


async def test_authenticate_returns_and_stores_token():
    async with _make_session() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "xboxhttp", "xboxhttp")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "abc123"})
            token = await client.authenticate()
        assert token == "abc123"
        assert client.token == "abc123"


async def test_authenticate_bad_credentials_raises_auth_error():
    async with _make_session() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "x", "y")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", status=401)
            with pytest.raises(NovaAuthError):
                await client.authenticate()


async def test_authenticate_connection_failure_raises_connection_error():
    async with _make_session() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "x", "y")
        with aioresponses() as mock:
            mock.post(
                f"{BASE}/authenticate",
                exception=aiohttp.ClientConnectionError("boom"),
            )
            with pytest.raises(NovaConnectionError):
                await client.authenticate()

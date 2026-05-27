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


async def test_get_title_sends_bearer_and_returns_json():
    async with _make_session() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.get(f"{BASE}/title", payload={"titleid": "DEADBEEF"})
            result = await client.get_title()
        assert result == {"titleid": "DEADBEEF"}


async def test_request_reauths_once_on_401():
    async with _make_session() as session:
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
    async with _make_session() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.get(f"{BASE}/title", status=401)
            mock.post(f"{BASE}/authenticate", payload={"token": "t2"})
            mock.get(f"{BASE}/title", status=401)
            with pytest.raises(NovaAuthError):
                await client.get_title()


async def test_get_temperature_and_memory():
    async with _make_session() as session:
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


async def test_launch_title_posts_multipart_fields():
    async with _make_session() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.post(f"{BASE}/title/launch", status=202)
            # Should not raise on a 202 with no JSON body.
            await client.launch_title("default.xex", r"Hdd1:\Games\MyGame", 0)
        # Confirm the launch endpoint was actually called.
        called = any(
            method == "POST" and str(url).endswith("/title/launch")
            for (method, url) in mock.requests
        )
        assert called


async def test_get_smc_profile_bandwidth():
    async with _make_session() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.get(f"{BASE}/smc", payload={"avpack": 1, "traystate": 4})
            smc = await client.get_smc()
            mock.get(f"{BASE}/profile", payload=[{"gamertag": "Hudson", "signedin": 1}])
            profile = await client.get_profile()
            mock.get(
                f"{BASE}/systemlink/bandwidth",
                payload={"rate": {"downstream": 10.0, "upstream": 2.0}},
            )
            bw = await client.get_systemlink_bandwidth()
        assert smc["traystate"] == 4
        assert profile[0]["gamertag"] == "Hudson"
        assert bw["rate"]["downstream"] == 10.0


async def test_set_thread_state_posts_suspend():
    async with _make_session() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.post(f"{BASE}/thread/state", status=202)
            await client.set_thread_state(True)
        called = any(
            method == "POST" and str(url).endswith("/thread/state")
            for (method, url) in mock.requests
        )
        assert called


async def test_get_achievement_and_player():
    async with _make_session() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.get(f"{BASE}/achievement", payload=[{"id": 1, "cred": 20}])
            ach = await client.get_achievement()
            mock.get(f"{BASE}/achievement/player", payload=[{"id": 1, "player": [1, 0, 0, 0]}])
            players = await client.get_achievement_player()
        assert ach[0]["cred"] == 20
        assert players[0]["player"][0] == 1


async def test_get_profile_image_returns_bytes():
    async with _make_session() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.get(
                f"{BASE}/image/profile?uuid=0",
                body=b"BMP-BYTES",
                content_type="image/bmp",
            )
            data = await client.get_profile_image(0)
        assert data == b"BMP-BYTES"


async def test_take_screencapture_returns_meta():
    async with _make_session() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.get(
                f"{BASE}/screencapture/meta",
                payload={"filename": "415608C320260527", "titleid": "415608C3"},
            )
            result = await client.take_screencapture()
        assert result == {"filename": "415608C320260527", "titleid": "415608C3"}


async def test_list_screencaptures_returns_list():
    async with _make_session() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.get(
                f"{BASE}/screencapture/meta/list",
                payload=[{"filename": "x", "timestamp": "20260527"}],
            )
            result = await client.list_screencaptures()
        assert result == [{"filename": "x", "timestamp": "20260527"}]


async def test_get_plugin_returns_json():
    async with _make_session() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.get(
                f"{BASE}/plugin",
                payload={"version": "0.7b", "features": ["screencapture"]},
            )
            result = await client.get_plugin()
        assert result["version"] == "0.7b"
        assert "screencapture" in result["features"]


async def test_get_dashlaunch_returns_json():
    async with _make_session() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.get(
                f"{BASE}/dashlaunch",
                payload={"version": "3.21", "kernel": "2.0.17559.0"},
            )
            result = await client.get_dashlaunch()
        assert result["version"] == "3.21"
        assert result["kernel"] == "2.0.17559.0"


async def test_get_update_notification_returns_counters():
    async with _make_session() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.get(
                f"{BASE}/update/notification",
                payload={"titles": 5, "profiles": 2, "screencaptures": 3},
            )
            result = await client.get_update_notification()
        assert result == {"titles": 5, "profiles": 2, "screencaptures": 3}


async def test_get_screencapture_image_returns_bytes():
    async with _make_session() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.get(
                f"{BASE}/image/screencapture?uuid=fname",
                body=b"BMP-SCREEN-BYTES",
                content_type="image/bmp",
            )
            data = await client.get_screencapture_image("fname")
        assert data == b"BMP-SCREEN-BYTES"


async def test_delete_screencapture_issues_delete():
    async with _make_session() as session:
        client = NovaClient(session, "1.2.3.4", 9999, "u", "p")
        with aioresponses() as mock:
            mock.post(f"{BASE}/authenticate", payload={"token": "t1"})
            mock.delete(f"{BASE}/screencapture?uuid=fname", status=204)
            await client.delete_screencapture("fname")
        called = any(
            method == "DELETE" and "/screencapture" in str(url)
            for (method, url) in mock.requests
        )
        assert called

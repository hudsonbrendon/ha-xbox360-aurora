"""Fixtures for Xbox 360 Aurora tests."""
from unittest.mock import AsyncMock, patch

import aiohttp.resolver
import homeassistant.helpers.aiohttp_client as _ha_aiohttp_client
import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of custom integrations in all tests."""
    yield


@pytest.fixture(autouse=True)
def _use_threaded_resolver():
    """Replace the c-ares AsyncResolver with the pure-Python ThreadedResolver.

    aiohttp's default resolver (AsyncResolver via pycares/aiodns) spawns a
    persistent daemon thread named ``_run_safe_shutdown_loop`` when the DNS
    channel is garbage-collected.  The
    pytest-homeassistant-custom-component ``verify_cleanup`` fixture rejects
    any threads that linger after a test, causing a teardown error.

    HA's ``_async_get_connector`` (called by ``async_get_clientsession``)
    explicitly imports and instantiates ``AsyncResolver`` using the name bound
    in ``homeassistant.helpers.aiohttp_client`` (``from aiohttp.resolver import
    AsyncResolver``).  Patching that module-level name ensures the connector
    created for tests uses ``ThreadedResolver`` and never touches pycares.
    """
    original = _ha_aiohttp_client.AsyncResolver
    _ha_aiohttp_client.AsyncResolver = aiohttp.resolver.ThreadedResolver
    try:
        yield
    finally:
        _ha_aiohttp_client.AsyncResolver = original


@pytest.fixture
def mock_nova():
    """Patch all coordinator-polled NovaClient methods with overridable AsyncMocks.

    Yields a dict keyed by method name; tests set `.return_value` (or
    `.side_effect`) before calling async_setup to customize responses.
    """
    defaults = {
        "authenticate": AsyncMock(return_value="tok"),
        "get_title": AsyncMock(return_value={}),
        "get_temperature": AsyncMock(return_value={}),
        "get_memory": AsyncMock(return_value={}),
        "get_system": AsyncMock(return_value={}),
        "get_smc": AsyncMock(return_value={}),
        "get_profile": AsyncMock(return_value=[]),
        "get_systemlink_bandwidth": AsyncMock(return_value={}),
        "get_achievement": AsyncMock(return_value=[]),
        "get_achievement_player": AsyncMock(return_value=[]),
    }
    with patch.multiple(
        "custom_components.xbox360_aurora.nova.NovaClient", create=True, **defaults
    ):
        yield defaults

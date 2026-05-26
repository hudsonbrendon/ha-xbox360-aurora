"""Fixtures for Xbox 360 Aurora tests."""
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

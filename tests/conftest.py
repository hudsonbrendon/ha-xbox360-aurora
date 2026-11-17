"""Fixtures for Xbox 360 Aurora tests."""
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of custom integrations in all tests."""
    yield


@pytest.fixture(autouse=True)
def _instant_request_refresh():
    """Make the coordinator's background refresh fire immediately in tests.

    Setup now calls ``coordinator.async_request_refresh()`` (non-blocking) so
    HA finishes setup even when the console is off.  That request is debounced
    with a 10s cooldown, which never elapses inside ``async_block_till_done``.
    Dropping the cooldown to 0 lets the first refresh complete during setup so
    entity-state assertions stay deterministic.
    """
    with patch(
        "homeassistant.helpers.update_coordinator.REQUEST_REFRESH_DEFAULT_COOLDOWN",
        0,
    ):
        yield


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
        "list_screencaptures": AsyncMock(return_value=[]),
        "get_update_notification": AsyncMock(return_value={}),
        "get_plugin": AsyncMock(return_value={}),
        "get_dashlaunch": AsyncMock(return_value={}),
        "take_screencapture": AsyncMock(return_value={}),
        "get_screencapture_image": AsyncMock(return_value=None),
        "delete_screencapture": AsyncMock(return_value=None),
    }
    with patch.multiple(
        "xbox360_nova.NovaClient", create=True, **defaults
    ):
        yield defaults

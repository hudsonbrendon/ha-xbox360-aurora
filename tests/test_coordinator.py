"""Tests for the coordinator's offline / last-known-state behavior."""
import pytest
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.xbox360_aurora.const import (
    CONF_FTP_PASSWORD,
    CONF_FTP_PORT,
    CONF_FTP_USERNAME,
    DOMAIN,
)

from xbox360_nova import NovaAuthError, NovaError

ENTRY_DATA = {
    CONF_HOST: "1.2.3.4",
    CONF_PORT: 9999,
    CONF_USERNAME: "xboxhttp",
    CONF_PASSWORD: "xboxhttp",
    CONF_FTP_PORT: 21,
    CONF_FTP_USERNAME: "xboxftp",
    CONF_FTP_PASSWORD: "xboxftp",
}

TITLE_PAYLOAD = {"titleid": "DEADBEEF", "path": r"Hdd1:\Games\X"}


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=ENTRY_DATA,
        unique_id="1.2.3.4:9999",
        title="Xbox 360 (1.2.3.4)",
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_connection_error_keeps_last_known_state(
    hass: HomeAssistant, mock_nova
):
    """A NovaError during update returns cached data instead of raising."""
    mock_nova["get_title"].return_value = TITLE_PAYLOAD
    entry = await _setup(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # First refresh succeeded and populated data.
    assert coordinator.data is not None
    assert coordinator.last_update_success is True
    cached = coordinator.data
    assert cached["title"] == TITLE_PAYLOAD

    # Console goes offline: a connection (non-auth) error is raised.
    mock_nova["get_title"].side_effect = NovaError("connection refused")

    result = await coordinator._async_update_data()

    # Cached data is returned unchanged, no exception raised.
    assert result is cached


async def test_auth_error_raises_config_entry_auth_failed(
    hass: HomeAssistant, mock_nova
):
    """A NovaAuthError during update raises ConfigEntryAuthFailed."""
    mock_nova["get_title"].return_value = TITLE_PAYLOAD
    entry = await _setup(hass)
    coordinator = hass.data[DOMAIN][entry.entry_id]

    assert coordinator.data is not None

    mock_nova["get_title"].side_effect = NovaAuthError("bad credentials")

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()

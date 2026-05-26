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

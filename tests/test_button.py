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
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=ENTRY_DATA,
        unique_id="1.2.3.4:9999",
        title="Xbox 360 (1.2.3.4)",
    )
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
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_system",
        new=AsyncMock(return_value={}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_smc",
        new=AsyncMock(return_value={}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_profile",
        new=AsyncMock(return_value=[]),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_systemlink_bandwidth",
        new=AsyncMock(return_value={}),
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


async def test_restart_aurora_button_sends_site_restart(hass: HomeAssistant):
    await _setup(hass)
    with patch(
        "custom_components.xbox360_aurora.button.site_command", return_value="200 OK"
    ) as mock_site:
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.xbox_360_1_2_3_4_restart_aurora"},
            blocking=True,
        )
    mock_site.assert_called_once_with("1.2.3.4", 21, "xboxftp", "xboxftp", "RESTART")

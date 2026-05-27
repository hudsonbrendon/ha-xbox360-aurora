"""Tests for reboot/shutdown buttons."""
from unittest.mock import patch

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


async def _setup(hass: HomeAssistant, mock_nova) -> MockConfigEntry:
    mock_nova["get_title"].return_value = {"titleid": "1"}
    mock_nova["get_temperature"].return_value = {
        "cpu": 1, "gpu": 1, "case": 1, "memory": 1, "celsius": True
    }
    mock_nova["get_memory"].return_value = {"free": 1, "used": 1, "total": 1}
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


async def test_reboot_button_sends_site_reboot(hass: HomeAssistant, mock_nova):
    await _setup(hass, mock_nova)
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


async def test_shutdown_button_sends_site_shutdown(hass: HomeAssistant, mock_nova):
    await _setup(hass, mock_nova)
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


async def test_restart_aurora_button_sends_site_restart(hass: HomeAssistant, mock_nova):
    await _setup(hass, mock_nova)
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


async def test_take_screenshot_button(hass: HomeAssistant, mock_nova):
    await _setup(hass, mock_nova)
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.xbox_360_1_2_3_4_take_screenshot"},
        blocking=True,
    )
    mock_nova["take_screencapture"].assert_awaited()


async def test_delete_screenshot_button(hass: HomeAssistant, mock_nova):
    mock_nova["list_screencaptures"].return_value = [{"filename": "x", "timestamp": "1"}]
    await _setup(hass, mock_nova)
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.xbox_360_1_2_3_4_delete_screenshot"},
        blocking=True,
    )
    mock_nova["delete_screencapture"].assert_awaited_once_with("x")

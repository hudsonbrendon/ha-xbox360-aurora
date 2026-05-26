"""Tests for sensor entities."""
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


async def test_sensors_expose_nova_values(hass: HomeAssistant):
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
        new=AsyncMock(return_value={"titleid": "DEADBEEF"}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature",
        new=AsyncMock(
            return_value={"cpu": 50, "gpu": 55, "case": 40, "memory": 45, "celsius": True}
        ),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_memory",
        new=AsyncMock(return_value={"free": 104857600, "used": 200, "total": 300}),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.xbox_360_1_2_3_4_current_title").state == "DEADBEEF"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_cpu_temperature").state == "50"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_gpu_temperature").state == "55"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_free_ram").state == "100.0"


async def test_current_title_resolves_game_name(hass: HomeAssistant):
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
        new=AsyncMock(return_value={"titleid": "0x415608C3"}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature",
        new=AsyncMock(
            return_value={"cpu": 50, "gpu": 55, "case": 40, "memory": 45, "celsius": True}
        ),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_memory",
        new=AsyncMock(return_value={"free": 104857600, "used": 200, "total": 300}),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.xbox_360_1_2_3_4_current_title")
    assert state.state == "Call of Duty: Black Ops II"
    assert state.attributes["title_id"] == "415608C3"

"""Tests for the connectivity binary sensor."""
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
from custom_components.xbox360_aurora.nova import NovaConnectionError

ENTRY_DATA = {
    CONF_HOST: "1.2.3.4",
    CONF_PORT: 9999,
    CONF_USERNAME: "xboxhttp",
    CONF_PASSWORD: "xboxhttp",
    CONF_FTP_PORT: 21,
    CONF_FTP_USERNAME: "xboxftp",
    CONF_FTP_PASSWORD: "xboxftp",
}


async def test_connectivity_on_when_polling_succeeds(hass: HomeAssistant):
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

    state = hass.states.get("binary_sensor.xbox_360_1_2_3_4_online")
    assert state is not None
    assert state.state == "on"


async def test_connectivity_off_when_polling_fails(hass: HomeAssistant):
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
        new=AsyncMock(side_effect=NovaConnectionError("offline")),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature",
        new=AsyncMock(side_effect=NovaConnectionError("offline")),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_memory",
        new=AsyncMock(side_effect=NovaConnectionError("offline")),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_smc",
        new=AsyncMock(side_effect=NovaConnectionError("offline")),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_profile",
        new=AsyncMock(side_effect=NovaConnectionError("offline")),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_systemlink_bandwidth",
        new=AsyncMock(side_effect=NovaConnectionError("offline")),
    ):
        # First refresh fails -> entry setup raises ConfigEntryNotReady.
        # We still want the binary sensor available and "off", so we force a
        # successful setup first, then a failed refresh.
        with patch(
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

        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_refresh()
        await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.xbox_360_1_2_3_4_online")
    assert state.state == "off"

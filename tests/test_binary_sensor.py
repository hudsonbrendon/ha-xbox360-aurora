"""Tests for the connectivity binary sensor."""
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.xbox360_aurora.const import (
    CONF_FTP_PASSWORD,
    CONF_FTP_PORT,
    CONF_FTP_USERNAME,
    DOMAIN,
)
from xbox360_nova import NovaConnectionError

ENTRY_DATA = {
    CONF_HOST: "1.2.3.4",
    CONF_PORT: 9999,
    CONF_USERNAME: "xboxhttp",
    CONF_PASSWORD: "xboxhttp",
    CONF_FTP_PORT: 21,
    CONF_FTP_USERNAME: "xboxftp",
    CONF_FTP_PASSWORD: "xboxftp",
}


async def test_connectivity_on_when_polling_succeeds(hass: HomeAssistant, mock_nova):
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

    state = hass.states.get("binary_sensor.xbox_360_1_2_3_4_online")
    assert state is not None
    assert state.state == "on"


async def test_connectivity_off_when_first_poll_fails(hass: HomeAssistant, mock_nova):
    """With no cached data yet, a connection failure leaves the sensor off.

    When the console is unreachable from the very first refresh there is no
    last-known state to keep, so the coordinator raises ``UpdateFailed`` and
    ``last_update_success`` stays ``False`` -> connectivity reports "off".
    """
    mock_nova["get_title"].side_effect = NovaConnectionError("offline")
    mock_nova["get_temperature"].side_effect = NovaConnectionError("offline")
    mock_nova["get_memory"].side_effect = NovaConnectionError("offline")
    mock_nova["get_smc"].side_effect = NovaConnectionError("offline")
    mock_nova["get_profile"].side_effect = NovaConnectionError("offline")
    mock_nova["get_systemlink_bandwidth"].side_effect = NovaConnectionError("offline")

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=ENTRY_DATA,
        unique_id="1.2.3.4:9999",
        title="Xbox 360 (1.2.3.4)",
    )
    entry.add_to_hass(hass)
    # Setup is non-blocking, so it succeeds even though the console is offline.
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.xbox_360_1_2_3_4_online")
    assert state is not None
    assert state.state == "off"


async def test_connectivity_off_but_data_retained_when_console_goes_offline(
    hass: HomeAssistant, mock_nova
):
    """After a successful poll, a later connection failure reports off but keeps data.

    The coordinator keeps the cached payload so data entities retain their
    last-known values, but ``device_online`` flips to ``False`` so the
    connectivity sensor correctly reports the console as offline.
    """
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

    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator.data is not None
    assert coordinator.device_online is True
    cached = coordinator.data

    # Console goes offline on the next refresh.
    mock_nova["get_title"].side_effect = NovaConnectionError("offline")
    mock_nova["get_temperature"].side_effect = NovaConnectionError("offline")
    mock_nova["get_memory"].side_effect = NovaConnectionError("offline")
    mock_nova["get_smc"].side_effect = NovaConnectionError("offline")
    mock_nova["get_profile"].side_effect = NovaConnectionError("offline")
    mock_nova["get_systemlink_bandwidth"].side_effect = NovaConnectionError("offline")

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # The console is reported offline...
    assert coordinator.device_online is False
    state = hass.states.get("binary_sensor.xbox_360_1_2_3_4_online")
    assert state is not None
    assert state.state == "off"

    # ...but data entities keep their last-known values.
    assert coordinator.data == cached

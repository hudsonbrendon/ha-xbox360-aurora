"""Restore-on-restart: entities keep their last value across a HA restart.

``test_coordinator.py`` / ``test_binary_sensor.py`` cover staying available
while the console is merely offline *within one running HA process*
(``coordinator.data`` lives in memory and is simply not cleared). This file
covers the harder case: a full Home Assistant restart reborns
``coordinator.data`` as ``None`` before the console is ever reached again, so
the previous run's last value has to come back from Home Assistant's
restore-state storage instead. Unlike ``jbl_charge5``/``igps``,
``async_setup_entry`` here never blocks on the first refresh (it runs in a
background task), so setup always succeeds even with the console off — a
full config-entry setup can be exercised directly.
"""

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant, State
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache,
    mock_restore_cache_with_extra_data,
)

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


def _fail_all_polls(mock_nova) -> None:
    for key in (
        "get_title",
        "get_temperature",
        "get_memory",
        "get_smc",
        "get_profile",
        "get_systemlink_bandwidth",
    ):
        mock_nova[key].side_effect = NovaConnectionError("offline")


async def _setup_with_console_off(hass: HomeAssistant, mock_nova) -> MockConfigEntry:
    """Load the integration as if the console were off across the restart."""
    _fail_all_polls(mock_nova)
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


async def test_gamertag_sensor_restores_last_value_after_restart(
    hass: HomeAssistant, mock_nova
):
    """A string sensor must show its pre-restart value, not go unavailable."""
    mock_restore_cache_with_extra_data(
        hass,
        (
            (
                State("sensor.xbox_360_1_2_3_4_gamertag", "PlayerOne"),
                {"native_value": "PlayerOne", "native_unit_of_measurement": None},
            ),
        ),
    )

    await _setup_with_console_off(hass, mock_nova)

    state = hass.states.get("sensor.xbox_360_1_2_3_4_gamertag")
    assert state is not None
    assert state.state == "PlayerOne"


async def test_gamerscore_sensor_restores_last_value_after_restart(
    hass: HomeAssistant, mock_nova
):
    """A numeric sensor restores its typed last value, not a raw string."""
    mock_restore_cache_with_extra_data(
        hass,
        (
            (
                State("sensor.xbox_360_1_2_3_4_gamerscore", "12345"),
                {"native_value": 12345, "native_unit_of_measurement": None},
            ),
        ),
    )

    await _setup_with_console_off(hass, mock_nova)

    state = hass.states.get("sensor.xbox_360_1_2_3_4_gamerscore")
    assert state is not None
    assert state.state == "12345"


async def test_sensor_unavailable_when_nothing_was_ever_restored(
    hass: HomeAssistant, mock_nova
):
    """No prior state, no live data: stays unavailable, no fake value."""
    await _setup_with_console_off(hass, mock_nova)

    state = hass.states.get("sensor.xbox_360_1_2_3_4_gamertag")
    assert state is not None
    assert state.state == "unavailable"


async def test_pause_switch_restores_last_commanded_state_after_restart(
    hass: HomeAssistant, mock_nova
):
    """The optimistic pause switch restores its last commanded on/off."""
    mock_restore_cache(
        hass, [State("switch.xbox_360_1_2_3_4_game_paused", "on")]
    )

    await _setup_with_console_off(hass, mock_nova)

    state = hass.states.get("switch.xbox_360_1_2_3_4_game_paused")
    assert state is not None
    assert state.state == "on"


async def test_connectivity_sensor_never_restores_a_stale_on(
    hass: HomeAssistant, mock_nova
):
    """Connectivity is a live fact: a saved 'on' must never leak back in."""
    mock_restore_cache(
        hass, [State("binary_sensor.xbox_360_1_2_3_4_online", "on")]
    )

    await _setup_with_console_off(hass, mock_nova)

    state = hass.states.get("binary_sensor.xbox_360_1_2_3_4_online")
    assert state is not None
    assert state.state == "off"

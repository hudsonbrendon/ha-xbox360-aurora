"""Tests for the pause/resume switch."""
import contextlib
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

EMPTY = {}


def _patches():
    return [
        patch("custom_components.xbox360_aurora.NovaClient.authenticate", new=AsyncMock(return_value="tok")),
        patch("custom_components.xbox360_aurora.coordinator.NovaClient.get_title", new=AsyncMock(return_value=EMPTY)),
        patch("custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature", new=AsyncMock(return_value=EMPTY)),
        patch("custom_components.xbox360_aurora.coordinator.NovaClient.get_memory", new=AsyncMock(return_value=EMPTY)),
        patch("custom_components.xbox360_aurora.coordinator.NovaClient.get_system", new=AsyncMock(return_value=EMPTY)),
        patch("custom_components.xbox360_aurora.coordinator.NovaClient.get_smc", new=AsyncMock(return_value=EMPTY)),
        patch("custom_components.xbox360_aurora.coordinator.NovaClient.get_profile", new=AsyncMock(return_value=[])),
        patch("custom_components.xbox360_aurora.coordinator.NovaClient.get_systemlink_bandwidth", new=AsyncMock(return_value=EMPTY)),
    ]


async def test_pause_switch_calls_set_thread_state(hass: HomeAssistant):
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA, unique_id="1.2.3.4:9999", title="Xbox 360 (1.2.3.4)")
    entry.add_to_hass(hass)
    with contextlib.ExitStack() as stack:
        for p in _patches():
            stack.enter_context(p)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        eid = "switch.xbox_360_1_2_3_4_game_paused"
        assert hass.states.get(eid).state == "off"

        with patch(
            "custom_components.xbox360_aurora.switch.NovaClient.set_thread_state",
            new=AsyncMock(),
        ) as mock_set:
            await hass.services.async_call(
                "switch", "turn_on", {"entity_id": eid}, blocking=True
            )
            mock_set.assert_awaited_once_with(True)
            assert hass.states.get(eid).state == "on"

            await hass.services.async_call(
                "switch", "turn_off", {"entity_id": eid}, blocking=True
            )
            assert mock_set.await_args.args == (False,)
            assert hass.states.get(eid).state == "off"

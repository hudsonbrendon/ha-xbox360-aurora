"""Tests for config entry diagnostics."""
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
from custom_components.xbox360_aurora.diagnostics import (
    async_get_config_entry_diagnostics,
)

ENTRY_DATA = {
    CONF_HOST: "1.2.3.4",
    CONF_PORT: 9999,
    CONF_USERNAME: "xboxhttp",
    CONF_PASSWORD: "secret",
    CONF_FTP_PORT: 21,
    CONF_FTP_USERNAME: "xboxftp",
    CONF_FTP_PASSWORD: "ftpsecret",
}


async def test_diagnostics_redacts_secrets(hass: HomeAssistant):
    system = {"serial": "123", "cpukey": "AAAA", "dvdkey": "BBBB", "console": {"motherboard": "Jasper"}}
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_DATA, unique_id="1.2.3.4:9999", title="Xbox 360 (1.2.3.4)")
    entry.add_to_hass(hass)
    patches = [
        patch("custom_components.xbox360_aurora.NovaClient.authenticate", new=AsyncMock(return_value="tok")),
        patch("custom_components.xbox360_aurora.coordinator.NovaClient.get_title", new=AsyncMock(return_value={"titleid": "DEADBEEF"})),
        patch("custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature", new=AsyncMock(return_value={})),
        patch("custom_components.xbox360_aurora.coordinator.NovaClient.get_memory", new=AsyncMock(return_value={})),
        patch("custom_components.xbox360_aurora.coordinator.NovaClient.get_system", new=AsyncMock(return_value=system)),
        patch("custom_components.xbox360_aurora.coordinator.NovaClient.get_smc", new=AsyncMock(return_value={})),
        patch("custom_components.xbox360_aurora.coordinator.NovaClient.get_profile", new=AsyncMock(return_value=[])),
        patch("custom_components.xbox360_aurora.coordinator.NovaClient.get_systemlink_bandwidth", new=AsyncMock(return_value={})),
    ]
    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        diag = await async_get_config_entry_diagnostics(hass, entry)

    assert diag["entry_data"][CONF_PASSWORD] == "**REDACTED**"
    assert diag["entry_data"][CONF_FTP_PASSWORD] == "**REDACTED**"
    assert diag["system"]["cpukey"] == "**REDACTED**"
    assert diag["system"]["dvdkey"] == "**REDACTED**"
    assert diag["system"]["console"]["motherboard"] == "Jasper"
    assert diag["data"]["title"]["titleid"] == "DEADBEEF"

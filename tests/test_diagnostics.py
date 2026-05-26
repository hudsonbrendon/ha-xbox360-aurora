"""Tests for config entry diagnostics."""
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


async def test_diagnostics_redacts_secrets(hass: HomeAssistant, mock_nova):
    system = {
        "serial": "123", "cpukey": "AAAA", "dvdkey": "BBBB",
        "console": {"motherboard": "Jasper"},
    }
    mock_nova["get_title"].return_value = {"titleid": "DEADBEEF"}
    mock_nova["get_system"].return_value = system
    entry = MockConfigEntry(
        domain=DOMAIN, data=ENTRY_DATA, unique_id="1.2.3.4:9999", title="Xbox 360 (1.2.3.4)"
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    diag = await async_get_config_entry_diagnostics(hass, entry)

    assert diag["entry_data"][CONF_PASSWORD] == "**REDACTED**"
    assert diag["entry_data"][CONF_FTP_PASSWORD] == "**REDACTED**"
    assert diag["system"]["cpukey"] == "**REDACTED**"
    assert diag["system"]["dvdkey"] == "**REDACTED**"
    assert diag["system"]["console"]["motherboard"] == "Jasper"
    assert diag["data"]["title"]["titleid"] == "DEADBEEF"

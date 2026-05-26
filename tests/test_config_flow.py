"""Tests for the config flow."""
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant

from custom_components.xbox360_aurora.const import (
    CONF_FTP_PASSWORD,
    CONF_FTP_PORT,
    CONF_FTP_USERNAME,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)
from custom_components.xbox360_aurora.nova import NovaAuthError, NovaConnectionError

USER_INPUT = {
    CONF_HOST: "1.2.3.4",
    CONF_PORT: 9999,
    CONF_USERNAME: "xboxhttp",
    CONF_PASSWORD: "xboxhttp",
    CONF_FTP_PORT: 21,
    CONF_FTP_USERNAME: "xboxftp",
    CONF_FTP_PASSWORD: "xboxftp",
}


async def test_user_flow_success(hass: HomeAssistant):
    with patch(
        "custom_components.xbox360_aurora.config_flow.NovaClient.authenticate",
        new=AsyncMock(return_value="tok"),
    ), patch(
        "custom_components.xbox360_aurora.async_setup_entry",
        new=AsyncMock(return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Xbox 360 (1.2.3.4)"
    assert result2["data"] == USER_INPUT


async def test_user_flow_invalid_auth(hass: HomeAssistant):
    with patch(
        "custom_components.xbox360_aurora.config_flow.NovaClient.authenticate",
        new=AsyncMock(side_effect=NovaAuthError),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_user_flow_cannot_connect(hass: HomeAssistant):
    with patch(
        "custom_components.xbox360_aurora.config_flow.NovaClient.authenticate",
        new=AsyncMock(side_effect=NovaConnectionError),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_options_flow_sets_scan_interval(hass: HomeAssistant):
    entry = __import__(
        "pytest_homeassistant_custom_component.common", fromlist=["MockConfigEntry"]
    ).MockConfigEntry(domain=DOMAIN, data=USER_INPUT, unique_id="1.2.3.4:9999")
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 60}
    )
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_SCAN_INTERVAL] == 60

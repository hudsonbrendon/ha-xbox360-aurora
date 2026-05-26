"""Config flow for Xbox 360 Aurora."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_FTP_PASSWORD,
    CONF_FTP_PORT,
    CONF_FTP_USERNAME,
    DEFAULT_FTP_PASSWORD,
    DEFAULT_FTP_PORT,
    DEFAULT_FTP_USERNAME,
    DEFAULT_NOVA_PASSWORD,
    DEFAULT_NOVA_PORT,
    DEFAULT_NOVA_USERNAME,
    DOMAIN,
)
from .nova import NovaAuthError, NovaClient, NovaError

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_NOVA_PORT): int,
        vol.Required(CONF_USERNAME, default=DEFAULT_NOVA_USERNAME): str,
        vol.Required(CONF_PASSWORD, default=DEFAULT_NOVA_PASSWORD): str,
        vol.Required(CONF_FTP_PORT, default=DEFAULT_FTP_PORT): int,
        vol.Required(CONF_FTP_USERNAME, default=DEFAULT_FTP_USERNAME): str,
        vol.Required(CONF_FTP_PASSWORD, default=DEFAULT_FTP_PASSWORD): str,
    }
)


class XboxAuroraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the UI configuration flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = NovaClient(
                session,
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            try:
                await client.authenticate()
            except NovaAuthError:
                errors["base"] = "invalid_auth"
            except NovaError:
                errors["base"] = "cannot_connect"
            else:
                unique_id = f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Xbox 360 ({user_input[CONF_HOST]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

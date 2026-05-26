"""The Xbox 360 Aurora integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    ATTR_EXEC,
    ATTR_PATH,
    ATTR_TYPE,
    DOMAIN,
    PLATFORMS,
    SERVICE_LAUNCH_TITLE,
)
from .coordinator import XboxAuroraCoordinator
from .nova import NovaClient
from .titles import async_load_titles

LAUNCH_TITLE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_EXEC): cv.string,
        vol.Required(ATTR_PATH): cv.string,
        vol.Optional(ATTR_TYPE, default=0): vol.All(
            vol.Coerce(int), vol.Range(min=-1, max=4)
        ),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Xbox 360 Aurora from a config entry."""
    session = async_get_clientsession(hass)
    client = NovaClient(
        session,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    await async_load_titles(hass)

    coordinator = XboxAuroraCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_LAUNCH_TITLE)
    return unload_ok


def _async_register_services(hass: HomeAssistant) -> None:
    """Register the launch_title service once."""
    if hass.services.has_service(DOMAIN, SERVICE_LAUNCH_TITLE):
        return

    async def _handle_launch_title(call: ServiceCall) -> None:
        """Launch a title on every configured console."""
        for coordinator in hass.data[DOMAIN].values():
            await coordinator.client.launch_title(
                call.data[ATTR_EXEC],
                call.data[ATTR_PATH],
                call.data[ATTR_TYPE],
            )

    hass.services.async_register(
        DOMAIN, SERVICE_LAUNCH_TITLE, _handle_launch_title, schema=LAUNCH_TITLE_SCHEMA
    )

"""Diagnostics support for Xbox 360 Aurora."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import CONF_FTP_PASSWORD, DOMAIN
from .coordinator import XboxAuroraCoordinator

REDACT_ENTRY = {CONF_PASSWORD, CONF_FTP_PASSWORD}
REDACT_SYSTEM = {"cpukey", "dvdkey", "serial", "consoleid"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return redacted diagnostics for a config entry."""
    coordinator: XboxAuroraCoordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "entry_data": async_redact_data(dict(entry.data), REDACT_ENTRY),
        "options": dict(entry.options),
        "system": async_redact_data(coordinator.system, REDACT_SYSTEM),
        "data": async_redact_data(coordinator.data or {}, REDACT_SYSTEM),
    }

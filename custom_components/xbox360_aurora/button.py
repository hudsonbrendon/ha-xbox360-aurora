"""Button platform for Xbox 360 Aurora (reboot/shutdown via FTP)."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_FTP_PASSWORD,
    CONF_FTP_PORT,
    CONF_FTP_USERNAME,
    DOMAIN,
    FTP_CMD_REBOOT,
    FTP_CMD_SHUTDOWN,
)
from .ftp import site_command


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up reboot and shutdown buttons."""
    async_add_entities(
        [
            XboxAuroraButton(entry, "reboot", "reboot", FTP_CMD_REBOOT),
            XboxAuroraButton(entry, "shutdown", "shutdown", FTP_CMD_SHUTDOWN),
        ]
    )


class XboxAuroraButton(ButtonEntity):
    """A button that issues an Aurora FTP SITE command."""

    _attr_has_entity_name = True

    def __init__(
        self, entry: ConfigEntry, key: str, translation_key: str, command: str
    ) -> None:
        self._entry = entry
        self._command = command
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Microsoft",
            model="Xbox 360 (Aurora / NOVA)",
        )

    async def async_press(self) -> None:
        """Run the SITE command in the executor (ftplib is blocking)."""
        data = self._entry.data
        await self.hass.async_add_executor_job(
            site_command,
            data[CONF_HOST],
            data[CONF_FTP_PORT],
            data[CONF_FTP_USERNAME],
            data[CONF_FTP_PASSWORD],
            self._command,
        )

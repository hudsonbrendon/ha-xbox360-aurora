"""Button platform for Xbox 360 Aurora (reboot/shutdown via FTP)."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from xbox360_nova import FTP_CMD_REBOOT, FTP_CMD_RESTART, FTP_CMD_SHUTDOWN, site_command

from .const import (
    CONF_FTP_PASSWORD,
    CONF_FTP_PORT,
    CONF_FTP_USERNAME,
    DOMAIN,
)
from .coordinator import XboxAuroraCoordinator
from .entity import XboxAuroraEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up reboot, shutdown, and screenshot buttons."""
    coordinator: XboxAuroraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            XboxAuroraButton(entry, "reboot", "reboot", FTP_CMD_REBOOT),
            XboxAuroraButton(entry, "shutdown", "shutdown", FTP_CMD_SHUTDOWN),
            XboxAuroraButton(entry, "restart_aurora", "restart_aurora", FTP_CMD_RESTART),
            XboxAuroraTakeScreenshotButton(coordinator, entry),
            XboxAuroraDeleteScreenshotButton(coordinator, entry),
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


class XboxAuroraTakeScreenshotButton(XboxAuroraEntity, ButtonEntity):
    """Button that triggers a screencapture via NOVA."""

    _attr_translation_key = "take_screenshot"
    _attr_icon = "mdi:camera"

    def __init__(
        self, coordinator: XboxAuroraCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_take_screenshot"

    async def async_press(self) -> None:
        """Take a screencapture and refresh coordinator data."""
        await self.coordinator.client.take_screencapture()
        await self.coordinator.async_request_refresh()


class XboxAuroraDeleteScreenshotButton(XboxAuroraEntity, ButtonEntity):
    """Button that deletes the most recent screencapture via NOVA."""

    _attr_translation_key = "delete_screenshot"
    _attr_icon = "mdi:image-remove"

    def __init__(
        self, coordinator: XboxAuroraCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_delete_screenshot"

    async def async_press(self) -> None:
        """Delete the newest screencapture and refresh coordinator data."""
        caps = (self.coordinator.data or {}).get("screencaptures") or []
        if not caps:
            return
        newest = max(caps, key=lambda c: c.get("timestamp", ""))
        filename = newest.get("filename")
        if filename:
            await self.coordinator.client.delete_screencapture(filename)
            await self.coordinator.async_request_refresh()

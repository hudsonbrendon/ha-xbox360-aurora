"""Shared entity base for Xbox 360 Aurora."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XboxAuroraCoordinator


class XboxAuroraEntity(CoordinatorEntity[XboxAuroraCoordinator]):
    """Base entity with shared DeviceInfo."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: XboxAuroraCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Microsoft",
            model="Xbox 360 (Aurora / NOVA)",
        )

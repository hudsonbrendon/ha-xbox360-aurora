"""Binary sensor platform for Xbox 360 Aurora (connectivity)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import XboxAuroraCoordinator
from .entity import XboxAuroraEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the connectivity binary sensor."""
    coordinator: XboxAuroraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([XboxAuroraOnlineSensor(coordinator, entry)])


class XboxAuroraOnlineSensor(XboxAuroraEntity, BinarySensorEntity):
    """Reports whether the console is reachable over NOVA."""

    _attr_translation_key = "online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: XboxAuroraCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_online"

    @property
    def available(self) -> bool:
        """A connectivity sensor must report even when the console is offline."""
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.last_update_success

"""Switch platform for Xbox 360 Aurora — pause/resume the running game."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import XboxAuroraCoordinator
from .entity import XboxAuroraEntity
from .nova import NovaClient  # noqa: F401  (referenced by tests for patching)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the pause/resume switch."""
    coordinator: XboxAuroraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([XboxAuroraPauseSwitch(coordinator, entry)])


class XboxAuroraPauseSwitch(XboxAuroraEntity, SwitchEntity):
    """Optimistic switch that suspends (on) or resumes (off) the running title."""

    _attr_translation_key = "game_paused"
    _attr_icon = "mdi:pause-octagon"
    _attr_assumed_state = True

    def __init__(self, coordinator: XboxAuroraCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_game_paused"
        self._attr_is_on = False

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_thread_state(True)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_thread_state(False)
        self._attr_is_on = False
        self.async_write_ha_state()

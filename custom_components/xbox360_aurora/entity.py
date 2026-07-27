"""Shared entity base for Xbox 360 Aurora."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XboxAuroraCoordinator


def build_device_info(coordinator: XboxAuroraCoordinator, entry: ConfigEntry) -> DeviceInfo:
    """Build DeviceInfo, enriched from the console's /system data when available."""
    system = coordinator.system or {}
    console = system.get("console") or {}
    motherboard = console.get("motherboard")
    model = f"Xbox 360 {motherboard}" if motherboard else "Xbox 360 (Aurora / NOVA)"

    version = system.get("version") or {}
    sw_version = None
    if version:
        sw_version = ".".join(
            str(version.get(part, 0)) for part in ("major", "minor", "build", "qfe")
        )

    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Microsoft",
        model=model,
        serial_number=system.get("serial"),
        sw_version=sw_version,
    )


class XboxAuroraEntity(RestoreEntity, CoordinatorEntity[XboxAuroraCoordinator]):
    """Base entity with shared DeviceInfo and restart-safe "last known state".

    ``coordinator.data`` already keeps its last value while the console is
    merely offline (see coordinator.py) — but that cache lives in process
    memory, so a Home Assistant *restart* still reborns it as ``None``. This
    base class closes that gap: it remembers, via ``RestoreEntity``, whether
    this entity had a real (non-unavailable, non-unknown) state before the
    restart, and factors that into ``available``.

    The connectivity binary sensor is the deliberate exception: it always
    overrides ``available`` (``True``) and ``is_on`` (live
    ``coordinator.device_online``), never restoring a value.
    """

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: XboxAuroraCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = build_device_info(coordinator, entry)
        self._restored_available = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        self._restored_available = (
            last_state is not None
            and last_state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)
        )

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success or self._restored_available

"""Shared entity base for Xbox 360 Aurora."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
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


class XboxAuroraEntity(CoordinatorEntity[XboxAuroraCoordinator]):
    """Base entity with shared DeviceInfo."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: XboxAuroraCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = build_device_info(coordinator, entry)

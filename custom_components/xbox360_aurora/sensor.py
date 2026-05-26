"""Sensor platform for Xbox 360 Aurora."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfInformation,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .coordinator import XboxAuroraCoordinator
from .entity import XboxAuroraEntity
from .titles import normalize_title_id, resolve_title_name

_TRAY_STATES = {0: "idle", 1: "closing", 2: "open", 3: "opening", 4: "closed", 5: "error"}
_AVPACK = {0: "unknown", 1: "hdmi", 2: "component", 3: "vga", 4: "composite"}
_TILT = {0: "vertical", 1: "horizontal"}


def _enum(mapping: dict[int, str], data: dict, section: str, field: str) -> StateType:
    raw = (data.get(section) or {}).get(field)
    return mapping.get(raw) if raw is not None else None


def _primary_profile(data: dict) -> dict:
    """Return the lowest-index signed-in profile, or {}."""
    profiles = [p for p in (data.get("profile") or []) if p.get("signedin")]
    if not profiles:
        return {}
    return min(profiles, key=lambda p: p.get("index", 99))


def _gamertag(data: dict) -> StateType:
    return _primary_profile(data).get("gamertag") or None


def _gamerscore(data: dict) -> StateType:
    profile = _primary_profile(data)
    return profile.get("gamerscore") if profile else None


def _signed_in_count(data: dict) -> StateType:
    return sum(1 for p in (data.get("profile") or []) if p.get("signedin"))


def _dashboard_version(data: dict) -> StateType:
    version = (data.get("system") or {}).get("version") or {}
    if not version:
        return None
    return ".".join(
        str(version.get(part, 0)) for part in ("major", "minor", "build", "qfe")
    )


@dataclass(frozen=True, kw_only=True)
class XboxSensorDescription(SensorEntityDescription):
    """Sensor description with a value extractor and optional attributes."""

    value_fn: Callable[[dict], StateType]
    attrs_fn: Callable[[dict], dict[str, StateType]] | None = None


def _free_mb(data: dict) -> StateType:
    free = (data.get("memory") or {}).get("free")
    if free is None:
        return None
    return round(free / 1048576, 1)


def _used_mb(data: dict) -> StateType:
    used = (data.get("memory") or {}).get("used")
    return None if used is None else round(used / 1048576, 1)


def _total_mb(data: dict) -> StateType:
    total = (data.get("memory") or {}).get("total")
    return None if total is None else round(total / 1048576, 1)


def _ram_usage_pct(data: dict) -> StateType:
    mem = data.get("memory") or {}
    used, total = mem.get("used"), mem.get("total")
    if not used or not total:
        return None
    return round(used / total * 100, 1)


def _current_title(data: dict) -> StateType:
    """Resolve the running title's name, falling back to the raw title ID."""
    title_id = (data.get("title") or {}).get("titleid")
    if not title_id:
        return None
    return resolve_title_name(title_id) or title_id


def _current_title_attrs(data: dict) -> dict[str, StateType]:
    title_id = (data.get("title") or {}).get("titleid")
    return {"title_id": normalize_title_id(title_id)}


SENSORS: tuple[XboxSensorDescription, ...] = (
    XboxSensorDescription(
        key="current_title",
        translation_key="current_title",
        icon="mdi:gamepad-variant",
        value_fn=_current_title,
        attrs_fn=_current_title_attrs,
    ),
    XboxSensorDescription(
        key="cpu_temperature",
        translation_key="cpu_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (data.get("temperature") or {}).get("cpu"),
    ),
    XboxSensorDescription(
        key="gpu_temperature",
        translation_key="gpu_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (data.get("temperature") or {}).get("gpu"),
    ),
    XboxSensorDescription(
        key="case_temperature",
        translation_key="case_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (data.get("temperature") or {}).get("case"),
    ),
    XboxSensorDescription(
        key="free_ram",
        translation_key="free_ram",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_free_mb,
    ),
    XboxSensorDescription(
        key="used_ram",
        translation_key="used_ram",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_used_mb,
    ),
    XboxSensorDescription(
        key="total_ram",
        translation_key="total_ram",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_total_mb,
    ),
    XboxSensorDescription(
        key="ram_usage",
        translation_key="ram_usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_ram_usage_pct,
    ),
    XboxSensorDescription(
        key="memory_temperature",
        translation_key="memory_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (data.get("temperature") or {}).get("memory"),
    ),
    XboxSensorDescription(
        key="disc_tray",
        translation_key="disc_tray",
        icon="mdi:disc",
        device_class=SensorDeviceClass.ENUM,
        options=list(_TRAY_STATES.values()),
        value_fn=lambda data: _enum(_TRAY_STATES, data, "smc", "traystate"),
    ),
    XboxSensorDescription(
        key="video_output",
        translation_key="video_output",
        icon="mdi:video-input-hdmi",
        device_class=SensorDeviceClass.ENUM,
        options=list(_AVPACK.values()),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _enum(_AVPACK, data, "smc", "avpack"),
    ),
    XboxSensorDescription(
        key="orientation",
        translation_key="orientation",
        icon="mdi:rotate-3d-variant",
        device_class=SensorDeviceClass.ENUM,
        options=list(_TILT.values()),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _enum(_TILT, data, "smc", "tiltstate"),
    ),
    XboxSensorDescription(
        key="smc_version",
        translation_key="smc_version",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: (data.get("smc") or {}).get("smcversion"),
    ),
    XboxSensorDescription(
        key="motherboard",
        translation_key="motherboard",
        icon="mdi:expansion-card",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: (data.get("system") or {}).get("console", {}).get("motherboard"),
    ),
    XboxSensorDescription(
        key="console_type",
        translation_key="console_type",
        icon="mdi:identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: (data.get("system") or {}).get("console", {}).get("type"),
    ),
    XboxSensorDescription(
        key="dashboard_version",
        translation_key="dashboard_version",
        icon="mdi:numeric",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_dashboard_version,
    ),
    XboxSensorDescription(
        key="serial_number",
        translation_key="serial_number",
        icon="mdi:barcode",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: (data.get("system") or {}).get("serial"),
    ),
    XboxSensorDescription(
        key="console_id",
        translation_key="console_id",
        icon="mdi:barcode",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: (data.get("system") or {}).get("consoleid"),
    ),
    XboxSensorDescription(
        key="gamertag",
        translation_key="gamertag",
        icon="mdi:account",
        value_fn=_gamertag,
    ),
    XboxSensorDescription(
        key="gamerscore",
        translation_key="gamerscore",
        icon="mdi:trophy",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_gamerscore,
    ),
    XboxSensorDescription(
        key="signed_in_profiles",
        translation_key="signed_in_profiles",
        icon="mdi:account-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_signed_in_count,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator: XboxAuroraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        XboxAuroraSensor(coordinator, entry, description) for description in SENSORS
    )


class XboxAuroraSensor(XboxAuroraEntity, SensorEntity):
    """A NOVA-backed sensor."""

    entity_description: XboxSensorDescription

    def __init__(
        self,
        coordinator: XboxAuroraCoordinator,
        entry: ConfigEntry,
        description: XboxSensorDescription,
    ) -> None:
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> StateType:
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, StateType] | None:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator.data or {})

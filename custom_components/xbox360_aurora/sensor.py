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
from homeassistant.const import UnitOfInformation, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .coordinator import XboxAuroraCoordinator
from .entity import XboxAuroraEntity


@dataclass(frozen=True, kw_only=True)
class XboxSensorDescription(SensorEntityDescription):
    """Sensor description with a value extractor."""

    value_fn: Callable[[dict], StateType]


def _free_mb(data: dict) -> StateType:
    free = (data.get("memory") or {}).get("free")
    if free is None:
        return None
    return round(free / 1048576, 1)


SENSORS: tuple[XboxSensorDescription, ...] = (
    XboxSensorDescription(
        key="current_title",
        translation_key="current_title",
        icon="mdi:gamepad-variant",
        value_fn=lambda data: (data.get("title") or {}).get("titleid"),
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

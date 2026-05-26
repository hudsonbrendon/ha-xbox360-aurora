"""Image platform for Xbox 360 Aurora — signed-in profile gamerpic."""
from __future__ import annotations

import io

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import XboxAuroraCoordinator
from .entity import build_device_info
from .nova import NovaClient, NovaError  # noqa: F401  (NovaClient referenced for patching)


def _bmp_to_png(data: bytes) -> bytes:
    """Convert BMP bytes to PNG bytes (runs in the executor)."""
    from PIL import Image

    with Image.open(io.BytesIO(data)) as img:
        out = io.BytesIO()
        img.convert("RGB").save(out, format="PNG")
        return out.getvalue()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the gamerpic image entity."""
    coordinator: XboxAuroraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([XboxAuroraGamerpic(hass, coordinator, entry)])


class XboxAuroraGamerpic(CoordinatorEntity[XboxAuroraCoordinator], ImageEntity):
    """The primary signed-in profile's gamerpic."""

    _attr_has_entity_name = True
    _attr_translation_key = "gamerpic"
    _attr_content_type = "image/png"

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: XboxAuroraCoordinator,
        entry: ConfigEntry,
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass, verify_ssl=False)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_gamerpic"
        self._attr_device_info = build_device_info(coordinator, entry)
        self._cached_index: int | None = None

    def _primary_index(self) -> int | None:
        profiles = [
            p for p in (self.coordinator.data or {}).get("profile", []) if p.get("signedin")
        ]
        if not profiles:
            return None
        return min(profiles, key=lambda p: p.get("index", 99)).get("index")

    def _handle_coordinator_update(self) -> None:
        index = self._primary_index()
        if index != self._cached_index:
            self._cached_index = index
            self._attr_image_last_updated = dt_util.utcnow()
        super()._handle_coordinator_update()

    async def async_image(self) -> bytes | None:
        index = self._primary_index()
        if index is None:
            return None
        try:
            raw = await self.coordinator.client.get_profile_image(index)
        except NovaError:
            return None
        if not raw:
            return None
        return await self.hass.async_add_executor_job(_bmp_to_png, raw)

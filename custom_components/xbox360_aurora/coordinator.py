"""Coordinator that polls the NOVA API and shares data with entities."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .nova import NovaClient, NovaError

_LOGGER = logging.getLogger(__name__)


class XboxAuroraCoordinator(DataUpdateCoordinator[dict]):
    """Polls NOVA for title, temperature, and memory."""

    def __init__(self, hass: HomeAssistant, client: NovaClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        """Fetch the latest data. UpdateFailed marks entities unavailable (offline)."""
        try:
            title = await self.client.get_title()
            temperature = await self.client.get_temperature()
            memory = await self.client.get_memory()
        except NovaError as err:
            raise UpdateFailed(f"Error communicating with NOVA: {err}") from err
        return {
            "title": title or {},
            "temperature": temperature or {},
            "memory": memory or {},
        }

"""Coordinator that polls the NOVA API and shares data with entities."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .nova import NovaAuthError, NovaClient, NovaError

_LOGGER = logging.getLogger(__name__)


class XboxAuroraCoordinator(DataUpdateCoordinator[dict]):
    """Polls NOVA for title, temperature, memory, SMC, profile, and bandwidth."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: NovaClient
    ) -> None:
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self.entry = entry
        self.client = client
        self.system: dict = {}

    async def async_load_static(self) -> None:
        """Fetch data that does not change (system info) once at setup."""
        try:
            self.system = await self.client.get_system() or {}
        except NovaError:
            # Non-fatal: device info is enriched best-effort.
            self.system = {}

    async def _async_update_data(self) -> dict:
        """Fetch the latest data. UpdateFailed marks entities unavailable."""
        try:
            title = await self.client.get_title()
            temperature = await self.client.get_temperature()
            memory = await self.client.get_memory()
            smc = await self.client.get_smc()
            profile = await self.client.get_profile()
            bandwidth = await self.client.get_systemlink_bandwidth()
        except NovaAuthError as err:
            raise ConfigEntryAuthFailed("NOVA authentication failed") from err
        except NovaError as err:
            raise UpdateFailed(f"Error communicating with NOVA: {err}") from err
        return {
            "title": title or {},
            "temperature": temperature or {},
            "memory": memory or {},
            "smc": smc or {},
            "profile": profile or [],
            "bandwidth": bandwidth or {},
            "system": self.system,
        }

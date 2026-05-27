"""Coordinator that polls the NOVA API and shares data with entities."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN, EVENT_NOTIFICATION
from .nova import NovaAuthError, NovaClient, NovaError
from .titles import normalize_title_id, resolve_title_name

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
        self.plugin: dict = {}
        self.dashlaunch: dict = {}
        self._last_notification: dict | None = None

    async def async_load_static(self) -> None:
        """Fetch data that does not change (system info, plugin, dashlaunch) once at setup."""
        try:
            self.system = await self.client.get_system() or {}
            self.plugin = await self.client.get_plugin() or {}
            self.dashlaunch = await self.client.get_dashlaunch() or {}
        except NovaError:
            # Non-fatal: device info is enriched best-effort.
            pass

    async def _async_update_data(self) -> dict:
        """Fetch the latest data. UpdateFailed marks entities unavailable."""
        try:
            title = await self.client.get_title()
            temperature = await self.client.get_temperature()
            memory = await self.client.get_memory()
            smc = await self.client.get_smc()
            profile = await self.client.get_profile()
            bandwidth = await self.client.get_systemlink_bandwidth()
            achievement = await self.client.get_achievement()
            achievement_player = await self.client.get_achievement_player()
            screencaptures = await self.client.list_screencaptures()
            notification = await self.client.get_update_notification()
        except NovaAuthError as err:
            raise ConfigEntryAuthFailed("NOVA authentication failed") from err
        except NovaError as err:
            raise UpdateFailed(f"Error communicating with NOVA: {err}") from err
        self._fire_notification_events(notification or {}, title or {})
        return {
            "title": title or {},
            "temperature": temperature or {},
            "memory": memory or {},
            "smc": smc or {},
            "profile": profile or [],
            "bandwidth": bandwidth or {},
            "system": self.system,
            "achievement": achievement or [],
            "achievement_player": achievement_player or [],
            "screencaptures": screencaptures or [],
            "notification": notification or {},
            "plugin": self.plugin,
            "dashlaunch": self.dashlaunch,
        }

    def _fire_notification_events(self, notification: dict, title: dict) -> None:
        """Fire HA events when session activity counters increase."""
        if not notification:
            return
        last = self._last_notification
        self._last_notification = notification
        if last is None:
            return  # establish baseline; don't fire on first poll
        mapping = (
            ("title", "title_launched"),
            ("screencapture", "screenshot_taken"),
            ("profiles", "profile_changed"),
        )
        for key, event_type in mapping:
            if notification.get(key, 0) > last.get(key, 0):
                data = {"type": event_type, "entry_id": self.entry.entry_id}
                if event_type == "title_launched":
                    title_id = title.get("titleid")
                    data["title_id"] = normalize_title_id(title_id)
                    data["title_name"] = resolve_title_name(title_id) or title_id
                self.hass.bus.async_fire(EVENT_NOTIFICATION, data)

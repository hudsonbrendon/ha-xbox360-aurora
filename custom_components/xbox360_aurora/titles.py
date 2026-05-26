"""Resolve Xbox 360 title IDs to human-readable game names.

The bundled ``titles.json`` maps uppercase 8-hex-digit title IDs to game names.
Data derived from https://github.com/wiredopposite/Xbox360-Game-Database.
"""
from __future__ import annotations

import json
from pathlib import Path

from homeassistant.core import HomeAssistant

_TITLES_PATH = Path(__file__).parent / "titles.json"
_TITLES: dict[str, str] | None = None


def _load_from_disk() -> dict[str, str]:
    """Read and normalize the bundled title map (blocking — call in executor)."""
    try:
        with _TITLES_PATH.open(encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, ValueError):
        return {}
    return {str(key).upper(): str(value) for key, value in data.items()}


async def async_load_titles(hass: HomeAssistant) -> None:
    """Load the title map once into the module cache, off the event loop."""
    global _TITLES
    if _TITLES is None:
        _TITLES = await hass.async_add_executor_job(_load_from_disk)


def normalize_title_id(title_id: str | None) -> str | None:
    """Return an uppercase hex title ID without any ``0x`` prefix, or None."""
    if not title_id:
        return None
    value = str(title_id).strip()
    if value[:2].lower() == "0x":
        value = value[2:]
    value = value.upper()
    return value or None


def resolve_title_name(title_id: str | None) -> str | None:
    """Return the game name for a title ID, or None if unknown/not loaded."""
    normalized = normalize_title_id(title_id)
    if not normalized or not _TITLES:
        return None
    return _TITLES.get(normalized)

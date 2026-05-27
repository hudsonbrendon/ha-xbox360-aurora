"""Tests for xbox360_aurora_event automation events fired by the coordinator."""
from unittest.mock import AsyncMock

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
)

from custom_components.xbox360_aurora.const import (
    CONF_FTP_PASSWORD,
    CONF_FTP_PORT,
    CONF_FTP_USERNAME,
    DOMAIN,
    EVENT_NOTIFICATION,
)

ENTRY_DATA = {
    CONF_HOST: "1.2.3.4",
    CONF_PORT: 9999,
    CONF_USERNAME: "xboxhttp",
    CONF_PASSWORD: "xboxhttp",
    CONF_FTP_PORT: 21,
    CONF_FTP_USERNAME: "xboxftp",
    CONF_FTP_PASSWORD: "xboxftp",
}

TITLE_PAYLOAD = {"titleid": "DEADBEEF", "path": r"Hdd1:\Games\X"}


async def test_title_launched_event(hass: HomeAssistant, mock_nova):
    """Event fires when title counter increases; no event on first poll (baseline)."""
    # First poll will return notification counter=1 (establishes baseline)
    mock_nova["get_title"].return_value = TITLE_PAYLOAD
    mock_nova["get_update_notification"].return_value = {
        "title": 1,
        "screencapture": 0,
        "profiles": 0,
    }

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=ENTRY_DATA,
        unique_id="1.2.3.4:9999",
        title="Xbox 360 (1.2.3.4)",
    )
    entry.add_to_hass(hass)

    # Capture events BEFORE setup so we don't miss anything
    events = async_capture_events(hass, EVENT_NOTIFICATION)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # No event should have fired on the first poll (baseline establishment)
    assert len(events) == 0

    # Get coordinator from hass.data
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Second poll: title counter increases from 1 → 2
    mock_nova["get_update_notification"].return_value = {
        "title": 2,
        "screencapture": 0,
        "profiles": 0,
    }

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Now exactly one event should have fired
    assert len(events) == 1
    event_data = events[0].data
    assert event_data["type"] == "title_launched"
    assert event_data["entry_id"] == entry.entry_id
    assert event_data["title_id"] == "DEADBEEF"


async def test_no_event_when_counter_unchanged(hass: HomeAssistant, mock_nova):
    """No event fires when notification counters stay the same."""
    mock_nova["get_update_notification"].return_value = {
        "title": 3,
        "screencapture": 2,
        "profiles": 1,
    }

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=ENTRY_DATA,
        unique_id="1.2.3.4:9999",
        title="Xbox 360 (1.2.3.4)",
    )
    entry.add_to_hass(hass)
    events = async_capture_events(hass, EVENT_NOTIFICATION)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Baseline established — no events
    assert len(events) == 0

    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Counters unchanged on second poll
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(events) == 0


async def test_screenshot_taken_event(hass: HomeAssistant, mock_nova):
    """screenshot_taken event fires when screencapture counter increases."""
    mock_nova["get_update_notification"].return_value = {
        "title": 0,
        "screencapture": 0,
        "profiles": 0,
    }

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=ENTRY_DATA,
        unique_id="1.2.3.4:9999",
        title="Xbox 360 (1.2.3.4)",
    )
    entry.add_to_hass(hass)
    events = async_capture_events(hass, EVENT_NOTIFICATION)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(events) == 0

    coordinator = hass.data[DOMAIN][entry.entry_id]

    mock_nova["get_update_notification"].return_value = {
        "title": 0,
        "screencapture": 1,
        "profiles": 0,
    }

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["type"] == "screenshot_taken"


async def test_empty_notification_fires_no_event(hass: HomeAssistant, mock_nova):
    """Empty notification dict does not cause any events."""
    # Default mock already returns {} for get_update_notification

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=ENTRY_DATA,
        unique_id="1.2.3.4:9999",
        title="Xbox 360 (1.2.3.4)",
    )
    entry.add_to_hass(hass)
    events = async_capture_events(hass, EVENT_NOTIFICATION)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(events) == 0

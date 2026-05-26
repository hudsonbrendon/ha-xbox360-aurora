"""Tests for sensor entities."""
from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.xbox360_aurora.const import (
    CONF_FTP_PASSWORD,
    CONF_FTP_PORT,
    CONF_FTP_USERNAME,
    DOMAIN,
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


async def test_sensors_expose_nova_values(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=ENTRY_DATA,
        unique_id="1.2.3.4:9999",
        title="Xbox 360 (1.2.3.4)",
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.xbox360_aurora.NovaClient.authenticate",
        new=AsyncMock(return_value="tok"),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_title",
        new=AsyncMock(return_value={"titleid": "DEADBEEF"}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature",
        new=AsyncMock(
            return_value={"cpu": 50, "gpu": 55, "case": 40, "memory": 45, "celsius": True}
        ),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_memory",
        new=AsyncMock(return_value={"free": 104857600, "used": 200, "total": 300}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_system",
        new=AsyncMock(return_value={}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_smc",
        new=AsyncMock(return_value={}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_profile",
        new=AsyncMock(return_value=[]),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_systemlink_bandwidth",
        new=AsyncMock(return_value={}),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.xbox_360_1_2_3_4_current_title").state == "DEADBEEF"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_cpu_temperature").state == "50"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_gpu_temperature").state == "55"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_free_ram").state == "100.0"


async def test_current_title_resolves_game_name(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=ENTRY_DATA,
        unique_id="1.2.3.4:9999",
        title="Xbox 360 (1.2.3.4)",
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.xbox360_aurora.NovaClient.authenticate",
        new=AsyncMock(return_value="tok"),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_title",
        new=AsyncMock(return_value={"titleid": "0x415608C3"}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature",
        new=AsyncMock(
            return_value={"cpu": 50, "gpu": 55, "case": 40, "memory": 45, "celsius": True}
        ),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_memory",
        new=AsyncMock(return_value={"free": 104857600, "used": 200, "total": 300}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_system",
        new=AsyncMock(return_value={}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_smc",
        new=AsyncMock(return_value={}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_profile",
        new=AsyncMock(return_value=[]),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_systemlink_bandwidth",
        new=AsyncMock(return_value={}),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.xbox_360_1_2_3_4_current_title")
    assert state.state == "Call of Duty: Black Ops II"
    assert state.attributes["title_id"] == "415608C3"


async def test_memory_and_memory_temp_sensors(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN, data=ENTRY_DATA, unique_id="1.2.3.4:9999", title="Xbox 360 (1.2.3.4)"
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.xbox360_aurora.NovaClient.authenticate", new=AsyncMock(return_value="tok")
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_title", new=AsyncMock(return_value={"titleid": "DEADBEEF"})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature",
        new=AsyncMock(return_value={"cpu": 50, "gpu": 55, "case": 40, "memory": 45, "celsius": True}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_memory",
        new=AsyncMock(return_value={"free": 50, "used": 150, "total": 200}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_system", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_smc", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_profile", new=AsyncMock(return_value=[])
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_systemlink_bandwidth", new=AsyncMock(return_value={})
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.xbox_360_1_2_3_4_used_ram").state == "0.0"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_total_ram").state == "0.0"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_ram_usage").state == "75.0"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_memory_temperature").state == "45"


async def test_smc_sensors(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN, data=ENTRY_DATA, unique_id="1.2.3.4:9999", title="Xbox 360 (1.2.3.4)"
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.xbox360_aurora.NovaClient.authenticate", new=AsyncMock(return_value="tok")
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_title", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_memory", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_system", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_smc",
        new=AsyncMock(return_value={"avpack": 1, "traystate": 4, "tiltstate": 0, "smcversion": "2.3"}),
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_profile", new=AsyncMock(return_value=[])
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_systemlink_bandwidth", new=AsyncMock(return_value={})
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.xbox_360_1_2_3_4_disc_tray").state == "closed"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_video_output").state == "hdmi"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_orientation").state == "vertical"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_smc_version").state == "2.3"


async def test_system_sensors(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN, data=ENTRY_DATA, unique_id="1.2.3.4:9999", title="Xbox 360 (1.2.3.4)"
    )
    entry.add_to_hass(hass)
    system = {
        "console": {"motherboard": "Jasper", "type": "Retail"},
        "consoleid": "ABCDEF123456",
        "serial": "123456789012",
        "version": {"major": 2, "minor": 0, "build": 17559, "qfe": 0},
    }
    with patch(
        "custom_components.xbox360_aurora.NovaClient.authenticate", new=AsyncMock(return_value="tok")
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_title", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_memory", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_system", new=AsyncMock(return_value=system)
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_smc", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_profile", new=AsyncMock(return_value=[])
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_systemlink_bandwidth", new=AsyncMock(return_value={})
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.xbox_360_1_2_3_4_motherboard").state == "Jasper"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_console_type").state == "Retail"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_dashboard_version").state == "2.0.17559.0"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_serial_number").state == "123456789012"


async def test_profile_sensors(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN, data=ENTRY_DATA, unique_id="1.2.3.4:9999", title="Xbox 360 (1.2.3.4)"
    )
    entry.add_to_hass(hass)
    profiles = [
        {"gamertag": "Hudson", "gamerscore": 1234, "signedin": 1, "index": 0},
        {"gamertag": "Player2", "gamerscore": 50, "signedin": 1, "index": 1},
        {"gamertag": "", "gamerscore": 0, "signedin": 0, "index": 2},
    ]
    with patch(
        "custom_components.xbox360_aurora.NovaClient.authenticate", new=AsyncMock(return_value="tok")
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_title", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_memory", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_system", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_smc", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_profile", new=AsyncMock(return_value=profiles)
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_systemlink_bandwidth", new=AsyncMock(return_value={})
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.xbox_360_1_2_3_4_gamertag").state == "Hudson"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_gamerscore").state == "1234"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_signed_in_profiles").state == "2"


async def test_bandwidth_sensors(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN, data=ENTRY_DATA, unique_id="1.2.3.4:9999", title="Xbox 360 (1.2.3.4)"
    )
    entry.add_to_hass(hass)
    bw = {"rate": {"downstream": 2048.0, "upstream": 1024.0}, "bytes": {"downstream": 1048576, "upstream": 524288}}
    with patch(
        "custom_components.xbox360_aurora.NovaClient.authenticate", new=AsyncMock(return_value="tok")
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_title", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_temperature", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_memory", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_system", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_smc", new=AsyncMock(return_value={})
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_profile", new=AsyncMock(return_value=[])
    ), patch(
        "custom_components.xbox360_aurora.coordinator.NovaClient.get_systemlink_bandwidth", new=AsyncMock(return_value=bw)
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.xbox_360_1_2_3_4_network_download").state == "2048.0"
    assert hass.states.get("sensor.xbox_360_1_2_3_4_network_upload").state == "1024.0"

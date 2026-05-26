"""Tests for the gamerpic image entity."""
import io
from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from PIL import Image
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


def _bmp_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (0, 128, 0)).save(buf, format="BMP")
    return buf.getvalue()


async def test_gamerpic_serves_png(hass: HomeAssistant, mock_nova):
    mock_nova["get_profile"].return_value = [
        {"gamertag": "Hudson", "gamerscore": 100, "signedin": 1, "index": 0}
    ]
    entry = MockConfigEntry(
        domain=DOMAIN, data=ENTRY_DATA, unique_id="1.2.3.4:9999", title="Xbox 360 (1.2.3.4)"
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.xbox360_aurora.image.NovaClient.get_profile_image",
        new=AsyncMock(return_value=_bmp_bytes()),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("image.xbox_360_1_2_3_4_gamerpic")
        assert state is not None

        coordinator = hass.data[DOMAIN][entry.entry_id]
        ent = next(
            e for e in hass.data["entity_components"]["image"].entities
            if e.unique_id == f"{entry.entry_id}_gamerpic"
        )
        png = await ent.async_image()
    assert png is not None and png[:4] == b"\x89PNG"

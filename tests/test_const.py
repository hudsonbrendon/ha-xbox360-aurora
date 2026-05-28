"""Sanity tests for constants."""
from custom_components.xbox360_aurora.const import (
    DOMAIN,
    PLATFORMS,
    DEFAULT_NOVA_PORT,
    DEFAULT_FTP_PORT,
)


def test_domain_value():
    assert DOMAIN == "xbox360_aurora"


def test_default_ports():
    assert DEFAULT_NOVA_PORT == 9999
    assert DEFAULT_FTP_PORT == 21


def test_platforms_registered():
    assert len(PLATFORMS) == 5


def test_image_platform_registered():
    from homeassistant.const import Platform
    from custom_components.xbox360_aurora.const import PLATFORMS

    assert Platform.IMAGE in PLATFORMS
    assert len(PLATFORMS) == 5


def test_switch_platform_and_new_consts():
    from homeassistant.const import Platform

    from custom_components.xbox360_aurora.const import (
        CONF_SCAN_INTERVAL,
        MAX_SCAN_INTERVAL,
        MIN_SCAN_INTERVAL,
        PLATFORMS,
    )
    from xbox360_nova import FTP_CMD_RESTART

    assert Platform.SWITCH in PLATFORMS
    assert CONF_SCAN_INTERVAL == "scan_interval"
    assert FTP_CMD_RESTART == "RESTART"
    assert MIN_SCAN_INTERVAL < MAX_SCAN_INTERVAL

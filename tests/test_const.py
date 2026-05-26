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
    assert len(PLATFORMS) == 3

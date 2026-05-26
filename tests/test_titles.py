"""Tests for the title ID -> game name resolver."""
from custom_components.xbox360_aurora import titles


def test_normalize_title_id():
    assert titles.normalize_title_id("0x415608C3") == "415608C3"
    assert titles.normalize_title_id("415608c3") == "415608C3"
    assert titles.normalize_title_id(" 0X415608c3 ") == "415608C3"
    assert titles.normalize_title_id(None) is None
    assert titles.normalize_title_id("") is None


def test_bundled_database_loads():
    db = titles._load_from_disk()
    assert len(db) > 1000
    assert db["415608C3"] == "Call of Duty: Black Ops II"


def test_resolve_known_title():
    titles._TITLES = titles._load_from_disk()
    assert titles.resolve_title_name("0x415608C3") == "Call of Duty: Black Ops II"
    assert titles.resolve_title_name("415608c3") == "Call of Duty: Black Ops II"


def test_resolve_unknown_returns_none():
    titles._TITLES = titles._load_from_disk()
    assert titles.resolve_title_name("DEADBEEF") is None
    assert titles.resolve_title_name(None) is None

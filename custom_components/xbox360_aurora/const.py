"""Constants for the Xbox 360 Aurora integration."""
from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "xbox360_aurora"

# Config entry keys (host/username/password reuse homeassistant.const CONF_* keys)
CONF_FTP_PORT = "ftp_port"
CONF_FTP_USERNAME = "ftp_username"
CONF_FTP_PASSWORD = "ftp_password"

# Defaults
DEFAULT_NOVA_PORT = 9999
DEFAULT_NOVA_USERNAME = "xboxhttp"
DEFAULT_NOVA_PASSWORD = "xboxhttp"
DEFAULT_FTP_PORT = 21
DEFAULT_FTP_USERNAME = "xboxftp"
DEFAULT_FTP_PASSWORD = "xboxftp"

DEFAULT_SCAN_INTERVAL = 30

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.IMAGE,
    Platform.SENSOR,
    Platform.SWITCH,
]

CONF_SCAN_INTERVAL = "scan_interval"
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 600

# launch_title service
SERVICE_LAUNCH_TITLE = "launch_title"
ATTR_EXEC = "exec"
ATTR_PATH = "path"
ATTR_TYPE = "type"

# Events
EVENT_NOTIFICATION = f"{DOMAIN}_event"

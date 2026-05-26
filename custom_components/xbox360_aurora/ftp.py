"""Blocking FTP helper for Aurora SITE commands (no Home Assistant imports).

Run via hass.async_add_executor_job — ftplib is synchronous.
"""
from __future__ import annotations

import ftplib


class FtpError(Exception):
    """Raised when an FTP SITE command fails."""


def site_command(
    host: str,
    port: int,
    username: str,
    password: str,
    command: str,
    timeout: float = 10.0,
) -> str:
    """Connect to the Aurora FTP server and run `SITE <command>`.

    Returns the server's response line. Raises FtpError on any failure.
    """
    try:
        with ftplib.FTP(timeout=timeout) as ftp:
            ftp.connect(host, port)
            ftp.login(username, password)
            return ftp.sendcmd(f"SITE {command}")
    except ftplib.all_errors as err:  # includes OSError, EOFError, ftplib.Error
        raise FtpError(str(err)) from err

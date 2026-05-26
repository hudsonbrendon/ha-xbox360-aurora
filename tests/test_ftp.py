"""Tests for the FTP SITE command helper."""
import ftplib
from unittest.mock import MagicMock, patch

import pytest

from custom_components.xbox360_aurora.ftp import site_command, FtpError


def test_site_command_logs_in_and_sends_site_prefix():
    fake_ftp = MagicMock()
    fake_ftp.sendcmd.return_value = "200 Rebooting"
    with patch("custom_components.xbox360_aurora.ftp.ftplib.FTP") as ftp_cls:
        ftp_cls.return_value.__enter__.return_value = fake_ftp
        result = site_command("1.2.3.4", 21, "xboxftp", "xboxftp", "REBOOT")

    fake_ftp.connect.assert_called_once_with("1.2.3.4", 21)
    fake_ftp.login.assert_called_once_with("xboxftp", "xboxftp")
    fake_ftp.sendcmd.assert_called_once_with("SITE REBOOT")
    assert result == "200 Rebooting"


def test_site_command_wraps_ftp_errors():
    with patch("custom_components.xbox360_aurora.ftp.ftplib.FTP") as ftp_cls:
        ftp_cls.return_value.__enter__.side_effect = OSError("connection refused")
        with pytest.raises(FtpError):
            site_command("1.2.3.4", 21, "xboxftp", "xboxftp", "SHUTDOWN")

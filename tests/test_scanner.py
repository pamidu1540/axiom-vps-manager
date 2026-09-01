"""
Unit tests for Axiom security audit scanner
"""

import os
import sys
from unittest.mock import mock_open, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from axiom.security.scanner import SecurityScanner


def test_scanner_runs():
    res = SecurityScanner.audit_system()
    assert "overall_status" in res
    assert "findings" in res
    assert isinstance(res["findings"], list)
    assert "firewall_status" in res


def test_scanner_detects_plaintext_passwords():
    with patch("os.path.exists") as mock_exists, patch("os.listdir") as mock_listdir:
        mock_exists.side_effect = lambda p: p == "/etc/VPSManager/senha"
        mock_listdir.return_value = ["user1", "user2"]

        res = SecurityScanner.audit_system()
        assert res["overall_status"] in ("WARNING", "FAILED")
        assert any(f["title"] == "Plaintext Password Directory Found" for f in res["findings"])


def test_scanner_detects_exposed_webroot_backup():
    with patch("os.path.exists") as mock_exists:
        mock_exists.side_effect = lambda p: p == "/var/www/html/backup/backup.vps"

        res = SecurityScanner.audit_system()
        assert res["overall_status"] == "FAILED"
        assert any("Webroot" in f["title"] for f in res["findings"])


def test_scanner_detects_root_ssh_login():
    sshd_content = "Port 22\nPermitRootLogin yes\nPasswordAuthentication yes\n"
    with (
        patch("os.path.exists", side_effect=lambda p: p == "/etc/ssh/sshd_config"),
        patch("builtins.open", mock_open(read_data=sshd_content)),
    ):
        res = SecurityScanner.audit_system()
        assert any("Root Password Login" in f["title"] for f in res["findings"])


def test_scanner_detects_static_key():
    with patch("os.path.exists") as mock_exists:
        mock_exists.side_effect = lambda p: p == "/stunnel.pem"

        res = SecurityScanner.audit_system()
        assert any("Static RSA Key Found" in f["title"] for f in res["findings"])

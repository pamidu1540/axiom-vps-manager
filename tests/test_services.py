"""
Unit tests for Axiom tunneling and proxy services
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from axiom.services.hysteria import HysteriaService
from axiom.services.singbox import SingboxService
from axiom.services.xray import XrayService


def test_xray_reality_generation():
    xray = XrayService(port=443)
    config = xray.generate_reality_config(
        clients=[{"uuid": "12345678-1234-1234-1234-123456789abc"}], private_key="test_priv_key", short_id="01234567"
    )
    assert config["inbounds"][0]["port"] == 443
    assert config["inbounds"][0]["streamSettings"]["security"] == "reality"

    uri = xray.generate_client_uri("12345678-1234-1234-1234-123456789abc", "1.2.3.4", "pubkey", "01234567")
    assert uri.startswith("vless://")
    assert "security=reality" in uri


def test_hysteria_config():
    hy2 = HysteriaService(port=8443, up_mbps=50, down_mbps=100)
    cfg = hy2.generate_server_config(auth_passwords=["secret_pw"])
    assert cfg["listen"] == ":8443"
    assert cfg["auth"]["password"] == "secret_pw"
    assert cfg["bandwidth"]["up"] == "50 mbps"


def test_singbox_config():
    sb = SingboxService(clash_api_port=9090)
    cfg = sb.generate_unified_config()
    assert "inbounds" in cfg
    assert "outbounds" in cfg
    assert cfg["experimental"]["clash_api"]["external_controller"] == "127.0.0.1:9090"

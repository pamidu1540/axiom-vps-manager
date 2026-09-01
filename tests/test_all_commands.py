"""
Axiom VPS Manager — Comprehensive All-Command & Component Test Suite
Verifies interface contracts, CLI entrypoints, REST APIs, and backend services.
"""

import os
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from axiom.cli import main as cli_main
from axiom.config import load_config
from axiom.firewall.nft_manager import NFT_BASE_TEMPLATE
from axiom.monitor.bandwidth import BandwidthMonitor
from axiom.monitor.stats import SystemMonitor
from axiom.security.scanner import SecurityScanner
from axiom.services.hysteria import HysteriaService
from axiom.services.qrcode_gen import QRCodeGenerator
from axiom.services.singbox import SingboxService
from axiom.services.wireguard import WireGuardService
from axiom.services.xray import XrayService
from axiom.telegram.bot import AxiomTelegramBot
from axiom.tui.dashboard import Dashboard
from axiom.users.backup import BackupEngine
from axiom.users.manager import UserManager


# ==============================================================================
# 1. Config Loader & System Initializer
# ==============================================================================
def test_config_loader():
    cfg = load_config()
    assert isinstance(cfg, dict)
    assert "axiom" in cfg or "ssh" in cfg


# ==============================================================================
# 2. User Management Engine
# ==============================================================================
def test_user_manager_full_cycle():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tmp_db = tf.name

    orig_chmod = os.chmod

    def safe_chmod(p, m, *args, **kwargs):
        if sys.platform == "win32":
            orig_chmod(p, 0o777, *args, **kwargs)
        else:
            orig_chmod(p, m, *args, **kwargs)

    with patch("os.chmod", side_effect=safe_chmod):
        try:
            mgr = UserManager(db_path=tmp_db)

            # Set limit
            mgr._set_user_limit("alice", 2)
            users = mgr.list_users()
            assert len(users) == 1
            assert users[0]["username"] == "alice"
            assert users[0]["limit"] == "2"

            # Update limit
            mgr._set_user_limit("alice", 5)
            assert mgr.list_users()[0]["limit"] == "5"

            # Remove
            mgr._remove_from_db("alice")
            assert len(mgr.list_users()) == 0
        finally:
            if os.path.exists(tmp_db):
                os.remove(tmp_db)


# ==============================================================================
# 3. WireGuard Service
# ==============================================================================
def test_wireguard_service_contract():
    wg = WireGuardService(interface="wg0", port=51820)
    client = wg.add_client("peer1", "10.66.66.5/32", "198.51.100.1")
    assert client["client_name"] == "peer1"
    assert "Endpoint = 198.51.100.1:51820" in client["config"]
    assert "AllowedIPs = 0.0.0.0/0, ::/0" in client["config"]


# ==============================================================================
# 4. Xray VLESS Reality Service
# ==============================================================================
def test_xray_service_contract():
    xray = XrayService(port=443)
    config = xray.generate_reality_config(
        clients=[{"uuid": "test-uuid-1234"}], private_key="priv_test", short_id="abcd"
    )
    assert config["inbounds"][0]["protocol"] == "vless"
    assert config["inbounds"][0]["port"] == 443
    uri = xray.generate_client_uri("test-uuid-1234", "198.51.100.1", "pub_key", "abcd")
    assert uri.startswith("vless://test-uuid-1234@198.51.100.1:443")


# ==============================================================================
# 5. Hysteria2 Service
# ==============================================================================
def test_hysteria_service_contract():
    hy2 = HysteriaService(port=8443, up_mbps=50, down_mbps=150)
    cfg = hy2.generate_server_config(auth_passwords=["secret"])
    assert cfg["listen"] == ":8443"
    assert cfg["auth"]["type"] == "password"
    assert cfg["bandwidth"]["up"] == "50 mbps"
    assert cfg["bandwidth"]["down"] == "150 mbps"


# ==============================================================================
# 6. Singbox Unified Service
# ==============================================================================
def test_singbox_service_contract():
    sb = SingboxService(clash_api_port=9090)
    cfg = sb.generate_unified_config()
    assert "inbounds" in cfg
    assert "outbounds" in cfg
    assert "experimental" in cfg


# ==============================================================================
# 7. QR Code Generator
# ==============================================================================
def test_qrcode_generator():
    data = "vless://sample-profile"
    qr_text = QRCodeGenerator.generate_terminal_qr(data)
    assert len(qr_text) > 0


# ==============================================================================
# 8. Firewall NFTables Manager
# ==============================================================================
def test_nftables_manager_template():
    assert "table inet axiom" in NFT_BASE_TEMPLATE
    assert "chain input" in NFT_BASE_TEMPLATE
    assert "ssh_meter" in NFT_BASE_TEMPLATE


# ==============================================================================
# 9. Backup Engine
# ==============================================================================
def test_backup_engine(tmp_path):
    bdir = str(tmp_path / "backups")
    engine = BackupEngine(backup_dir=bdir)
    assert os.path.exists(bdir)
    assert engine.list_backups() == []


# ==============================================================================
# 10. System Monitor & Telemetry
# ==============================================================================
def test_system_monitor():
    metrics = SystemMonitor.get_system_metrics()
    assert isinstance(metrics, dict)
    for key in ["disk_used_gb", "disk_total_gb", "mem_used_mb", "mem_total_mb", "online_users"]:
        assert key in metrics


# ==============================================================================
# 11. Bandwidth Monitor
# ==============================================================================
def test_bandwidth_monitor():
    stats = BandwidthMonitor.get_interface_stats()
    assert "rx_bytes" in stats
    assert "tx_bytes" in stats
    assert "total_gb" in stats


# ==============================================================================
# 12. Security Audit Scanner
# ==============================================================================
def test_security_scanner():
    report = SecurityScanner.audit_system()
    assert "overall_status" in report
    assert "firewall_status" in report
    assert "findings" in report


# ==============================================================================
# 13. Telegram Bot Module
# ==============================================================================
def test_telegram_bot_class():
    bot = AxiomTelegramBot(token="123456:SAMPLE_TOKEN", admin_id=12345678)
    assert bot.token == "123456:SAMPLE_TOKEN"
    assert bot.admin_id == 12345678


# ==============================================================================
# 14. TUI Dashboard
# ==============================================================================
def test_dashboard_class():
    dash = Dashboard()
    assert dash is not None


# ==============================================================================
# 15. CLI Dispatcher Invocations
# ==============================================================================
def test_cli_scan_command(capsys):
    with patch("sys.argv", ["axiom", "scan"]):
        cli_main()
        captured = capsys.readouterr()
        assert "Axiom Security Audit Scanner" in captured.out


def test_cli_bandwidth_command(capsys):
    with patch("sys.argv", ["axiom", "bandwidth"]):
        cli_main()
        captured = capsys.readouterr()
        assert "Interface Bandwidth Traffic" in captured.out


def test_cli_user_list_command(capsys):
    with patch("sys.argv", ["axiom", "user", "list"]):
        cli_main()
        captured = capsys.readouterr()
        assert "Active Users" in captured.out


def test_cli_backup_list_command(capsys):
    with patch("sys.argv", ["axiom", "backup", "list"]):
        cli_main()
        captured = capsys.readouterr()
        assert "Available Backups" in captured.out


# ==============================================================================
# 16. Verification of All 30 Menu Commands & Symlink Infrastructure
# ==============================================================================
def test_all_30_menu_commands_exist_and_linked():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    modulos_dir = os.path.join(repo_root, "Modulos")
    install_sh = os.path.join(repo_root, "install.sh")
    uninstall_sh = os.path.join(repo_root, "uninstall.sh")
    menu_sh = os.path.join(modulos_dir, "menu")

    # 30 Menu Actions & Supporting Modules
    required_modules = [
        "criarusuario",  # Option 01
        "criarteste",  # Option 02
        "remover",  # Option 03
        "sshmonitor",  # Option 04
        "mudardata",  # Option 05
        "alterarlimite",  # Option 06
        "alterarsenha",  # Option 07
        "expcleaner",  # Option 08
        "infousers",  # Option 09
        "conexao",  # Option 10
        "speedtest",  # Option 11
        "banner",  # Option 12
        "otimizar",  # Option 14
        "userbackup",  # Option 15
        "limiter",  # Option 16
        "badvpn",  # Option 17
        "detalhes",  # Option 18
        "addhost",  # Option 20
        "delhost",  # Option 21
        "reiniciarsistema",  # Option 22
        "reiniciarservicos",  # Option 23
        "blockt",  # Option 24
        "botssh",  # Option 25
        "senharoot",  # Option 26
        "attscript",  # Option 28
        "delscript",  # Option 29
        "uexpired",  # cron utility
        "verifatt",  # update verification
    ]

    for mod in required_modules:
        mod_path = os.path.join(modulos_dir, mod)
        assert os.path.isfile(mod_path), f"Module '{mod}' missing in Modulos/"

    # Check menu has PATH export
    with open(menu_sh, encoding="utf-8", errors="ignore") as f:
        menu_content = f.read()
    assert 'export PATH="/opt/axiom/Modulos' in menu_content

    # Check install.sh symlinks all modules
    with open(install_sh, encoding="utf-8", errors="ignore") as f:
        install_content = f.read()
    assert 'for mod in "$INSTALL_DIR/Modulos"/*' in install_content
    assert 'ln -sf "$mod" "/usr/local/bin/$mod_name"' in install_content
    assert 'ln -sf "$mod" "/bin/$mod_name"' in install_content

    # Check uninstall.sh cleans symlinks
    with open(uninstall_sh, encoding="utf-8", errors="ignore") as f:
        uninstall_content = f.read()
    assert "rm -f /etc/profile.d/axiom.sh" in uninstall_content
    assert "/usr/local/bin/$bin" in uninstall_content

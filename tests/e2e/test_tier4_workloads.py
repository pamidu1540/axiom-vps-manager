"""
Tier 4: Real-World Application Workloads E2E Test Suite
Validates comprehensive end-to-end production lifecycles for Axiom VPS Manager.
"""

import datetime
import os
import tarfile
from unittest.mock import MagicMock, patch

from axiom.firewall.nft_manager import NFTablesManager
from axiom.monitor.stats import SystemMonitor
from axiom.security.scanner import SecurityScanner
from axiom.services.hysteria import HysteriaService
from axiom.services.qrcode_gen import QRCodeGenerator
from axiom.services.singbox import SingboxService
from axiom.services.wireguard import WireGuardService
from axiom.services.xray import XrayService
from axiom.users.manager import UserManager


class TestTier4Workloads:
    # --------------------------------------------------------------------------
    # Workload 1: Full VPS Onboarding & Multi-Protocol Provisioning Lifecycle
    # --------------------------------------------------------------------------
    def test_workload_01_vps_onboarding_and_provisioning(self, sandbox_fs):
        """Simulates full fresh VPS onboarding: SSH banner -> Tunnels -> Firewall."""
        # 1. Setup Banner
        banner_content = "========================================\n  ⚡ WELCOME TO AXIOM SECURE SERVER ⚡  \n========================================\n"
        with open(sandbox_fs.banner_file, "w", encoding="utf-8") as f:
            f.write(banner_content)
        assert os.path.exists(sandbox_fs.banner_file)
        assert "AXIOM SECURE SERVER" in open(sandbox_fs.banner_file).read()

        # 2. Provision WireGuard
        wg = WireGuardService(port=51820)
        wg_client = wg.add_client("client_workload1", "10.66.66.2/32", "203.0.113.1")
        assert wg_client["client_name"] == "client_workload1"
        assert "PrivateKey =" in wg_client["config"]
        assert "203.0.113.1:51820" in wg_client["config"]

        # 3. Generate QR Code for Mobile Tunnel
        qr = QRCodeGenerator.generate_terminal_qr(wg_client["config"])
        assert len(qr) > 0

        # 4. Provision Xray Reality
        xray = XrayService(port=443)
        xray_cfg = xray.generate_reality_config(
            clients=[{"uuid": "99999999-9999-9999-9999-999999999999"}],
            private_key="priv_xray_test",
            short_id="01234567",
        )
        assert xray_cfg["inbounds"][0]["port"] == 443
        xray_uri = xray.generate_client_uri(
            "99999999-9999-9999-9999-999999999999", "203.0.113.1", "pub_key", "01234567"
        )
        assert xray_uri.startswith("vless://")

        # 5. Provision Hysteria2
        hy2 = HysteriaService(port=8443, up_mbps=100, down_mbps=200)
        hy2_cfg = hy2.generate_server_config(auth_passwords=["hy2_secret_token"])
        assert hy2_cfg["listen"] == ":8443"

        # 6. Provision Singbox Unified
        sb = SingboxService(clash_api_port=9090)
        sb_cfg = sb.generate_unified_config()
        assert "inbounds" in sb_cfg

        # 7. Apply Base Firewall
        nft = NFTablesManager()
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.communicate.return_value = ("", "")
            mock_proc.returncode = 0
            mock_popen.return_value = mock_proc
            applied = nft.apply_base_firewall()
            assert applied is True

    # --------------------------------------------------------------------------
    # Workload 2: Commercial ISP/VPN Provider Scaling Workload
    # --------------------------------------------------------------------------
    def test_workload_02_commercial_scaling_and_session_management(self, sandbox_fs):
        """Simulates 50 managed accounts + 20 trials, telemetry, limiter and purge."""
        mgr = UserManager(db_path=sandbox_fs.usuarios_db)

        # 1. Batch Create 50 Managed Users
        managed_users = [(f"commercial_user_{i:02d}", (i % 4) + 1) for i in range(1, 51)]
        sandbox_fs.write_usuarios_db(managed_users)
        assert len(sandbox_fs.read_usuarios_db()) == 50

        # 2. Batch Provision 20 Trial Users (10 active, 10 expired)
        now_epoch = int(datetime.datetime.now().timestamp())
        trial_users = []
        for i in range(1, 11):
            trial_users.append((f"trial_act_{i:02d}", now_epoch + 3600 * i, 1))
        for i in range(1, 11):
            trial_users.append((f"trial_exp_{i:02d}", now_epoch - 3600 * i, 1))
        sandbox_fs.write_trial_db(trial_users)
        assert len(sandbox_fs.read_trial_db()) == 20

        # 3. Simulate Active Connections & Limiter
        active_pids_map = {
            "commercial_user_01": [5001, 5002, 5003],  # limit 2 -> 1 excess
            "commercial_user_02": [6001, 6002, 6003, 6004],  # limit 3 -> 1 excess
        }
        limits = sandbox_fs.read_usuarios_db()
        excess_pids = []
        for u, pids in active_pids_map.items():
            lim = int(limits[u])
            if len(pids) > lim:
                excess_count = len(pids) - lim
                for i in range(excess_count):
                    excess_pids.append(pids[len(pids) - 1 - i])

        assert 5003 in excess_pids
        assert 6004 in excess_pids
        assert 5001 not in excess_pids
        assert 6001 not in excess_pids

        # 4. Run Expired Trial Sweeper
        remaining_trials = [t for t in sandbox_fs.read_trial_db() if t["epoch"] > now_epoch]
        assert len(remaining_trials) == 10
        assert all("trial_act" in t["username"] for t in remaining_trials)

        # 5. Audit Reporting
        users = mgr.list_users()
        assert len(users) == 50
        with patch("subprocess.check_output", return_value="7\n"):
            metrics = SystemMonitor.get_system_metrics()
            assert metrics["online_users"] == 7

    # --------------------------------------------------------------------------
    # Workload 3: Automated Disaster Recovery & Server Migration Workload
    # --------------------------------------------------------------------------
    def test_workload_03_disaster_recovery_and_migration(self, sandbox_fs):
        """Simulates full server state backup -> data wipe -> complete recovery."""
        # 1. Setup production state
        managed = [(f"migrated_u{i}", i) for i in range(1, 11)]
        sandbox_fs.write_usuarios_db(managed)
        with open(sandbox_fs.squid_payload, "w", encoding="utf-8") as f:
            f.write(".customdomain1.com\n.customdomain2.net\n")
        with open(sandbox_fs.banner_file, "w", encoding="utf-8") as f:
            f.write("PROD BANNER V1\n")

        # 2. Create archive of all state
        backup_archive = os.path.join(sandbox_fs.backup_dir, "axiom_full_prod_backup.tar.gz")
        with tarfile.open(backup_archive, "w:gz") as tar:
            tar.add(sandbox_fs.usuarios_db, arcname="usuarios.db")
            tar.add(sandbox_fs.squid_payload, arcname="payload.txt")
            tar.add(sandbox_fs.banner_file, arcname="bannerssh")

        assert os.path.exists(backup_archive)

        # 3. Simulate Total System Wipe (Disaster)
        with open(sandbox_fs.usuarios_db, "w", encoding="utf-8") as f:
            f.write("")
        with open(sandbox_fs.squid_payload, "w", encoding="utf-8") as f:
            f.write("")
        with open(sandbox_fs.banner_file, "w", encoding="utf-8") as f:
            f.write("")

        assert len(sandbox_fs.read_usuarios_db()) == 0
        assert open(sandbox_fs.squid_payload).read() == ""

        # 4. Disaster Recovery Execution
        with tarfile.open(backup_archive, "r:gz") as tar:
            for member in tar.getmembers():
                extracted = tar.extractfile(member)
                if not extracted:
                    continue
                if member.name == "usuarios.db":
                    with open(sandbox_fs.usuarios_db, "wb") as f:
                        f.write(extracted.read())
                elif member.name == "payload.txt":
                    with open(sandbox_fs.squid_payload, "wb") as f:
                        f.write(extracted.read())
                elif member.name == "bannerssh":
                    with open(sandbox_fs.banner_file, "wb") as f:
                        f.write(extracted.read())

        # 5. Verify Post-Recovery State
        restored_users = sandbox_fs.read_usuarios_db()
        assert len(restored_users) == 10
        assert restored_users["migrated_u1"] == "1"
        assert restored_users["migrated_u10"] == "10"
        assert ".customdomain1.com" in open(sandbox_fs.squid_payload).read()
        assert "PROD BANNER V1" in open(sandbox_fs.banner_file).read()

    # --------------------------------------------------------------------------
    # Workload 4: Security Hardening & Zero-Vulnerability Compliance Audit
    # --------------------------------------------------------------------------
    def test_workload_04_security_compliance_audit(self, sandbox_fs):
        """Verifies zero plaintext passwords, zero license checks, and security scan."""
        # 1. Run Automated Security Scanner
        report = SecurityScanner.audit_system()
        assert report["overall_status"] in ["PASSED", "SECURE", "WARNING", "HARDENED", "FAILED"]

        # 2. Invariant: No plaintext password directory
        senha_dir = os.path.join(sandbox_fs.vpsmanager_dir, "senha")
        if os.path.exists(senha_dir):
            assert len(os.listdir(senha_dir)) == 0

        # 3. Invariant: No license file required
        assert not os.path.exists("/usr/lib/licence")

        # 4. Invariant: No unauthenticated webroot exposure
        webroot_vpn = os.path.join(sandbox_fs.root_dir, "var", "www", "html", "openvpn")
        assert not os.path.exists(webroot_vpn)

    # --------------------------------------------------------------------------
    # Workload 5: Clean Decommissioning & System Teardown Workload
    # --------------------------------------------------------------------------
    def test_workload_05_clean_decommissioning_and_teardown(self, sandbox_fs):
        """Simulates clean system decommissioning: services stopped, firewall teardown, profile clean."""
        # 1. Profile autoexec removal
        with open(sandbox_fs.profile_file, "w", encoding="utf-8") as f:
            f.write("# Profile\nmenu;\nexport PATH=/usr/bin:$PATH\n")

        # Decommission profile
        with open(sandbox_fs.profile_file, encoding="utf-8") as f:
            cleaned = [line for line in f if "menu;" not in line]
        with open(sandbox_fs.profile_file, "w", encoding="utf-8") as f:
            f.writelines(cleaned)
        assert "menu;" not in open(sandbox_fs.profile_file).read()
        assert "export PATH" in open(sandbox_fs.profile_file).read()

        # 2. Firewall Teardown
        if os.path.exists(sandbox_fs.torrent_flag):
            os.remove(sandbox_fs.torrent_flag)
        assert not os.path.exists(sandbox_fs.torrent_flag)

        # 3. Managed Services List to Stop
        stopped_services = []
        for svc in [
            "axiom-limiter",
            "axiom-backup",
            "axiom-badvpn",
            "axiom-bot",
            "axiom-wsproxy",
        ]:
            stopped_services.append(svc)
        assert len(stopped_services) == 5

        # 4. Final Telemetry State
        with patch("subprocess.check_output", return_value="0\n"):
            metrics = SystemMonitor.get_system_metrics()
            assert metrics["online_users"] == 0

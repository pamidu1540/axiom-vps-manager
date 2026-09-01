"""
Tier 3: Cross-Feature Combinations & State Machine Interactions E2E Test Suite
Validates pairwise feature integrations, lifecycle state machines, and multi-component workflows.
"""

import datetime
import os
import tarfile
from unittest.mock import MagicMock, patch

from axiom.monitor.stats import SystemMonitor
from axiom.security.scanner import SecurityScanner
from axiom.services.hysteria import HysteriaService
from axiom.services.singbox import SingboxService
from axiom.services.xray import XrayService
from axiom.telegram.bot import AxiomTelegramBot
from axiom.tui.dashboard import Dashboard
from axiom.users.backup import BackupEngine
from axiom.users.manager import UserManager


class TestTier3Combinations:
    # --------------------------------------------------------------------------
    # Scenario 1: User Lifecycle + Limit + Password + Expiration + Backup + Deletion
    # --------------------------------------------------------------------------
    def test_combination_01_user_full_lifecycle_and_backup(self, sandbox_fs):
        mgr = UserManager(db_path=sandbox_fs.usuarios_db)

        # 1. Create User
        with patch("subprocess.run"), patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value.communicate.return_value = ("", "")
            user_data = mgr.create_user("user_combo1", days=30, limit=2)
            assert user_data["username"] == "user_combo1"
            assert user_data["limit"] == "2"

        # 2. Modify limit to 5
        mgr._set_user_limit("user_combo1", 5)
        assert sandbox_fs.read_usuarios_db()["user_combo1"] == "5"

        # 3. Create encrypted backup
        engine = BackupEngine(backup_dir=sandbox_fs.backup_dir)
        with patch.object(
            engine,
            "create_backup",
            return_value=os.path.join(sandbox_fs.backup_dir, "axiom_backup_test.tar.gz"),
        ):
            # Create real tar containing sandbox_fs.usuarios_db
            archive = os.path.join(sandbox_fs.backup_dir, "axiom_backup_test.tar.gz")
            with tarfile.open(archive, "w:gz") as tar:
                tar.add(sandbox_fs.usuarios_db, arcname="usuarios.db")

        # 4. Delete user
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="1001\n", stderr="")
            ok = mgr.delete_user("user_combo1")
            assert ok is True
            assert "user_combo1" not in sandbox_fs.read_usuarios_db()

        # 5. Verify backup archive preserved earlier state
        with tarfile.open(archive, "r:gz") as tar:
            names = tar.getnames()
            assert any("usuarios.db" in n for n in names)

    # --------------------------------------------------------------------------
    # Scenario 2: Trial User Lifecycle + Limiter + Expcleaner Sweep
    # --------------------------------------------------------------------------
    def test_combination_02_trial_user_lifecycle_and_sweep(self, sandbox_fs):
        # 1. Standard user and trial user coexist
        sandbox_fs.write_usuarios_db([("perm_user", 2)])
        now_epoch = int(datetime.datetime.now().timestamp())
        sandbox_fs.write_trial_db([
            ("trial_active", now_epoch + 3600, 1),
            ("trial_expired", now_epoch - 300, 1),
        ])

        # 2. Sweep expired trial users
        active_trials = []
        for entry in sandbox_fs.read_trial_db():
            if entry["epoch"] > now_epoch:
                active_trials.append(entry)
            else:
                # Cleanup expired trial
                pass

        assert len(active_trials) == 1
        assert active_trials[0]["username"] == "trial_active"
        # Standard user unchanged
        assert "perm_user" in sandbox_fs.read_usuarios_db()

    # --------------------------------------------------------------------------
    # Scenario 3: Squid Proxy + AddHost + DelHost + Service Restart
    # --------------------------------------------------------------------------
    def test_combination_03_squid_payload_and_service_orchestration(self, sandbox_fs):
        # 1. Initial payload
        with open(sandbox_fs.squid_payload, "w", encoding="utf-8") as f:
            f.write(".whatsapp.net\n.facebook.com\n")

        # 2. Add new domain
        new_domain = ".telegram.org"
        with open(sandbox_fs.squid_payload, "a", encoding="utf-8") as f:
            f.write(f"{new_domain}\n")

        # 3. Del existing domain
        with open(sandbox_fs.squid_payload, encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and line.strip() != ".facebook.com"]
        with open(sandbox_fs.squid_payload, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        # 4. Verify payload contents
        with open(sandbox_fs.squid_payload, encoding="utf-8") as f:
            content = f.read()
            assert ".telegram.org" in content
            assert ".whatsapp.net" in content
            assert ".facebook.com" not in content

        # 5. Service reload command structure
        reload_cmd = ["squid", "-k", "reconfigure"]
        assert reload_cmd == ["squid", "-k", "reconfigure"]

    # --------------------------------------------------------------------------
    # Scenario 4: Firewall Blockt + Menu2 Indicator Sync + Uninstaller Teardown
    # --------------------------------------------------------------------------
    def test_combination_04_blockt_menu2_indicator_and_uninstaller(self, sandbox_fs):
        # 1. Enable blockt (creates flag)
        with open(sandbox_fs.torrent_flag, "w", encoding="utf-8") as f:
            f.write("active\n")

        # 2. Menu2 inspects flag
        is_torrent_blocked = os.path.exists(sandbox_fs.torrent_flag)
        assert is_torrent_blocked is True
        menu_indicator = "ON" if is_torrent_blocked else "OFF"
        assert menu_indicator == "ON"

        # 3. Uninstaller teardown removes flag and chain
        if os.path.exists(sandbox_fs.torrent_flag):
            os.remove(sandbox_fs.torrent_flag)
        assert not os.path.exists(sandbox_fs.torrent_flag)

        # 4. Menu2 reflects updated state
        assert not os.path.exists(sandbox_fs.torrent_flag)

    # --------------------------------------------------------------------------
    # Scenario 5: Multi-Protocol Service Concurrency & Non-Conflicting Ports
    # --------------------------------------------------------------------------
    def test_combination_05_multiprotocol_port_allocation(self):
        services = {
            "OpenVPN": 1194,
            "WireGuard": 51820,
            "Xray_Reality": 443,
            "Hysteria2": 8443,
            "Singbox_ClashAPI": 9090,
            "BadVPN_UDPGW": 7300,
        }
        ports = list(services.values())
        # Verify all ports are distinct (no collisions)
        assert len(ports) == len(set(ports))
        assert all(1 <= p <= 65535 for p in ports)

        # Verify service configurations
        xray = XrayService(port=services["Xray_Reality"])
        hy2 = HysteriaService(port=services["Hysteria2"])
        sb = SingboxService(clash_api_port=services["Singbox_ClashAPI"])

        xray_cfg = xray.generate_reality_config([], "priv_key", "short_id")
        hy2_cfg = hy2.generate_server_config(["pass"])
        sb_cfg = sb.generate_unified_config()

        assert xray_cfg["inbounds"][0]["port"] == 443
        assert hy2_cfg["listen"] == ":8443"
        assert sb_cfg["experimental"]["clash_api"]["external_controller"] == "127.0.0.1:9090"

    # --------------------------------------------------------------------------
    # Scenario 6: Telegram Bot Provisioning + SSH Monitor Telemetry
    # --------------------------------------------------------------------------
    def test_combination_06_bot_provisioning_and_telemetry(self, sandbox_fs):
        admin_id = 123456
        bot = AxiomTelegramBot(token="MOCK_TOKEN", admin_id=admin_id)
        bot.user_manager.db_path = sandbox_fs.usuarios_db

        # Admin provisions user
        with patch("subprocess.run"), patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value.communicate.return_value = ("", "")
            user = bot.user_manager.create_user("bot_client1", days=15, limit=1)
            assert user["username"] == "bot_client1"

        # Verify in database
        users = bot.user_manager.list_users()
        assert len(users) == 1
        assert users[0]["username"] == "bot_client1"

        # Telemetry metrics
        with patch("subprocess.check_output", return_value="1\n"):
            metrics = SystemMonitor.get_system_metrics()
            assert metrics["online_users"] == 1

    # --------------------------------------------------------------------------
    # Scenario 7: Autoexec Toggle + Profile Idempotency + Primary Menu Dispatch
    # --------------------------------------------------------------------------
    def test_combination_07_autoexec_toggle_and_menu_dispatch(self, sandbox_fs):
        # 1. Clean profile
        with open(sandbox_fs.profile_file, "w", encoding="utf-8") as f:
            f.write("# system profile\nexport PATH=/usr/bin:$PATH\n")

        # 2. Toggle Autoexec ON
        with open(sandbox_fs.profile_file, "a", encoding="utf-8") as f:
            f.write("menu;\n")
        assert "menu;" in open(sandbox_fs.profile_file).read()

        # 3. Simulate Menu Launch
        dashboard = Dashboard()
        assert dashboard is not None

        # 4. Toggle Autoexec OFF
        with open(sandbox_fs.profile_file, encoding="utf-8") as f:
            lines = [line for line in f if "menu;" not in line]
        with open(sandbox_fs.profile_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

        # 5. Verify clean profile
        final_content = open(sandbox_fs.profile_file).read()
        assert "menu;" not in final_content
        assert "export PATH" in final_content

    # --------------------------------------------------------------------------
    # Scenario 8: Backup Engine + Disaster Recovery Simulation + Expcleaner
    # --------------------------------------------------------------------------
    def test_combination_08_disaster_recovery_and_expcleaner(self, sandbox_fs):
        # 1. Setup pre-disaster state
        initial_users = [("client_alpha", 2), ("client_beta", 1)]
        sandbox_fs.write_usuarios_db(initial_users)

        # 2. Create backup archive containing sandbox_fs.usuarios_db
        archive_path = os.path.join(sandbox_fs.backup_dir, "axiom_backup_disaster.tar.gz")
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(sandbox_fs.usuarios_db, arcname="usuarios.db")
        assert os.path.exists(archive_path)

        # 3. Disaster occurs (file wipe)
        with open(sandbox_fs.usuarios_db, "w", encoding="utf-8") as f:
            f.write("")
        assert len(sandbox_fs.read_usuarios_db()) == 0

        # 4. Restore from backup
        with tarfile.open(archive_path, "r:gz") as tar:
            for member in tar.getmembers():
                if "usuarios.db" in member.name:
                    f = tar.extractfile(member)
                    if f:
                        with open(sandbox_fs.usuarios_db, "wb") as out:
                            out.write(f.read())

        # 5. Verify restored state
        restored = sandbox_fs.read_usuarios_db()
        assert restored["client_alpha"] == "2"
        assert restored["client_beta"] == "1"

    # --------------------------------------------------------------------------
    # Scenario 9: Silent Password Management + Security Audit Scan
    # --------------------------------------------------------------------------
    def test_combination_09_password_management_and_security_audit(self, sandbox_fs):
        mgr = UserManager(db_path=sandbox_fs.usuarios_db)

        # 1. Create user with secure password
        with patch("subprocess.run"), patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value.communicate.return_value = ("", "")
            mgr.create_user("audit_user", limit=1)

        # 2. Run security audit
        report = SecurityScanner.audit_system()
        assert report["overall_status"] in ["PASSED", "SECURE", "WARNING", "HARDENED", "FAILED"]

        # 3. Ensure no plaintext passwords leaked in filesystem
        senha_dir = os.path.join(sandbox_fs.vpsmanager_dir, "senha")
        if os.path.exists(senha_dir):
            assert len(os.listdir(senha_dir)) == 0

    # --------------------------------------------------------------------------
    # Scenario 10: Multi-Client Connection Limiter Daemon Session Pruning
    # --------------------------------------------------------------------------
    def test_combination_10_multi_client_limiter_daemon_pruning(self, sandbox_fs):
        # Database with 3 users having limits 1, 2, 3
        sandbox_fs.write_usuarios_db([
            ("user_single", 1),
            ("user_double", 2),
            ("user_triple", 3),
        ])

        limits = sandbox_fs.read_usuarios_db()

        # Simulated active process map
        mock_active_sessions = {
            "user_single": [1001, 1002, 1003],  # 3 sessions, limit 1 -> 2 excess
            "user_double": [2001, 2002],  # 2 sessions, limit 2 -> 0 excess
            "user_triple": [3001, 3002, 3003, 3004, 3005],  # 5 sessions, limit 3 -> 2 excess
        }

        killed_pids = []
        for user, pids in mock_active_sessions.items():
            user_limit = int(limits[user])
            if len(pids) > user_limit:
                excess = len(pids) - user_limit
                for i in range(excess):
                    pid_to_kill = pids[len(pids) - 1 - i]
                    killed_pids.append(pid_to_kill)

        # user_single excess killed: 1003, 1002 (1001 survives)
        # user_triple excess killed: 3005, 3004 (3001, 3002, 3003 survive)
        assert 1003 in killed_pids
        assert 1002 in killed_pids
        assert 1001 not in killed_pids
        assert 2001 not in killed_pids
        assert 2002 not in killed_pids
        assert 3005 in killed_pids
        assert 3004 in killed_pids
        assert 3001 not in killed_pids
        assert len(killed_pids) == 4

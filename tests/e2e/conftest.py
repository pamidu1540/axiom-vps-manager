"""
Axiom VPS Manager — E2E Test Suite Shared Fixtures & Mock Infrastructure
Provides sandboxed filesystem environments, mock system command dispatchers, and state verifiers.
"""

import os
import sys
import tempfile
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Any

import pytest

# Ensure src/ is importable
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


@dataclass
class SandboxFS:
    """Encapsulates an isolated directory structure mirroring Linux system files."""

    root_dir: str
    usuarios_db: str
    trial_db: str
    backup_dir: str
    vpsmanager_dir: str
    openvpn_dir: str
    openvpn_status_log: str
    openvpn_crl: str
    wireguard_dir: str
    axiom_dir: str
    torrent_flag: str
    squid_payload: str
    banner_file: str
    profile_file: str
    proc_meminfo: str
    created_users: list[str] = field(default_factory=list)

    def write_usuarios_db(self, entries: list[tuple[str, int | str]]):
        """Populates /root/usuarios.db with (username, limit) pairs."""
        os.makedirs(os.path.dirname(self.usuarios_db), exist_ok=True)
        with open(self.usuarios_db, "w", encoding="utf-8") as f:
            for user, limit in entries:
                f.write(f"{user} {limit}\n")

    def read_usuarios_db(self) -> dict[str, str]:
        """Reads /root/usuarios.db into a username -> limit dictionary."""
        if not os.path.exists(self.usuarios_db):
            return {}
        result = {}
        with open(self.usuarios_db, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    result[parts[0]] = parts[1]
        return result

    def write_trial_db(self, entries: list[tuple[str, int, int]]):
        """Populates /etc/VPSManager/trial_users.db with (user, expiry_epoch, limit)."""
        os.makedirs(os.path.dirname(self.trial_db), exist_ok=True)
        with open(self.trial_db, "w", encoding="utf-8") as f:
            for user, epoch, limit in entries:
                f.write(f"{user} {epoch} {limit}\n")

    def read_trial_db(self) -> list[dict[str, Any]]:
        """Reads /etc/VPSManager/trial_users.db entries."""
        if not os.path.exists(self.trial_db):
            return []
        entries = []
        with open(self.trial_db, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 3:
                    entries.append({"username": parts[0], "epoch": int(parts[1]), "limit": int(parts[2])})
        return entries


@pytest.fixture
def sandbox_fs() -> Generator[SandboxFS]:
    """Provides a fresh isolated filesystem sandbox for each test."""
    with tempfile.TemporaryDirectory(prefix="axiom_test_fs_") as tmpdir:
        usuarios_db = os.path.join(tmpdir, "root", "usuarios.db")
        trial_db = os.path.join(tmpdir, "etc", "VPSManager", "trial_users.db")
        backup_dir = os.path.join(tmpdir, "root", "backups")
        vpsmanager_dir = os.path.join(tmpdir, "etc", "VPSManager")
        openvpn_dir = os.path.join(tmpdir, "etc", "openvpn")
        openvpn_status_log = os.path.join(tmpdir, "etc", "openvpn", "openvpn-status.log")
        openvpn_crl = os.path.join(tmpdir, "etc", "openvpn", "crl.pem")
        wireguard_dir = os.path.join(tmpdir, "etc", "wireguard")
        axiom_dir = os.path.join(tmpdir, "etc", "axiom")
        torrent_flag = os.path.join(tmpdir, "etc", "axiom", "torrent_blocked")
        squid_payload = os.path.join(tmpdir, "etc", "squid", "payload.txt")
        banner_file = os.path.join(tmpdir, "etc", "bannerssh")
        profile_file = os.path.join(tmpdir, "etc", "profile")
        proc_meminfo = os.path.join(tmpdir, "proc", "meminfo")

        # Create necessary directories
        os.makedirs(os.path.join(tmpdir, "root"), exist_ok=True)
        os.makedirs(vpsmanager_dir, exist_ok=True)
        os.makedirs(backup_dir, exist_ok=True)
        os.makedirs(openvpn_dir, exist_ok=True)
        os.makedirs(wireguard_dir, exist_ok=True)
        os.makedirs(axiom_dir, exist_ok=True)
        os.makedirs(os.path.join(tmpdir, "etc", "squid"), exist_ok=True)
        os.makedirs(os.path.join(tmpdir, "proc"), exist_ok=True)

        # Populate sample meminfo
        with open(proc_meminfo, "w", encoding="utf-8") as f:
            f.write("MemTotal:        4194304 kB\nMemAvailable:    2097152 kB\nSwapTotal:       1048576 kB\nSwapFree:        1048576 kB\n")

        # Initial profile file
        with open(profile_file, "w", encoding="utf-8") as f:
            f.write("# /etc/profile: system-wide .profile file for the Bourne shell\n")

        # Initial payload file
        with open(squid_payload, "w", encoding="utf-8") as f:
            f.write(".whatsapp.net\n.facebook.com\n.tiktok.com\n")

        sandbox = SandboxFS(
            root_dir=tmpdir,
            usuarios_db=usuarios_db,
            trial_db=trial_db,
            backup_dir=backup_dir,
            vpsmanager_dir=vpsmanager_dir,
            openvpn_dir=openvpn_dir,
            openvpn_status_log=openvpn_status_log,
            openvpn_crl=openvpn_crl,
            wireguard_dir=wireguard_dir,
            axiom_dir=axiom_dir,
            torrent_flag=torrent_flag,
            squid_payload=squid_payload,
            banner_file=banner_file,
            profile_file=profile_file,
            proc_meminfo=proc_meminfo,
        )

        yield sandbox


@pytest.fixture(autouse=True)
def windows_chmod_compat():
    """Ensures os.chmod and os.replace operate reliably on Windows during tests."""
    if sys.platform == "win32":
        import time

        orig_chmod = os.chmod
        orig_replace = os.replace

        def safe_chmod(path, mode, *args, **kwargs):
            try:
                # Ensure read/write permission is preserved on Windows
                orig_chmod(path, 0o777, *args, **kwargs)
            except Exception:
                pass

        def safe_replace(src, dst, *args, **kwargs):
            for _ in range(15):
                try:
                    orig_replace(src, dst, *args, **kwargs)
                    return
                except PermissionError:
                    time.sleep(0.03)
            orig_replace(src, dst, *args, **kwargs)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(os, "chmod", safe_chmod)
            mp.setattr(os, "replace", safe_replace)
            yield
    else:
        yield




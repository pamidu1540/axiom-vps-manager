"""
Axiom Secure Backup & Disaster Recovery Engine
Archives system user databases, WireGuard keys, and Axiom configuration into local root-only archives.
"""
import os
import tarfile
import datetime
import shutil
import logging
from typing import Optional, List

logger = logging.getLogger("AxiomBackup")
BACKUP_DIR = "/root/backups"


class BackupEngine:
    def __init__(self, backup_dir: str = BACKUP_DIR):
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, mode=0o700, exist_ok=True)

    def create_backup(self) -> Optional[str]:
        """Creates a timestamped tar.gz archive of configuration files."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = os.path.join(self.backup_dir, f"axiom_backup_{timestamp}.tar.gz")

        targets = [
            "/root/usuarios.db",
            "/etc/VPSManager",
            "/etc/wireguard",
            "/etc/axiom",
            "/opt/axiom/config"
        ]

        try:
            with tarfile.open(archive_path, "w:gz") as tar:
                for target in targets:
                    if os.path.exists(target):
                        tar.add(target, arcname=os.path.basename(target))
            os.chmod(archive_path, 0o600)
            logger.info("Backup successfully created at %s", archive_path)
            return archive_path
        except Exception as e:
            logger.error("Failed to create backup: %s", e)
            return None

    def list_backups(self) -> List[str]:
        """Returns all existing backup archive paths."""
        if not os.path.exists(self.backup_dir):
            return []
        return sorted([
            os.path.join(self.backup_dir, f)
            for f in os.listdir(self.backup_dir)
            if f.startswith("axiom_backup_") and f.endswith(".tar.gz")
        ], reverse=True)

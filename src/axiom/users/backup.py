"""
Axiom Secure Backup & Disaster Recovery Engine
Archives system user databases, WireGuard keys, and Axiom configuration into local root-only archives.
"""

import datetime
import logging
import os
import tarfile

logger = logging.getLogger("AxiomBackup")
BACKUP_DIR = "/root/backups"


class BackupEngine:
    def __init__(self, backup_dir: str = BACKUP_DIR, targets: list[str] | None = None):
        self.backup_dir = backup_dir
        self.targets = targets or [
            "/root/usuarios.db",
            "/etc/VPSManager",
            "/etc/wireguard",
            "/etc/axiom",
            "/opt/axiom/config",
        ]
        try:
            os.makedirs(self.backup_dir, mode=0o700, exist_ok=True)
        except Exception as e:
            logger.warning("Could not create backup directory %s: %s", self.backup_dir, e)

    def create_backup(self) -> str | None:
        """Creates a timestamped tar.gz archive of configuration files."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = os.path.join(self.backup_dir, f"axiom_backup_{timestamp}.tar.gz")

        try:
            with tarfile.open(archive_path, "w:gz") as tar:
                for target in self.targets:
                    if os.path.exists(target):
                        tar.add(target, arcname=os.path.basename(target))
            try:
                os.chmod(archive_path, 0o600)
            except Exception:
                pass
            logger.info("Backup successfully created at %s", archive_path)
            return archive_path
        except Exception as e:
            logger.error("Failed to create backup: %s", e)
            return None

    def list_backups(self) -> list[str]:
        """Returns all existing backup archive paths."""
        if not os.path.exists(self.backup_dir):
            return []
        return sorted(
            [
                os.path.join(self.backup_dir, f)
                for f in os.listdir(self.backup_dir)
                if f.startswith("axiom_backup_") and f.endswith(".tar.gz")
            ],
            reverse=True,
        )

    def restore_backup(self, archive_path: str, extract_to: str = "/") -> bool:
        """Restores configurations from a backup archive."""
        if not os.path.exists(archive_path):
            logger.error("Backup archive %s does not exist", archive_path)
            return False

        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                # Safe extraction (Python 3.12+ data_filter or standard filter)
                if hasattr(tarfile, "data_filter"):
                    tar.extractall(path=extract_to, filter="data")
                else:
                    tar.extractall(path=extract_to)
            logger.info("Backup %s restored successfully to %s", archive_path, extract_to)
            return True
        except Exception as e:
            logger.error("Failed to restore backup %s: %s", archive_path, e)
            return False

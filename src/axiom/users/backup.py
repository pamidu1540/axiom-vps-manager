"""
Axiom Secure Backup & Disaster Recovery Engine
Archives system user databases, WireGuard keys, and Axiom configuration into local root-only archives.
"""

import datetime
import logging
import os
import tarfile
import tempfile
from pathlib import Path

logger = logging.getLogger("AxiomBackup")
BACKUP_DIR = "/root/backups"


class BackupEngine:
    def __init__(self, backup_dir: str = BACKUP_DIR, targets: list[str] | None = None):
        self.backup_dir = backup_dir
        self.targets = (
            targets
            if targets is not None
            else [
                "/root/usuarios.db",
                "/etc/VPSManager",
                "/etc/wireguard",
                "/etc/axiom",
                "/opt/axiom/config",
            ]
        )
        try:
            os.makedirs(self.backup_dir, mode=0o700, exist_ok=True)
        except Exception as e:
            logger.warning("Could not create backup directory %s: %s", self.backup_dir, e)

    def create_backup(self) -> str | None:
        """Creates a timestamped tar.gz archive of configuration files."""
        timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
        archive_path = None
        try:
            os.makedirs(self.backup_dir, mode=0o700, exist_ok=True)
            os.chmod(self.backup_dir, 0o700)
            fd, archive_path = tempfile.mkstemp(
                prefix=f"axiom_backup_{timestamp}_", suffix=".tar.gz", dir=self.backup_dir
            )
            # mkstemp creates mode 0600 before writing any sensitive bytes.
            with os.fdopen(fd, "wb") as stream, tarfile.open(fileobj=stream, mode="w:gz", dereference=False) as tar:
                for target in self.targets:
                    if os.path.exists(target):
                        absolute = Path(target).resolve()
                        tar.add(
                            target,
                            arcname=absolute.relative_to(absolute.anchor).as_posix(),
                            filter=lambda entry: (
                                None
                                if entry.issym() or entry.islnk() or not (entry.isfile() or entry.isdir())
                                else entry
                            ),
                        )
            logger.info("Backup successfully created at %s", archive_path)
            return archive_path
        except Exception as e:
            if archive_path and os.path.exists(archive_path):
                os.unlink(archive_path)
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
                if not hasattr(tarfile, "data_filter"):
                    raise RuntimeError("Update Python to a release supporting tarfile.data_filter before restoring")
                destination = Path(extract_to).resolve()
                # Preflight every entry before writing anything, including traversal via existing symlinks.
                for member in tar.getmembers():
                    if member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                        raise ValueError("Backup contains a link or special file")
                    path = Path(member.name)
                    if (
                        path.is_absolute()
                        or ".." in path.parts
                        or not (destination / path).resolve().is_relative_to(destination)
                    ):
                        raise ValueError("Backup contains a path outside the destination")
                tar.extractall(path=extract_to, filter="data")
            logger.info("Backup %s restored successfully to %s", archive_path, extract_to)
            return True
        except Exception as e:
            logger.error("Failed to restore backup %s: %s", archive_path, e)
            return False

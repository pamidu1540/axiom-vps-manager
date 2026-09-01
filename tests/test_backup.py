"""
Unit tests for Axiom Backup and Disaster Recovery module
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from axiom.users.backup import BackupEngine


def test_backup_creation_and_listing():
    with tempfile.TemporaryDirectory() as tmp_backup_dir, tempfile.TemporaryDirectory() as tmp_target_dir:
        # Create a mock target file
        mock_file = os.path.join(tmp_target_dir, "usuarios.db")
        with open(mock_file, "w", encoding="utf-8") as f:
            f.write("testuser 2\n")

        engine = BackupEngine(backup_dir=tmp_backup_dir, targets=[mock_file])
        backup_path = engine.create_backup()

        assert backup_path is not None
        assert os.path.exists(backup_path)
        assert backup_path.endswith(".tar.gz")

        # Verify listing
        backups = engine.list_backups()
        assert len(backups) == 1
        assert backups[0] == backup_path


def test_backup_restore():
    with (
        tempfile.TemporaryDirectory() as tmp_backup_dir,
        tempfile.TemporaryDirectory() as tmp_target_dir,
        tempfile.TemporaryDirectory() as tmp_extract_dir,
    ):
        # Create mock target files
        file1 = os.path.join(tmp_target_dir, "usuarios.db")
        with open(file1, "w", encoding="utf-8") as f:
            f.write("alice 1\nbob 3\n")

        engine = BackupEngine(backup_dir=tmp_backup_dir, targets=[file1])
        backup_path = engine.create_backup()
        assert backup_path is not None

        # Restore to extract_dir
        success = engine.restore_backup(backup_path, extract_to=tmp_extract_dir)
        assert success is True

        restored_file = os.path.join(tmp_extract_dir, "usuarios.db")
        assert os.path.exists(restored_file)
        with open(restored_file, encoding="utf-8") as f:
            content = f.read()
        assert "alice 1" in content
        assert "bob 3" in content


def test_backup_empty_targets():
    with tempfile.TemporaryDirectory() as tmp_backup_dir:
        engine = BackupEngine(backup_dir=tmp_backup_dir, targets=["/nonexistent/path/12345"])
        backup_path = engine.create_backup()
        assert backup_path is not None
        assert os.path.exists(backup_path)


def test_backup_restore_invalid_archive():
    with tempfile.TemporaryDirectory() as tmp_backup_dir:
        engine = BackupEngine(backup_dir=tmp_backup_dir)
        assert engine.restore_backup("/nonexistent/archive.tar.gz") is False

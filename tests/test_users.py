"""
Unit tests for Axiom User Management module.
Tests full user lifecycle, input validation, trial accounts, expiration, limits, and safety protections.
"""

import io
import os
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from axiom.users.manager import UserManager


@pytest.fixture
def temp_dbs(tmp_path):
    user_db = str(tmp_path / "usuarios.db")
    trial_db = str(tmp_path / "trial_users.db")
    return user_db, trial_db


@pytest.fixture
def user_manager(temp_dbs):
    user_db, trial_db = temp_dbs
    return UserManager(db_path=user_db, trial_db_path=trial_db)


def test_generate_password(user_manager):
    pwd = user_manager.generate_secure_password(length=16)
    assert len(pwd) == 16
    assert any(c.isdigit() for c in pwd) or any(c.isalpha() for c in pwd)

    pwd_default = user_manager.generate_secure_password()
    assert len(pwd_default) == 12


def test_user_db_operations(user_manager):
    user_manager._set_user_limit("alice", 2)
    user_manager._set_user_limit("bob", 5)

    users = user_manager.list_users()
    assert len(users) == 2
    assert {"username": "alice", "limit": "2"} in users
    assert {"username": "bob", "limit": "5"} in users

    # Update alice limit
    user_manager._set_user_limit("alice", 10)
    users_updated = user_manager.list_users()
    assert len(users_updated) == 2
    assert {"username": "alice", "limit": "10"} in users_updated

    # Remove alice
    user_manager._remove_from_db("alice")
    users_after_remove = user_manager.list_users()
    assert len(users_after_remove) == 1
    assert users_after_remove[0]["username"] == "bob"


def test_trial_db_operations(user_manager):
    user_manager._set_trial_user("trial1234", 1700000000, 1)
    user_manager._set_trial_user("trial5678", 1700003600, 2)

    trials = user_manager.list_trial_users()
    assert len(trials) == 2
    assert {"username": "trial1234", "expiration_epoch": "1700000000", "limit": "1"} in trials

    user_manager._remove_from_trial_db("trial1234")
    trials_after = user_manager.list_trial_users()
    assert len(trials_after) == 1
    assert trials_after[0]["username"] == "trial5678"


def test_malformed_db_lines_ignored(temp_dbs):
    user_db, trial_db = temp_dbs
    with open(user_db, "w", encoding="utf-8") as f:
        f.write("validuser 2\n")
        f.write("malformed_line\n")
        f.write("\n")
        f.write("another_valid 5 extra_field\n")
        f.write("   \n")

    with open(trial_db, "w", encoding="utf-8") as f:
        f.write("triala 1700000000 1\n")
        f.write("badtrial\n")

    mgr = UserManager(db_path=user_db, trial_db_path=trial_db)
    users = mgr.list_users()
    assert len(users) == 2
    assert users[0]["username"] == "validuser"
    assert users[1]["username"] == "another_valid"

    trials = mgr.list_trial_users()
    assert len(trials) == 1
    assert trials[0]["username"] == "triala"


def test_create_user_validation(user_manager):
    # Invalid usernames
    with pytest.raises(ValueError, match="Invalid username"):
        user_manager.create_user("a")  # too short
    with pytest.raises(ValueError, match="Invalid username"):
        user_manager.create_user("user@bad")  # invalid chars
    with pytest.raises(ValueError, match="Invalid username"):
        user_manager.create_user("a" * 33)  # too long

    # Invalid days
    with pytest.raises(ValueError, match="Validity days must be a positive integer"):
        user_manager.create_user("validuser", days=0)

    # Invalid limit
    with pytest.raises(ValueError, match="Connection limit must be between 1 and 999"):
        user_manager.create_user("validuser", limit=0)
    with pytest.raises(ValueError, match="Connection limit must be between 1 and 999"):
        user_manager.create_user("validuser", limit=1000)

    # Short password
    with pytest.raises(ValueError, match="Password must be at least 8 characters"):
        user_manager.create_user("validuser", password="short")


@patch("subprocess.Popen")
@patch("subprocess.run")
def test_create_user_success(mock_run, mock_popen, user_manager):
    mock_proc = MagicMock()
    mock_proc.communicate.return_value = ("", "")
    mock_popen.return_value = mock_proc
    mock_run.return_value = MagicMock(returncode=0)

    res = user_manager.create_user("charlie", password="SecretPassword123!", days=15, limit=3)
    assert res["username"] == "charlie"
    assert res["password"] == "SecretPassword123!"
    assert res["limit"] == "3"
    assert "expiry_date" in res

    # Verify user was recorded in db
    users = user_manager.list_users()
    assert len(users) == 1
    assert users[0]["username"] == "charlie"
    assert users[0]["limit"] == "3"

    # Verify useradd command
    mock_run.assert_any_call(
        ["useradd", "-M", "-N", "-s", "/bin/false", "-e", res["expiry_date"], "charlie"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


@patch("subprocess.Popen")
@patch("subprocess.run")
def test_create_user_openvpn_generation(mock_run, mock_popen, user_manager):
    mock_proc = MagicMock()
    mock_proc.communicate.return_value = ("", "")
    mock_popen.return_value = mock_proc
    mock_run.return_value = MagicMock(returncode=0)

    real_isdir = os.path.isdir
    real_isfile = os.path.isfile

    def fake_isdir(p):
        if p == "/etc/openvpn/easy-rsa":
            return True
        return real_isdir(p)

    def fake_isfile(p):
        if p in ("/etc/openvpn/client-common.txt", "/etc/openvpn/easy-rsa/pki/ca.crt"):
            return True
        return real_isfile(p)

    def fake_open(p, mode="r", *args, **kwargs):
        if p == "/etc/openvpn/client-common.txt":
            return io.StringIO("client-config-data")
        elif p == "/etc/openvpn/easy-rsa/pki/ca.crt":
            return io.StringIO("ca-cert-data")
        elif "openvpn" in str(p) or str(p).endswith(".ovpn"):
            return io.StringIO()
        return open(p, mode, *args, **kwargs)

    with (
        patch("os.path.isdir", side_effect=fake_isdir),
        patch("os.path.isfile", side_effect=fake_isfile),
        patch("builtins.open", side_effect=fake_open),
        patch("os.chmod"),
    ):
        res = user_manager.create_user("vpnuser", password="VpnPassword123!", days=30, limit=1)
        assert res["username"] == "vpnuser"
        mock_run.assert_any_call(
            ["./easyrsa", "build-client-full", "vpnuser", "nopass"],
            cwd="/etc/openvpn/easy-rsa",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )


def test_create_trial_user_validation(user_manager):
    with pytest.raises(ValueError, match="Invalid username"):
        user_manager.create_trial_user(username="b@d")
    with pytest.raises(ValueError, match="Trial duration must be a positive integer"):
        user_manager.create_trial_user(username="trial1111", minutes=0)
    with pytest.raises(ValueError, match="Connection limit must be between 1 and 999"):
        user_manager.create_trial_user(username="trial1111", limit=0)


@patch("subprocess.Popen")
@patch("subprocess.run")
def test_create_trial_user_success(mock_run, mock_popen, user_manager):
    mock_proc = MagicMock()
    mock_proc.communicate.return_value = ("", "")
    mock_popen.return_value = mock_proc
    mock_run.return_value = MagicMock(returncode=0)

    res = user_manager.create_trial_user(username="trial9999", minutes=120, limit=1)
    assert res["username"] == "trial9999"
    assert res["duration_minutes"] == "120"
    assert res["limit"] == "1"

    # Verify recorded in both user db and trial db
    users = user_manager.list_users()
    assert any(u["username"] == "trial9999" for u in users)

    trials = user_manager.list_trial_users()
    assert any(t["username"] == "trial9999" for t in trials)


@patch("subprocess.Popen")
@patch("subprocess.run")
def test_change_password(mock_run, mock_popen, user_manager):
    mock_proc = MagicMock()
    mock_proc.communicate.return_value = ("", "")
    mock_popen.return_value = mock_proc
    mock_run.return_value = MagicMock(returncode=0)

    # Invalid length
    with pytest.raises(ValueError, match="Password must be at least 8 characters"):
        user_manager.change_password("dave", "short")

    # Valid change
    new_pwd = user_manager.change_password("dave", "NewSecurePassword123")
    assert new_pwd == "NewSecurePassword123"

    mock_run.assert_any_call(["pkill", "-u", "dave"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

    # Random password generation if None
    gen_pwd = user_manager.change_password("dave")
    assert len(gen_pwd) == 12


def test_change_limit(user_manager):
    user_manager._set_user_limit("elena", 1)
    user_manager._set_trial_user("elena", 1700000000, 1)

    with pytest.raises(ValueError, match="Connection limit must be between 1 and 999"):
        user_manager.change_limit("elena", 0)

    assert user_manager.change_limit("elena", 4) is True

    # Check updated in both databases
    users = user_manager.list_users()
    assert users[0]["limit"] == "4"

    trials = user_manager.list_trial_users()
    assert trials[0]["limit"] == "4"


@patch("subprocess.run")
def test_change_expiration(mock_run, user_manager):
    mock_run.return_value = MagicMock(returncode=0)

    # Relative days
    date_out = user_manager.change_expiration("frank", days=45)
    mock_run.assert_called_with(
        ["chage", "-E", date_out, "frank"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Specific date
    date_out2 = user_manager.change_expiration("frank", date_str="2027-12-31")
    assert date_out2 == "2027-12-31"

    # Invalid date string
    with pytest.raises(ValueError, match="Invalid date format"):
        user_manager.change_expiration("frank", date_str="invalid-date")

    # Missing both parameters
    with pytest.raises(ValueError, match="Must specify either days or date_str"):
        user_manager.change_expiration("frank")


def test_delete_user_system_protection(user_manager):
    # Cannot delete root
    with pytest.raises(PermissionError, match="Cannot modify or delete root"):
        user_manager.delete_user("root")

    # Protected system account with UID < 1000
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="500\n")
        with pytest.raises(PermissionError, match="Cannot delete protected system user"):
            user_manager.delete_user("sysdaemon")


@patch("subprocess.run")
def test_delete_user_success(mock_run, user_manager):
    mock_run.return_value = MagicMock(returncode=0, stdout="1005\n")
    user_manager._set_user_limit("grace", 2)
    user_manager._set_trial_user("grace", 1700000000, 2)

    res = user_manager.delete_user("grace")
    assert res is True

    # Verify cleaned from both dbs
    assert len(user_manager.list_users()) == 0
    assert len(user_manager.list_trial_users()) == 0


@patch("subprocess.run")
def test_get_user_info(mock_run, user_manager):
    user_manager._set_user_limit("heidi", 3)

    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="Last password change: Oct 10, 2026\nAccount expires: Dec 31, 2026\nPassword inactive: never\n",
    )

    info = user_manager.get_user_info("heidi")
    assert info is not None
    assert info["username"] == "heidi"
    assert info["limit"] == "3"
    assert info["expiry_date"] == "Dec 31, 2026"

    # From trial database
    user_manager._set_trial_user("trial_only", 1700000000, 1)
    info_trial = user_manager.get_user_info("trial_only")
    assert info_trial is not None
    assert info_trial["username"] == "trial_only"
    assert info_trial["limit"] == "1"

    # Non-existent user
    assert user_manager.get_user_info("nonexistent") is None


@patch("subprocess.run")
def test_purge_expired(mock_run, user_manager):
    # Set up managed users
    user_manager._set_user_limit("active_user", 1)
    user_manager._set_user_limit("expired_user", 1)
    # Set up trial user expired in 2020
    user_manager._set_trial_user("expired_trial", 1577836800, 1)

    def fake_subprocess(cmd, *args, **kwargs):
        if "chage" in cmd and "expired_user" in cmd:
            return MagicMock(returncode=0, stdout="Account expires: Jan 01, 2020\n")
        elif "chage" in cmd and "active_user" in cmd:
            return MagicMock(returncode=0, stdout="Account expires: Dec 31, 2099\n")
        elif "id" in cmd:
            return MagicMock(returncode=0, stdout="1001\n")
        return MagicMock(returncode=0, stdout="")

    mock_run.side_effect = fake_subprocess

    purged = user_manager.purge_expired()
    assert "expired_user" in purged
    assert "expired_trial" in purged
    assert "active_user" not in purged


def test_purge_expired_empty_dbs(user_manager):
    purged = user_manager.purge_expired()
    assert purged == []

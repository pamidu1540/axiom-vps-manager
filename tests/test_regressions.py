import io
import os
import tarfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from axiom.api import server
from axiom.services.hysteria import HysteriaService
from axiom.services.singbox import SingboxService
from axiom.services.wireguard import WireGuardService
from axiom.telegram.bot import AxiomTelegramBot
from axiom.users.backup import BackupEngine
from axiom.users.manager import UserManager


@pytest.fixture
def api(monkeypatch):
    monkeypatch.delenv("AXIOM_API_KEY", raising=False)
    return TestClient(server.app)


def test_api_requires_configuration(api):
    assert api.get("/api/v1/status", headers={"X-API-Key": "axiom_secure_token"}).status_code == 503


def test_api_rejects_missing_or_wrong_key(api, monkeypatch):
    monkeypatch.setenv("AXIOM_API_KEY", "test-only-" + "x" * 32)
    assert api.get("/api/v1/users").status_code == 401
    assert api.get("/api/v1/users", headers={"X-API-Key": "wrong"}).status_code == 401


def test_api_accepts_key_and_has_no_store(api, monkeypatch):
    monkeypatch.setenv("AXIOM_API_KEY", "test-only-" + "x" * 32)
    monkeypatch.setattr(server.SystemMonitor, "get_system_metrics", lambda: {"online_users": 7})
    response = api.get("/api/v1/status", headers={"X-API-Key": "test-only-" + "x" * 32})
    assert response.json() == {"online_users": 7}
    assert response.headers["cache-control"] == "no-store"


def test_api_validation_error(api, monkeypatch):
    monkeypatch.setenv("AXIOM_API_KEY", "test-only-" + "x" * 32)
    monkeypatch.setattr(UserManager, "create_user", Mock(side_effect=ValueError("Invalid username")))
    assert api.post("/api/v1/users?username=bad", headers={"X-API-Key": "test-only-" + "x" * 32}).status_code == 422


def test_dashboard_served_without_embedded_secret(api):
    response = api.get("/")
    assert response.status_code == 200
    script = api.get("/app.js").text
    assert "axiom_secure_token" not in script
    assert "localStorage" not in script
    assert "provisioned successfully" not in script
    assert "frame-ancestors" in response.headers["content-security-policy"]


@pytest.mark.parametrize("admin,user,expected", [(None, 99, False), (42, None, False), (42, 99, False), (42, 42, True)])
def test_bot_authorization(admin, user, expected):
    assert AxiomTelegramBot("dummy", admin).is_authorized(user) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["status", "create_trial", "list_users"])
async def test_bot_callback_denies_non_admin(action):
    bot = AxiomTelegramBot("dummy", 42)
    bot.user_manager = Mock()
    query = SimpleNamespace(data=action, answer=AsyncMock(), edit_message_text=AsyncMock())
    update = SimpleNamespace(
        callback_query=query, effective_user=SimpleNamespace(id=99), effective_chat=SimpleNamespace(type="private")
    )
    await bot.button_handler(update, None)
    bot.user_manager.create_trial_user.assert_not_called()
    bot.user_manager.list_users.assert_not_called()
    query.edit_message_text.assert_not_called()


@pytest.mark.asyncio
async def test_bot_denies_group_even_for_admin():
    bot = AxiomTelegramBot("dummy", 42)
    bot.user_manager = Mock()
    query = SimpleNamespace(data="create_trial", answer=AsyncMock(), edit_message_text=AsyncMock())
    await bot.button_handler(
        SimpleNamespace(
            callback_query=query, effective_user=SimpleNamespace(id=42), effective_chat=SimpleNamespace(type="group")
        ),
        None,
    )
    bot.user_manager.create_trial_user.assert_not_called()


def test_bot_refuses_missing_admin():
    with pytest.raises(ValueError, match="AXIOM_BOT_ADMIN_ID"):
        AxiomTelegramBot("dummy").run()


@pytest.mark.parametrize("username", ["-root", "root\n", "../root", "ab", "USER", "foo/bar"])
def test_invalid_usernames(username):
    with pytest.raises(ValueError):
        UserManager._validate_username(username)


@pytest.mark.parametrize("password", ["short", "validpass\nroot:evil", "long:password", "long\x00password"])
def test_invalid_passwords(password):
    with pytest.raises(ValueError):
        UserManager._validate_password(password)


def test_create_rolls_back_password_failure(tmp_path, monkeypatch):
    manager = UserManager(str(tmp_path / "users.db"), str(tmp_path / "trials.db"))
    run = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr("axiom.users.manager.subprocess.run", run)
    monkeypatch.setattr(manager, "_set_password", Mock(side_effect=RuntimeError("failure")))
    with pytest.raises(RuntimeError):
        # Bypass Linux-only flock to exercise the operation on Windows too.
        manager.create_user.__wrapped__(manager, "example", "dummy-password")
    assert ["userdel", "-f", "example"] in [call.args[0] for call in run.call_args_list]
    assert manager.list_users() == []


def test_password_process_failure_is_not_success(monkeypatch):
    monkeypatch.setattr("axiom.users.manager.subprocess.run", lambda *a, **kw: SimpleNamespace(returncode=1))
    with pytest.raises(RuntimeError, match="password update failed"):
        UserManager._set_password("example", "dummy-password")


def test_trial_rolls_back_when_expiry_scheduling_fails(tmp_path, monkeypatch):
    manager = UserManager(str(tmp_path / "users.db"), str(tmp_path / "trials.db"))
    monkeypatch.setattr("axiom.users.manager.TRIAL_CLEANUP_DIR", str(tmp_path / "cleanup"))

    def run(command, **kwargs):
        if command[0] == "at":
            raise FileNotFoundError("at not installed")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("axiom.users.manager.subprocess.run", run)
    with pytest.raises(RuntimeError, match="rolled back"):
        manager.create_trial_user.__wrapped__(manager, "trial1234", "dummy-password")
    assert manager.list_users() == []
    assert manager.list_trial_users() == []


def test_restore_preflights_before_writing(tmp_path):
    archive = tmp_path / "evil.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for name in ["innocent", "../escaped"]:
            member = tarfile.TarInfo(name)
            member.size = 1
            tar.addfile(member, io.BytesIO(b"x"))
    assert not BackupEngine(str(tmp_path / "backups"), []).restore_backup(str(archive), str(tmp_path / "out"))
    assert not (tmp_path / "out" / "innocent").exists()


def test_unmanaged_account_is_protected(tmp_path, monkeypatch):
    manager = UserManager(str(tmp_path / "users.db"))
    monkeypatch.setattr(manager, "_check_system_user_protection", lambda username: None)
    with pytest.raises(PermissionError, match="not managed"):
        manager._require_managed("unrelated")


def test_root_protected():
    with pytest.raises(PermissionError):
        UserManager()._check_system_user_protection("root")


def test_backups_unique_preserve_paths_and_restore(tmp_path):
    source = tmp_path / "etc" / "axiom.toml"
    source.parent.mkdir()
    source.write_text("dummy configuration")
    engine = BackupEngine(str(tmp_path / "backups"), [str(source)])
    first, second = engine.create_backup(), engine.create_backup()
    assert first and second and first != second
    target = tmp_path / "restore"
    assert engine.restore_backup(first, str(target))
    relative = source.resolve().relative_to(source.resolve().anchor)
    assert (target / relative).read_text() == "dummy configuration"
    if os.name != "nt":
        assert Path(first).stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize(
    "name,kind",
    [
        ("../escaped", tarfile.REGTYPE),
        ("/escaped", tarfile.REGTYPE),
        ("link", tarfile.SYMTYPE),
        ("device", tarfile.CHRTYPE),
    ],
)
def test_restore_rejects_unsafe_archive(tmp_path, name, kind):
    archive = tmp_path / "evil.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        member = tarfile.TarInfo(name)
        member.type = kind
        if kind == tarfile.REGTYPE:
            member.size = 1
        member.linkname = "../escaped"
        tar.addfile(member, io.BytesIO(b"x") if member.isfile() else None)
    assert not BackupEngine(str(tmp_path / "backups"), []).restore_backup(str(archive), str(tmp_path / "out"))
    assert not (tmp_path / "escaped").exists()


def test_wireguard_fails_without_tools(monkeypatch):
    monkeypatch.setattr("axiom.services.wireguard.subprocess.check_output", Mock(side_effect=FileNotFoundError))
    with pytest.raises(RuntimeError, match="wireguard-tools"):
        WireGuardService().generate_keypair()


def test_no_public_proxy_default():
    assert SingboxService().generate_unified_config()["inbounds"][0]["listen"] == "127.0.0.1"


def test_no_default_hysteria_credential():
    with pytest.raises(ValueError):
        HysteriaService().generate_server_config([])


@pytest.mark.skipif(os.name == "nt", reason="Linux flock integration")
def test_account_lock_and_db_permissions(tmp_path, monkeypatch):
    manager = UserManager(str(tmp_path / "users.db"), str(tmp_path / "trials.db"))
    monkeypatch.setattr("axiom.users.manager.subprocess.run", lambda *args, **kwargs: SimpleNamespace(returncode=0))
    manager.create_user("example", "dummy-password")
    assert manager.list_users() == [{"username": "example", "limit": "1"}]
    assert (tmp_path / "users.db").stat().st_mode & 0o777 == 0o600

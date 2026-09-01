"""
Unit tests for Axiom user manager
"""
import os
import sys
import tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from axiom.users.manager import UserManager


def test_generate_password():
    mgr = UserManager(db_path=tempfile.mktemp())
    pwd = mgr.generate_secure_password(length=16)
    assert len(pwd) == 16
    assert any(c.isdigit() for c in pwd) or any(c.isalpha() for c in pwd)


def test_user_db_operations():
    tmp_db = tempfile.mktemp()
    mgr = UserManager(db_path=tmp_db)
    
    mgr._set_user_limit("testuser", 2)
    users = mgr.list_users()
    assert len(users) == 1
    assert users[0]["username"] == "testuser"
    assert users[0]["limit"] == "2"

    mgr._remove_from_db("testuser")
    assert len(mgr.list_users()) == 0

    if os.path.exists(tmp_db):
        os.remove(tmp_db)

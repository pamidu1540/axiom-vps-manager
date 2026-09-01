"""
Unit tests for Axiom configuration loader
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from axiom.config import load_config


def test_load_default_config():
    config = load_config()
    assert isinstance(config, dict)
    assert "axiom" in config or "ssh" in config
    if "axiom" in config:
        assert config["axiom"]["version"] == "1.0.0"


def test_config_structure():
    config = load_config()
    assert "ssh" in config or "firewall" in config


def test_custom_config_path():
    toml_content = b"""
    [axiom]
    version = "2.0.0"
    language = "pt-BR"

    [telegram]
    enabled = true
    bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    admin_chat_id = "987654321"
    """
    with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
        f.write(toml_content)
        temp_path = f.name

    try:
        cfg = load_config(temp_path)
        assert cfg["axiom"]["version"] == "2.0.0"
        assert cfg["axiom"]["language"] == "pt-BR"
        assert cfg["telegram"]["enabled"] is True
        assert cfg["telegram"]["bot_token"] == "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        assert cfg["telegram"]["admin_chat_id"] == "987654321"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_fallback_when_path_missing():
    cfg = load_config("/non/existent/path/axiom.toml")
    assert isinstance(cfg, dict)
    assert "axiom" in cfg or "ssh" in cfg

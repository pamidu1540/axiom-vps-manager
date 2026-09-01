"""
Unit tests for Axiom configuration loader
"""

import os
import sys

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

"""
Axiom Configuration Loader using Python 3.11+ native tomllib
"""
import os
import tomllib
from typing import Any, Dict, Optional

CONFIG_PATHS = [
    "/etc/axiom/axiom.toml",
    "/opt/axiom/config/axiom.toml",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "axiom.toml"),
]


def load_config(custom_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads and parses the Axiom TOML configuration file."""
    if custom_path and os.path.isfile(custom_path):
        with open(custom_path, "rb") as f:
            return tomllib.load(f)

    for path in CONFIG_PATHS:
        if os.path.isfile(path):
            with open(path, "rb") as f:
                return tomllib.load(f)

    return {
        "axiom": {"version": "1.0.0", "language": "en"},
        "ssh": {"enabled": True, "port": 22},
        "firewall": {"backend": "nftables"},
    }

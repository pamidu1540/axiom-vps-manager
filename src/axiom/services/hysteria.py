"""
Axiom Hysteria 2 Service Manager
Generates high-performance UDP/QUIC proxy configurations.
"""
import secrets
from typing import Dict, Any, List


class HysteriaService:
    def __init__(self, port: int = 8443, up_mbps: int = 100, down_mbps: int = 100, obfs_password: str = ""):
        self.port = port
        self.up_mbps = up_mbps
        self.down_mbps = down_mbps
        self.obfs_password = obfs_password or secrets.token_hex(16)

    def generate_server_config(self, auth_passwords: List[str], tls_cert: str = "/etc/caddy/axiom.crt", tls_key: str = "/etc/caddy/axiom.key") -> Dict[str, Any]:
        """Builds Hysteria 2 server configuration dictionary."""
        config = {
            "listen": f":{self.port}",
            "tls": {
                "cert": tls_cert,
                "key": tls_key
            },
            "obfs": {
                "type": "salamander",
                "salamander": {
                    "password": self.obfs_password
                }
            },
            "auth": {
                "type": "password",
                "password": auth_passwords[0] if auth_passwords else "default_secret"
            },
            "bandwidth": {
                "up": f"{self.up_mbps} mbps",
                "down": f"{self.down_mbps} mbps"
            }
        }
        return config

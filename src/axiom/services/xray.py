"""
Axiom Xray Service Manager
Generates VLESS + REALITY configuration profiles for censorship circumvention.
"""
import uuid
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger("AxiomXray")


class XrayService:
    def __init__(self, port: int = 443, dest: str = "www.google.com:443", server_names: List[str] = None):
        self.port = port
        self.dest = dest
        self.server_names = server_names or ["www.google.com", "google.com"]

    def generate_reality_config(self, clients: List[Dict[str, str]], private_key: str, short_id: str) -> Dict[str, Any]:
        """Builds a complete server-side Xray VLESS-REALITY configuration."""
        inbound_clients = [{"id": c.get("uuid", str(uuid.uuid4())), "flow": "xtls-rprx-vision"} for c in clients]
        if not inbound_clients:
            inbound_clients = [{"id": str(uuid.uuid4()), "flow": "xtls-rprx-vision"}]

        config = {
            "log": {"loglevel": "warning"},
            "inbounds": [
                {
                    "port": self.port,
                    "protocol": "vless",
                    "settings": {
                        "clients": inbound_clients,
                        "decryption": "none"
                    },
                    "streamSettings": {
                        "network": "tcp",
                        "security": "reality",
                        "realitySettings": {
                            "show": False,
                            "dest": self.dest,
                            "xver": 0,
                            "serverNames": self.server_names,
                            "privateKey": private_key,
                            "shortIds": [short_id]
                        }
                    }
                }
            ],
            "outbounds": [
                {"protocol": "freedom", "tag": "direct"},
                {"protocol": "blackhole", "tag": "block"}
            ]
        }
        return config

    def generate_client_uri(self, client_uuid: str, server_ip: str, public_key: str, short_id: str, sni: str = "www.google.com") -> str:
        """Constructs a VLESS Reality sharing URI."""
        return (
            f"vless://{client_uuid}@{server_ip}:{self.port}?"
            f"encryption=none&flow=xtls-rprx-vision&security=reality&sni={sni}&"
            f"fp=chrome&pbk={public_key}&sid={short_id}&type=tcp#Axiom-VLESS-Reality"
        )

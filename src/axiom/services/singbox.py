"""
Axiom sing-box Universal Platform Manager
Builds unified JSON configurations for multi-inbound proxy routing.
"""
from typing import Dict, Any, List


class SingboxService:
    def __init__(self, clash_api_port: int = 9090):
        self.clash_api_port = clash_api_port

    def generate_unified_config(self, inbounds: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Builds a complete sing-box configuration with unified inbounds and outbounds."""
        config = {
            "log": {
                "level": "warn",
                "timestamp": True
            },
            "experimental": {
                "clash_api": {
                    "external_controller": f"127.0.0.1:{self.clash_api_port}"
                }
            },
            "inbounds": inbounds or [
                {
                    "type": "mixed",
                    "tag": "mixed-in",
                    "listen": "::",
                    "listen_port": 1080
                }
            ],
            "outbounds": [
                {
                    "type": "direct",
                    "tag": "direct"
                },
                {
                    "type": "block",
                    "tag": "block"
                }
            ],
            "route": {
                "rules": [
                    {
                        "protocol": "dns",
                        "outbound": "direct"
                    }
                ]
            }
        }
        return config

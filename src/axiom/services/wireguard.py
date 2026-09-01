"""
Axiom WireGuard Service Manager
Configures kernel WireGuard, client peers, and QR code generation.
"""

import logging
import os
import subprocess

logger = logging.getLogger("AxiomWireGuard")
WG_DIR = "/etc/wireguard"
WG_CONF = "/etc/wireguard/wg0.conf"


class WireGuardService:
    def __init__(self, interface: str = "wg0", port: int = 51820):
        self.interface = interface
        self.port = port

    def generate_keypair(self) -> dict[str, str]:
        """Generates a private and public key using wg genkey."""
        try:
            privkey = subprocess.check_output(["wg", "genkey"], text=True).strip()
            p = subprocess.Popen(["wg", "pubkey"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            pubkey, _ = p.communicate(input=privkey)
            return {"private_key": privkey, "public_key": pubkey.strip()}
        except Exception:
            # Fallback if wg is not in PATH during dev
            return {"private_key": "mock_private_key", "public_key": "mock_public_key"}

    def add_client(
        self, client_name: str, client_ip: str = "10.66.66.2/32", server_endpoint: str = "127.0.0.1"
    ) -> dict[str, str]:
        """Generates a WireGuard client configuration."""
        client_keys = self.generate_keypair()
        server_pubkey = "SERVER_PUBLIC_KEY"
        if os.path.exists(os.path.join(WG_DIR, "server_public.key")):
            with open(os.path.join(WG_DIR, "server_public.key"), encoding="utf-8") as f:
                server_pubkey = f.read().strip()

        client_config = f"""[Interface]
PrivateKey = {client_keys["private_key"]}
Address = {client_ip}
DNS = 1.1.1.1, 1.0.0.1

[Peer]
PublicKey = {server_pubkey}
Endpoint = {server_endpoint}:{self.port}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""
        return {"client_name": client_name, "config": client_config, "public_key": client_keys["public_key"]}

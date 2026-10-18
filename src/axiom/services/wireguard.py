"""
Axiom WireGuard Service Manager
Configures kernel WireGuard, client peers, and QR code generation.
"""

import ipaddress
import logging
import os
import re
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
            if p.returncode or not privkey or not pubkey.strip():
                raise RuntimeError("WireGuard key generation failed")
            return {"private_key": privkey, "public_key": pubkey.strip()}
        except OSError as exc:
            raise RuntimeError("Install wireguard-tools before generating profiles") from exc

    def add_client(self, client_name: str, client_ip: str, server_endpoint: str) -> dict[str, str]:
        """Generates a profile only; the returned public key must be registered on the server."""
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", client_name):
            raise ValueError("Invalid client name")
        ipaddress.ip_interface(client_ip)
        if not server_endpoint or any(c in server_endpoint for c in "\r\n\x00"):
            raise ValueError("Supply a server hostname or IP address")
        if not 1 <= self.port <= 65535:
            raise ValueError("Invalid WireGuard port")
        with open(os.path.join(WG_DIR, "server_public.key"), encoding="utf-8") as f:
            server_pubkey = f.read().strip()
        if not re.fullmatch(r"[A-Za-z0-9+/]{43}=", server_pubkey):
            raise ValueError("Server public key is missing or invalid")
        client_keys = self.generate_keypair()
        if ":" in server_endpoint and not server_endpoint.startswith("["):
            server_endpoint = f"[{server_endpoint}]"

        client_config = f"""[Interface]
PrivateKey = {client_keys["private_key"]}
Address = {client_ip}
DNS = 1.1.1.1, 1.0.0.1

[Peer]
PublicKey = {server_pubkey}
Endpoint = {server_endpoint}:{self.port}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
        return {"client_name": client_name, "config": client_config, "public_key": client_keys["public_key"]}

"""
Axiom nftables Firewall Manager
Manages isolated nftables chains for ports, rate limits, and GeoIP filters without flushing base system rules.
"""

import logging
import subprocess

logger = logging.getLogger("AxiomFirewall")

NFT_BASE_TEMPLATE = """#!/usr/sbin/nft -f
# Axiom VPS Manager — Isolated Firewall Table

table inet axiom {
    set banned_ips {
        type ipv4_addr
        flags timeout
    }

    chain input {
        type filter hook input priority 0; policy accept;

        # Allow loopback
        iif lo accept

        # Allow established / related
        ct state established,related accept

        # Drop invalid packets
        ct state invalid drop

        # Rate-limiting SSH brute-force (max 10 new connections / min per IP)
        tcp dport 22 ct state new meter ssh_meter { ip saddr limit rate 10/minute } accept
        tcp dport 22 ct state new drop
    }

    chain forward {
        type filter hook forward priority 0; policy accept;
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}
"""


class NFTablesManager:
    def __init__(self, nft_rules_path: str = "/etc/nftables.d/axiom.nft"):
        self.nft_rules_path = nft_rules_path

    def apply_base_firewall(self) -> bool:
        """Applies the default hardened Axiom nftables ruleset."""
        try:
            p = subprocess.Popen(
                ["nft", "-f", "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            stdout, stderr = p.communicate(input=NFT_BASE_TEMPLATE)
            if p.returncode == 0:
                logger.info("Successfully applied nftables ruleset.")
                return True
            else:
                logger.error("Failed to apply nftables: %s", stderr)
                return False
        except Exception as e:
            logger.error("nftables invocation error: %s", e)
            return False

    def ban_ip(self, ip_address: str, timeout_seconds: int = 3600) -> bool:
        """Adds an IP address to the temporary ban set."""
        cmd = ["nft", "add", "element", "inet", "axiom", "banned_ips", f"{{ {ip_address} timeout {timeout_seconds}s }}"]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0

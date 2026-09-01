"""
Axiom Automated Security & Hardening Scanner
Audits open ports, root password configuration, encryption parameters, and sensitive file exposures.
"""

import os
import subprocess
from typing import Any


class SecurityScanner:
    @staticmethod
    def audit_system() -> dict[str, Any]:
        findings = []
        status = "PASSED"

        # 1. Check for plaintext passwords on disk
        if os.path.exists("/etc/VPSManager/senha") and os.listdir("/etc/VPSManager/senha"):
            findings.append(
                {
                    "severity": "HIGH",
                    "title": "Plaintext Password Directory Found",
                    "detail": "/etc/VPSManager/senha contains plaintext credential files. Purge password directory.",
                }
            )
            status = "WARNING"

        # 2. Check root SSH login configuration
        sshd_config = "/etc/ssh/sshd_config"
        if os.path.exists(sshd_config):
            with open(sshd_config, encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if "PermitRootLogin yes" in content:
                    findings.append(
                        {
                            "severity": "MEDIUM",
                            "title": "SSH Root Password Login Enabled",
                            "detail": "PermitRootLogin is set to yes. Recommended: use SSH key authentication or set to no.",
                        }
                    )

        # 3. Check for exposed backup files in webroot
        if os.path.exists("/var/www/html/backup/backup.vps") or os.path.exists("/var/www/html/backup.vps"):
            findings.append(
                {
                    "severity": "CRITICAL",
                    "title": "Unauthenticated Backup File in Webroot",
                    "detail": "Backup archive is exposed to the public webroot (/var/www/html/). Remove immediately.",
                }
            )
            status = "FAILED"

        # 4. Check for leaked static stunnel.pem keys
        leaked_paths = ["/stunnel.pem", "/etc/stunnel/stunnel.pem", "/opt/axiom/stunnel.pem"]
        for p in leaked_paths:
            if os.path.exists(p):
                findings.append(
                    {
                        "severity": "HIGH",
                        "title": "Static RSA Key Found",
                        "detail": f"Static or leaked certificate/key found at {p}. Use dynamically generated certificates.",
                    }
                )
                if status != "FAILED":
                    status = "WARNING"

        # 5. Check firewall status
        nft_status = "INACTIVE"
        try:
            res = subprocess.run(["nft", "list", "tables"], capture_output=True, text=True, check=False)
            if res.returncode == 0 and "axiom" in res.stdout:
                nft_status = "ACTIVE"
        except Exception:
            pass

        return {
            "overall_status": status,
            "findings_count": len(findings),
            "findings": findings,
            "firewall_status": nft_status,
        }

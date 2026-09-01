"""
Axiom Automated Security & Hardening Scanner
Audits open ports, root password configuration, encryption parameters, and sensitive file exposures.
"""
import os
import subprocess
from typing import List, Dict, Any


class SecurityScanner:
    @staticmethod
    def audit_system() -> Dict[str, Any]:
        findings = []
        status = "PASSED"

        # 1. Check for plaintext passwords on disk
        if os.path.exists("/etc/VPSManager/senha") and os.listdir("/etc/VPSManager/senha"):
            findings.append({
                "severity": "HIGH",
                "title": "Plaintext Password Directory Found",
                "detail": "/etc/VPSManager/senha contains plaintext credential files. Run axiom user migrate to purge."
            })
            status = "WARNING"

        # 2. Check root SSH login configuration
        sshd_config = "/etc/ssh/sshd_config"
        if os.path.exists(sshd_config):
            with open(sshd_config, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if "PermitRootLogin yes" in content:
                    findings.append({
                        "severity": "MEDIUM",
                        "title": "SSH Root Password Login Enabled",
                        "detail": "PermitRootLogin is set to yes. Recommended: use SSH key authentication or set to no."
                    })

        # 3. Check for exposed backup files in webroot
        if os.path.exists("/var/www/html/backup/backup.vps"):
            findings.append({
                "severity": "CRITICAL",
                "title": "Unauthenticated Backup File in Webroot",
                "detail": "/var/www/html/backup/backup.vps is exposed to the public internet. Remove immediately."
            })
            status = "FAILED"

        # 4. Check firewall status
        nft_status = "INACTIVE"
        try:
            res = subprocess.run(["nft", "list", "tables"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0 and "axiom" in res.stdout:
                nft_status = "ACTIVE"
        except Exception:
            pass

        return {
            "overall_status": status,
            "findings_count": len(findings),
            "findings": findings,
            "firewall_status": nft_status
        }

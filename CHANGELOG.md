# 📋 Changelog

All notable changes to the **Axiom VPS Manager** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.2] - 2026-09-05

### 🚀 Added
- **VM Boot & Console Auto-Launch**:
  - Interactive root logins directly present the Axiom dashboard instead of standard shell prompts (/etc/profile.d/axiom.sh and /root/.bashrc).
  - Strict guard condition guarantees non-interactive tools (SFTP, SCP, automated rsync, Git) remain completely uninterrupted.
  - Option 27 (autoexec) provides an instant interactive toggle to enable or disable the boot auto-launch behavior with live state reporting.
  - Branded node banner added to /etc/issue.net and /etc/motd.
- **CI/CD GitHub Actions Workflow**:
  - Added .github/workflows/ci.yml running automated pipeline jobs on every push and pull request.
  - Automated static syntax checking (bash -n) across all shell scripts in the repository.
  - Automated executable permission validation for installer, uninstaller, and all modules.
  - Automated Python code quality linting via ruff check and test suite execution.

### 🛡️ Fixed & Hardened
- **Pervasive Pipefail Crash Loops Resolved**:
  - Eliminated dangerous set -euo pipefail from lib/axiom-common.sh and all 32 module scripts that previously caused silent aborts on benign non-zero subshell exits.
- **Universal netstat Fallback**:
  - Added seamless ss wrapper fallback in lib/axiom-common.sh for modern Linux distributions (Debian 12+ and Ubuntu 24.04 LTS) where legacy net-tools is not pre-installed.
- **Menu Recursion Traps Fixed**:
  - Corrected return mechanisms across Modulos/conexao, limit1, limit2, and autoexec so options cleanly yield control back to the event loop rather than spawning nested subshells.
- **Interactive Validation & Reprompting**:
  - Modulos/addhost: Automatically normalizes payloads by prepending . when omitted; supports 0 or q to safely cancel without modifying squid configurations.
  - Modulos/delhost: Accepts both .domain and domain format; supports clean cancellation.
  - Modulos/senharoot: Added input verification loops with confirmation matching and root permission assertions.
  - Modulos/remover: Guard against accidental deletion of system accounts (UID < 1000) with interactive notice and graceful exit options.
  - Modulos/userbackup: Error-tolerant file copying ensuring partial missing configurations do not break archive creation.
  - Modulos/detalhes: Sanitized CPU core count and RAM usage calculations.
  - Modulos/ajuda: Completely overhauled command reference documentation matching all 30 options.
- **Uninstaller Safety**:
  - Complete cleanup of /etc/axiom/autolaunch, /root/.bashrc hooks, and firewall chains during uninstallation.

---

## [1.0.1] - 2026-09-04

### 🛡️ Hardened
- **Zero Telemetry & Integrity Verification**: Removed all legacy phone-home calls, anti-tamper logic bombs, and external IP verification scripts.
- **Modern Cryptography**: Migrated user authentication to Argon2id and SHA-512; eliminated plaintext credential storage.
- **Firewall Isolation**: Replaced destructive iptables flushes with isolated AXIOM_TORRENT and AXIOM_NFT chains.
- **Asynchronous Telegram Bot**: Updated bot core to python-telegram-bot v22.8 with interactive conversational wizards.

---

## [1.0.0] - 2026-09-01

### 🎉 Initial Release
- Initial public release of Axiom VPS Manager.
- Multi-protocol proxy, VPN, and secure tunneling management for Debian and Ubuntu servers.

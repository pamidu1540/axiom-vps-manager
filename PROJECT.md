# Project: Axiom VPS Manager Exhaustive Security, Functional & Logical Audit

## Architecture
Axiom VPS Manager is a high-performance VPS management suite featuring dual Shell/Python interfaces:
- **Shell Layer (`Modulos/*`, `lib/*`, `Install/*`)**: 30 modular bash utilities offering interactive menu-driven VPS administration.
- **Python Backend (`src/axiom/*`)**: Structured modular Python package handling user accounts, system monitoring, service management, backup orchestration, security scanning, and asynchronous Telegram bot automation.
- **Service & Infrastructure Layer (`systemd/*`)**: Systemd unit files and background daemons for connection limiting, BadVPN UDP gateway, automatic backups, and WebSocket/SSH multiplexing.
- **Web UI & Asset Layer (`web/*`)**: Lightweight management dashboard interface verified with Biome and HTMLHint.

---

## Feature Inventory

Every feature across all 30 subtasks is enumerated below with assigned milestones and survey source:

| # | Task / Feature | Description | Milestone | Source |
|---|---|---|---|---|
| 1 | Task 01: criarusuario | User creation, Argon2id/SHA-512 hashing, chage expiry, limit registration in /root/usuarios.db, input validation | M1 | Survey P1 |
| 2 | Task 02: criarteste | Temporary trial account creation, automated expiration sweep, session cleanup, database isolation | M1 | Survey P1 |
| 3 | Task 03: remover | Single & batch user removal, pkill -u, userdel -f, UID >= 1000 safety guard, OpenVPN cert revocation | M1 | Survey P1 |
| 4 | Task 04: sshmonitor | Active SSH/Dropbear/OpenVPN counting, PID tracking, session elapsed timer, zero license checks | M1 | Survey P1 |
| 5 | Task 05: mudardata | Account expiration date extension (relative & YYYY-MM-DD), chage -E execution, input sanitization | M1 | Survey P1 |
| 6 | Task 06: alterarlimite | Connection limit modification in /root/usuarios.db, positive integer validation, atomic same-mount file updates | M1 | Survey P1 |
| 7 | Task 07: alterarsenha | Password changes via chpasswd, silent inputs, session termination, zero plaintext leaks | M1 | Survey P1 |
| 8 | Task 08: expcleaner | Expired account batch purging, UID >= 1000 system protection, OpenVPN CRL regen, /etc/VPSManager/Exp cleanup | M1 | Survey P1 |
| 9 | Task 09: infousers | User audit reporting, expiration calculation, active connection counting | M1 | Survey P1 |
| 10 | Task 10: conexao | Multi-protocol modes (Squid, Dropbear, OpenVPN, Stunnel4 dynamic RSA, SSLH, SlowDNS), remove license/killswitches, remove Apache webroot exposure, remove destructive iptables -F, secure mktemp | M2 | Survey P2 |
| 11 | Task 11: speedtest / velocity | Internet speed and latency benchmarking with automatic fallback | M2 | Survey P2 |
| 12 | Task 12: banner | SSH login banner creation, color formatting, /etc/bannerssh handling, Dropbear integration, fix HTML trailing tags | M2 | Survey P2 |
| 13 | Task 13: nload | Real-time network interface bandwidth visualization and dependency auto-installer | M2 | Survey P2 |
| 14 | Task 14: otimizar | RAM buffer/cache drop, swap memory recycling with safety thresholds, package cache cleaning | M2 | Survey P2 |
| 15 | Task 15: userbackup | Encrypted local archive generation (/root/backups/), chmod 600, non-interactive CLI argument support for systemd | M2 | Survey P2 |
| 16 | Task 16: limiter / limit_ssh | Background connection limiter daemon, selective excess session pruning without killing active connections, systemd unit | M2 | Survey P2 |
| 17 | Task 17: badvpn | BadVPN UDP Gateway daemon on port 7300, local binary deployment with SHA256 integrity verification, systemd integration | M2 | Survey P2 |
| 18 | Task 18: detalhes | System hardware inspection, CPU architecture (uname -m), RAM consumption, live TCP/UDP port enumeration (ss -tulpn) | M2 | Survey P2 |
| 19 | Task 19: menu2 | Secondary menu navigation, status indicators (/etc/axiom/torrent_blocked sync, $stsbot, $autm), screen transitions | M3 | Survey P3 |
| 20 | Task 20: addhost | Squid Proxy payload domain addition, escaped regex matching, file permissions preservation, proxy reload | M3 | Survey P3 |
| 21 | Task 21: delhost | Squid Proxy payload domain removal, input validation, escaped regex matching, proxy reload | M3 | Survey P3 |
| 22 | Task 22: reiniciarsistema | System reboot confirmation prompt [y/N] before executing reboot | M3 | Survey P3 |
| 23 | Task 23: reiniciarservicos | Graceful service restarts across OpenSSH, Caddy, WireGuard, Xray, Hysteria, Dropbear, Squid, and Axiom proxies | M3 | Survey P3 |
| 24 | Task 24: blockt | P2P/BitTorrent traffic filtering using dedicated AXIOM_TORRENT chain without flushing primary tables | M3 | Survey P3 |
| 25 | Task 25: botssh / axiom-bot | Async Telegram bot (python-telegram-bot v22.8), admin authorization enforcement, __main__ entrypoint, purge plaintext /etc/VPSManager/senha/ writes | M3 | Survey P3 |
| 26 | Task 26: senharoot | Root password updater with silent input entry, confirmation matching, and chpasswd invocation | M3 | Survey P3 |
| 27 | Task 27: autoexec | SSH login auto-run toggle in /etc/profile with safe idempotency, typo fixes | M3 | Survey P3 |
| 28 | Task 28: attscript / verifatt | Version manifest comparison against GitHub release endpoints and non-destructive updater invocation | M3 | Survey P3 |
| 29 | Task 29: delscript / uninstall.sh | Safe uninstaller with pre-removal backup prompt, systemd unit disabling, cron cleanup, firewall teardown, /etc/profile cleanup | M3 | Survey P3 |
| 30 | Task 30: menu | Primary menu return and dispatch handling | M3 | Survey P3 |
| 31 | Repository Hygiene & Security Cleanup | Delete committed stunnel.pem private key from repo root; purge legacy killswitch lines across all scripts | M3 | Survey P2/P3 |
| 32 | Test Infrastructure: Tiers 1-4 | Requirement-driven opaque-box test suite across 4 tiers covering all 30 tasks, Python pytest suite expansion, static linters | M4 | Survey P1/P2/P3 |
| 33 | Final Acceptance & Adversarial Verification | 100% E2E test suite pass + Challenger adversarial test coverage + Forensic Integrity Audit | M5 | Survey P1/P2/P3 |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| M1 | Phase 1: User & Account Management | Tasks 01–09 (`criarusuario`, `criarteste`, `remover`, `sshmonitor`, `mudardata`, `alterarlimite`, `alterarsenha`, `expcleaner`, `infousers`, `src/axiom/users/*`) | none | PLANNED |
| M2 | Phase 2: Protocols, Tunnels & Network | Tasks 10–18 (`conexao`, `speedtest`, `banner`, `nload`, `otimizar`, `userbackup`, `limiter`, `badvpn`, `detalhes`, service daemons) | none | PLANNED |
| M3 | Phase 3: Advanced Operations & Security | Tasks 19–30 (`menu2`, `addhost`, `delhost`, `reiniciarsistema`, `reiniciarservicos`, `blockt`, `botssh`, `senharoot`, `autoexec`, `attscript`, `delscript`, `menu`, stunnel.pem cleanup) | none | PLANNED |
| M4 | E2E Testing Track | Comprehensive 4-Tier Test Suite (`tests/e2e/`, expanded `tests/test_*.py`, test runner, `TEST_READY.md`) | none (Parallel) | PLANNED |
| M5 | Final Milestone: Full Acceptance & Adversarial Hardening | Pass 100% E2E tests (Tiers 1-4) + Tier 5 Adversarial Hardening + Forensic Integrity Audit | M1, M2, M3, M4 | PLANNED |

---

## Interface Contracts

### 1. User Database Format (`/root/usuarios.db`)
- Line format: `<username> <connection_limit>`
- Atomic updates: Temp file created in same directory (`mktemp /root/usuarios.db.XXXXXX` or in-place atomic rewrite)
- Safe parsing: Only parse lines matching `^[a-zA-Z0-9_-]+\s+[0-9]+$`

### 2. Trial Database Format (`/etc/VPSManager/trial_users.db`)
- Line format: `<username> <expiration_epoch> <limit>`
- Fallback sweep: Processed by `expcleaner` / `limiter` when `atd` is unavailable.

### 3. OpenVPN PKI Contract
- PKI directory: `/etc/openvpn/easy-rsa/pki/`
- Revocation: `./easyrsa --batch revoke <user>` followed by `./easyrsa gen-crl`
- CRL path: `/etc/openvpn/crl.pem` with permissions `644` or `nobody:nogroup` / `nobody:nobody`

### 4. Firewall Torrent Chain Contract
- Chain name: `AXIOM_TORRENT`
- Jumps: `iptables -I FORWARD -j AXIOM_TORRENT`, `iptables -I OUTPUT -j AXIOM_TORRENT`
- Flag file: `/etc/axiom/torrent_blocked` (standardized across `blockt`, `menu2`, and `uninstall.sh`)

### 5. Python API Interface
- `src/axiom/users/manager.py`: `UserManager` must implement `create_user`, `create_trial_user`, `delete_user`, `change_password`, `change_limit`, `change_expiration`, `get_user_info`, `list_users`, `purge_expired`
- `src/axiom/telegram/bot.py`: Admin authorization check on all sensitive callbacks; executable as module `python3 -m axiom.telegram.bot`.

---

## Code Layout

- Shell modules: `Modulos/` (`Modulos/criarusuario`, `Modulos/conexao`, `Modulos/menu`, etc.)
- Shared Shell libraries: `lib/` (`lib/axiom-common.sh`)
- Installation & Helper scripts: `Install/`, `Sistema/`, `install.sh`, `uninstall.sh`, `senharoot.sh`
- Python source: `src/axiom/`
  - `src/axiom/users/`: `manager.py`, `backup.py`
  - `src/axiom/monitor/`: `stats.py`, `bandwidth.py`
  - `src/axiom/services/`: `wireguard.py`, `xray.py`, `hysteria.py`, `singbox.py`
  - `src/axiom/security/`: `scanner.py`
  - `src/axiom/telegram/`: `bot.py`
  - `src/axiom/config.py`, `src/axiom/cli.py`
- Systemd units: `systemd/` (`axiom-backup.service`, `axiom-limiter.service`, `axiom-badvpn.service`, `axiom-bot.service`, etc.)
- Test suite: `tests/` (`tests/test_users.py`, `tests/test_services.py`, `tests/test_scanner.py`, `tests/test_config.py`, `tests/test_bot.py`, `tests/test_backup.py`, `tests/test_monitor.py`, `tests/e2e/`)
- Web UI: `web/` (`index.html`, `app.js`, `style.css`)
- Agent coordination: `.agents/` (metadata only)

# Survey & Investigation Report: Phase 3 (Tasks 19–30) & Test Infrastructure
**Project**: Axiom VPS Manager
**Date**: 2026-09-01
**Author**: Survey Explorer (Phase 3 & Test Infrastructure)

---

## 1. Executive Summary

This report delivers an exhaustive, multi-dimensional logical, functional, and security audit of **Phase 3: Advanced Operations, Security & Lifecycle (Tasks 19–30)** and the **Quality & Test Infrastructure** of Axiom VPS Manager.

The codebase exhibits a dual-architecture state:
1. **Modern Python Core (`src/axiom/`)**: Well-structured modular Python 3.13 packages (FastAPI, Pydantic, python-telegram-bot v22.8, Rich, nftables manager, security scanner).
2. **Modular Bash Operations (`Modulos/`, `Install/`, `lib/`, `Sistema/`)**: Production shell scripts delivering terminal TUI menus, service controllers, firewall managers, and legacy bridges.

All 52 shell scripts passed `bash -n` static syntax validation. Python components pass `ruff check` and existing `pytest` tests pass. Web assets pass `biome check` and `htmlhint`. However, critical security remnants (hardcoded private key `stunnel.pem`, `/usr/lib/licence` killswitch checks, and plaintext password storage in legacy scripts) and specific logical defects (unconfirmed reboot in `reiniciarsistema`, unauthenticated bot endpoints, and uncleaned `/etc/profile` in `uninstall.sh`) were discovered and documented with actionable remediations.

---

## 2. Exhaustive Task Survey (Tasks 19–30)

| Task | Command / Module | Primary File Locations | Functional Status | Security / Logic Findings |
|---|---|---|---|---|
| **Task 19** | `menu2` | `Modulos/menu` (lines 139–249) | **Working with UI Bugs** | Indicator `$stsf` checks `/etc/Plus-torrent` while `blockt` sets `/etc/axiom/torrent_blocked`. Variables `$stsbot` and `$autm` displayed but uncalculated. |
| **Task 20** | `addhost` | `Modulos/addhost` | **Working with Caveat** | Regex wildcard risk with unescaped `.` in `grep -q "^$host"`. `mktemp` + `mv` reduces payload file permissions to `0600` (blocking squid read). |
| **Task 21** | `delhost` | `Modulos/delhost` | **Working with Caveat** | Regex wildcard risk in `grep -v "^$host"`. `mktemp` + `mv` reduces payload permissions to `0600`. |
| **Task 22** | `reiniciarsistema` | `Modulos/reiniciarsistema` | **Defective (Safety Gap)** | Immediate `shutdown -r now` without user confirmation prompt. Accidental menu selection causes immediate disruption. |
| **Task 23** | `reiniciarservicos` | `Modulos/reiniciarservicos` | **Working (Robust)** | Restarts active/enabled services across OpenSSH, Caddy, WireGuard, Xray, Hysteria, Dropbear, Squid, Stunnel4, Axiom daemons cleanly. |
| **Task 24** | `blockt` | `Modulos/blockt` | **Working (Robust)** | Dedicated `AXIOM_TORRENT` chain. Filters TCP/UDP 6881–6889, 51413. Clean teardown without flushing base iptables rules. |
| **Task 25** | `botssh` / `axiom-bot` | `src/axiom/telegram/bot.py`, `systemd/axiom-bot.service`, `Modulos/botssh`, `Modulos/bot`, `Modulos/botgen`, `Modulos/botgerador` | **Security Issues in Legacy; Minor Gap in Python** | Python: `list_users` callback missing admin auth; missing `if __name__ == "__main__":` for systemd. Legacy `Modulos/bot`: line 10 license bomb `[[ ! -e /usr/lib/licence ]] && exit 0`; plaintext passwords written to `/etc/VPSManager/senha/`; weak DES crypt. |
| **Task 26** | `senharoot` | `Modulos/senharoot`, `senharoot.sh` | **Working (Secure)** | Silent dual input entry (`read -s`), length check (>=8 chars), piped to `chpasswd`. Zero plaintext leaks. `senharoot.sh` configures `sshd_config` and self-deletes. |
| **Task 27** | `autoexec` | `Modulos/menu` (lines 109–137) | **Working with Typo** | Idempotent toggle of `menu;` in `/etc/profile`. Typo on line 124: `A◇ㅤCTIVATING` instead of `◇ㅤACTIVATING`. |
| **Task 28** | `attscript` / `verifatt` | `Modulos/attscript`, `Modulos/verifatt`, `Install/versao`, `Sistema/versao` | **Working** | Manifest comparison against repository release endpoint. Non-destructive update flow re-running `install.sh`. `verifatt` provides silent cron checks. |
| **Task 29** | `delscript` / `uninstall.sh` | `Modulos/delscript`, `uninstall.sh` | **Working with Cleanup Gap** | Root check, interactive `[y/N]` prompt, backup option (`chmod 600`), systemd disable/remove, safe cron cleaning (`mktemp`), firewall table deletion, binary removal. Gap: does not clean `menu;` from `/etc/profile`. |
| **Task 30** | `menu` | `Modulos/menu` (lines 30–108, 250–421) | **Working (Robust)** | Primary dispatcher covering options 01–19, 00/0. Smooth bidirectional transitions with `menu2` (Option 19 -> menu2; Option 30 -> menu). |

---

## 3. Global Security, Vulnerability & Integrity Audit

### Critical & High Severity Security Findings

1. **Static Hardcoded Private Key and Certificate in Repository (`stunnel.pem`)**
   - **Location**: `stunnel.pem` (repo root)
   - **Detail**: Contains a 2048-bit RSA Private Key and Cloudflare Origin CA certificate for `*.kiritossh.xyz`.
   - **Risk**: Violates acceptance criteria ("zero unauthenticated private keys/certificates") and exposes private cryptographic key material.
   - **Remediation**: Remove `stunnel.pem` from Git tracking and repository root. Use dynamic on-demand self-signed or Let's Encrypt certificate generation via `openssl req` / Caddy.

2. **Anti-Tamper & License Bomb Remnants**
   - **Locations**:
     - `Modulos/bot`: line 10: `[[ ! -e /usr/lib/licence ]] && exit 0`
     - `Modulos/conexao`: line 12: `[[ $(awk -F" " '{print $2}' /usr/lib/licence) == "@DRAGON_VPS_MANAGER" ]] && {`
   - **Detail**: Scripts immediately terminate or branch if `/usr/lib/licence` is absent or does not match a hardcoded string.
   - **Risk**: Denial of service and unexpected operational failure on clean systems.
   - **Remediation**: Remove all references to `/usr/lib/licence`.

3. **Plaintext Password Storage in Legacy Modules**
   - **Locations**: `Modulos/bot`, `Modulos/botgerador`, `Install/list`
   - **Detail**: Plaintext passwords saved into `/etc/VPSManager/senha/$usuario`.
   - **Remediation**: Remove plaintext credential caching completely. Rely solely on standard Linux PAM / shadow authentication.

4. **Missing Authorization on Telegram Bot Administrative Handlers**
   - **Location**: `src/axiom/telegram/bot.py` (lines 73–78)
   - **Detail**: The `list_users` callback query handler dumps system usernames without verifying `update.effective_user.id == self.admin_id`.
   - **Remediation**: Add admin ID verification decorator or conditional check before executing administrative actions.

5. **Squid Whitelist File Permissions Downgrade**
   - **Locations**: `Modulos/addhost` (line 41), `Modulos/delhost` (line 35)
   - **Detail**: `mktemp` creates temporary files with `0600` permissions. Overwriting `/etc/squid/payload.txt` via `mv` leaves it readable only by root, preventing Squid daemon (`proxy` user) from reading whitelist rules.
   - **Remediation**: Add explicit `chmod 644 "$payload"` after updating.

---

## 4. Test Suite Architecture & Coverage Gap Analysis

### 4-Tier Test Architecture Status

```
+-------------------------------------------------------------------------+
| Tier 1: Static Linting & Syntax Verification                            |
| [PASS] bash -n (52 shell scripts)                                       |
| [PASS] ruff check (Python 3.13)                                         |
| [PASS] biome check & htmlhint (Web assets)                              |
+-------------------------------------------------------------------------+
| Tier 2: Unit Testing (pytest)                                           |
| [PASS] test_config.py (2 tests)                                         |
| [PASS] test_scanner.py (1 test)                                         |
| [PASS] test_services.py (3 tests - Xray, Hysteria, Singbox)             |
| [PASS] test_users.py (2 tests - Password gen, DB CRUD)                  |
| [GAP]  10 Python modules lack dedicated unit tests                      |
+-------------------------------------------------------------------------+
| Tier 3: Functional / Component Integration Testing                      |
| [GAP]  No mock test harnesses for bash scripts (iptables, systemctl)    |
| [GAP]  No CLI subparser execution tests                                 |
+-------------------------------------------------------------------------+
| Tier 4: End-to-End Lifecycle & Security Verification                    |
| [GAP]  No automated E2E test verifying install -> manage -> uninstall   |
+-------------------------------------------------------------------------+
```

### Coverage Gaps in Python Modules (`src/axiom/`):
1. `src/axiom/telegram/bot.py`: Test bot initialization, token format validation, admin auth enforcement, and mock update handling.
2. `src/axiom/firewall/nft_manager.py`: Test nftables ruleset template generation and IP ban command formatting.
3. `src/axiom/monitor/bandwidth.py`: Test JSON parsing of vnstat output and fallback handling.
4. `src/axiom/monitor/stats.py`: Test `/proc/meminfo` parser, disk metrics calculation, and fallback values.
5. `src/axiom/services/wireguard.py`: Test keypair generation and client configuration format.
6. `src/axiom/services/qrcode_gen.py`: Test ASCII QR code generation and PNG export fallback.
7. `src/axiom/users/backup.py`: Test archive creation, permission mask (`0600`), and backup listing.
8. `src/axiom/api/server.py`: Test FastAPI test client, token header verification (200 vs 401), and endpoint responses.
9. `src/axiom/cli.py`: Test argparse argument parsing for all subcommands.
10. `src/axiom/tui/dashboard.py`: Test Rich table rendering and plaintext fallback.

---

## 5. Recommended Remediation & Implementation Plan

### Phase 3 Remediation Roadmap

1. **Reboot Confirmation (Task 22)**:
   - Update `Modulos/reiniciarsistema` to require explicit interactive confirmation (`[y/N]`).
2. **Telegram Bot Enhancements (Task 25)**:
   - Add `if __name__ == "__main__":` entrypoint to `src/axiom/telegram/bot.py` reading environment variables (`AXIOM_BOT_TOKEN`, `AXIOM_BOT_ADMIN_ID`).
   - Add `is_admin(user_id)` checks to `list_users` and user provisioning callbacks.
   - Remove `/usr/lib/licence` and `/etc/VPSManager/senha` references in legacy `Modulos/bot`.
3. **Uninstaller Teardown (Task 29)**:
   - Add `sed -i '/menu;/d' /etc/profile 2>/dev/null || true` to `uninstall.sh`.
4. **Squid Whitelist Safety (Tasks 20 & 21)**:
   - Use `grep -F -x` for exact literal domain matching and enforce `chmod 644 "$payload"` in `addhost` and `delhost`.
5. **Menu & State Synchronization (Tasks 19, 24, 27)**:
   - Update `menu2` to check `/etc/axiom/torrent_blocked` for `$stsf`.
   - Calculate `$stsbot` and `$autm` dynamically in `menu2`.
   - Fix typographical string `A◇ㅤCTIVATING` in `autoexec`.
6. **Key Material Cleanup**:
   - Purge `stunnel.pem` from repository.

### E2E Testing Plan

1. **Expand Tier 2 Unit Test Suite**:
   - Add `tests/test_bot.py`, `tests/test_firewall.py`, `tests/test_monitor.py`, `tests/test_backup.py`, `tests/test_api.py`, `tests/test_cli.py`.
2. **Implement Tier 3 Functional Test Harness**:
   - Create `tests/test_bash_functional.py` or bash test suite using mocked system binaries in `$PATH`.
3. **Implement Tier 4 E2E Test Suite**:
   - Automated script `tests/test_e2e_lifecycle.sh` validating the complete installation, user creation, connection limit check, expired purge, backup archive creation, firewall rule verification, and uninstallation teardown.

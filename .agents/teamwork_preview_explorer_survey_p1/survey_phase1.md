# Phase 1 Survey Report: User & Account Management (Tasks 1–9)
**Axiom VPS Manager Investigation & Security Audit**
**Date:** 2026-09-01
**Author:** Teamwork Survey Explorer (Phase 1)

---

## 1. Executive Summary

Phase 1 encompasses all account lifecycle and access control mechanisms within Axiom VPS Manager (Tasks 1 through 9). This survey performed an exhaustive source-level inspection of shell scripts (`Modulos/*`), Python modules (`src/axiom/users/*`, `src/axiom/monitor/*`, `src/axiom/cli.py`), helper libraries (`lib/axiom-common.sh`), and the unit test suite (`tests/test_users.py`).

### Overall Assessment
- **Zero Malicious Artifacts**: No logic bombs, backdoor cron jobs, telemetry, or obfuscated payloads were detected in Tasks 1–9.
- **Zero Plaintext Password Files**: Password inputs are processed silently via `chpasswd` over stdin; no temporary plaintext password files are written to disk.
- **Key Vulnerabilities / Defects Identified**:
  1. *Missing Root Assertions & Common Library Integration*: Most shell scripts fail to source `lib/axiom-common.sh` or check `id -u -eq 0`.
  2. *System Account Exposure in Batch Purges*: Batch deletion in `remover` and `expcleaner` lacks explicit protection for system accounts (UID < 1000).
  3. *Fragile Trial Account Expiration*: `criarteste` relies exclusively on the `at` daemon (`atd.service`), which is often missing or disabled in minimal Linux VPS distributions.
  4. *Non-Atomic Cross-Device Renames*: `mktemp` in `/tmp` combined with `mv /tmp/... /root/usuarios.db` fails POSIX atomic rename guarantees if `/tmp` is mounted on `tmpfs`.
  5. *Python API Functional Gap*: `src/axiom/users/manager.py` lacks parity with shell modules for trial creation, password changes, expiry modification, and expired account purging.

---

## 2. Inventory & File Mapping for Tasks 1–9

| Task ID | Module Name | Primary Shell Path | Python Backend Path | CLI Command |
| :--- | :--- | :--- | :--- | :--- |
| **Task 01** | `criarusuario` | `Modulos/criarusuario` | `src/axiom/users/manager.py` (`UserManager.create_user`) | `axiom user create` |
| **Task 02** | `criarteste` | `Modulos/criarteste` | *Missing* (Needs `UserManager.create_trial_user`) | *Missing* |
| **Task 03** | `remover` | `Modulos/remover` | `src/axiom/users/manager.py` (`UserManager.delete_user`) | `axiom user delete` |
| **Task 04** | `sshmonitor` | `Modulos/sshmonitor` | `src/axiom/monitor/stats.py` (`SystemMonitor.get_system_metrics`) | `axiom menu` |
| **Task 05** | `mudardata` | `Modulos/mudardata` | *Missing* (Needs `UserManager.modify_expiry`) | *Missing* |
| **Task 06** | `alterarlimite` | `Modulos/alterarlimite` | `src/axiom/users/manager.py` (`UserManager._set_user_limit`) | *Missing* |
| **Task 07** | `alterarsenha` | `Modulos/alterarsenha` | *Missing* (Needs `UserManager.change_password`) | *Missing* |
| **Task 08** | `expcleaner` | `Modulos/expcleaner`<br>`Modulos/uexpired` | *Missing* (Needs `UserManager.purge_expired`) | *Missing* |
| **Task 09** | `infousers` | `Modulos/infousers` | `src/axiom/users/manager.py` (`UserManager.list_users`) | `axiom user list` |

---

## 3. Database Schema & Data Formats

### 3.1 Primary User Database (`/root/usuarios.db`)
- **Format**: Flat whitespace-delimited text.
- **Schema**: `<username> <limit>`
  ```text
  user1 2
  trial9482 1
  premium_client 5
  ```
- **Concurrency & Atomicity**:
  - Updates currently perform `tmp_db=$(mktemp)`, `grep -v`, `echo`, and `mv "$tmp_db" /root/usuarios.db`.
  - **Risk**: When `/tmp` is a `tmpfs` partition and `/root` is rootfs, `mv` falls back to `copy` + `unlink`, causing non-atomic replacement and potential race condition truncation during concurrent access.
  - **Remediation**: Use `mktemp /root/usuarios.db.XXXXXX` to guarantee same-filesystem `rename(2)` atomicity.

### 3.2 Trial Account Registry & Cleanup (`/etc/VPSManager/userteste/`)
- **Current Mechanism**: Individual Bash scripts `/etc/VPSManager/userteste/${nome}.sh` invoked via `at "now + $u_temp min"`.
- **Defect**: No centralized trial database; if the `at` spool is lost or `atd` is dead, trial accounts are indistinguishable from permanent accounts in `usuarios.db`.
- **Recommended Schema**: Dedicated registry `/etc/VPSManager/trial_users.db` storing `<username> <created_epoch> <duration_min> <expiry_epoch>`.

### 3.3 Expiration Counter Cache (`/etc/VPSManager/Exp`)
- **Format**: Single-line text containing integer of expired users (e.g. `0` or `5`).
- **Used by**: `Modulos/menu` header display, written by `Modulos/uexpired`, reset by `Modulos/expcleaner`.

### 3.4 OpenVPN PKI / Easy-RSA Database
- **Index**: `/etc/openvpn/easy-rsa/pki/index.txt`
- **Revocation List**: `/etc/openvpn/crl.pem`
- **Client Profiles**: `/root/${username}.ovpn` (Permissions: `chmod 600`).

---

## 4. Deep-Dive Analysis of Tasks 1–9

### Task 01: `criarusuario` (User Creation & Hardened Provisioning)
- **Code Observations**:
  - Lines 16–19: Username validation `^[a-zA-Z0-9_-]{3,32}$` is correctly implemented.
  - Lines 21–24: System collision check `id "$username"` prevents clobbering existing accounts.
  - Lines 26–30: Password input is silent (`read -s`), fallback generator provides 12 chars alphanumeric.
  - Lines 32–44: Validity days and connection limits validated as positive integers.
  - Lines 49–51: Sets expiry date via `useradd -e "$final_date" -M -s /bin/false` and invokes `chpasswd`.
  - Lines 60–77: Automatic Easy-RSA OpenVPN client creation and `.ovpn` bundling with `chmod 600`.
- **Issues & Gaps**:
  1. Lacks `source lib/axiom-common.sh` and `axiom_require_root`.
  2. Fallback password entropy: `echo "$((RANDOM % 899999 + 100000))"` is a weak 6-digit numeric fallback.
  3. UX double-prompt when invoked from `Modulos/menu`.

### Task 02: `criarteste` (Temporary Trial Account Creation)
- **Code Observations**:
  - Lines 12–15: Random trial username default `trial$((RANDOM % 8999 + 1000))`.
  - Lines 28–29: `u_temp="${u_temp:-60}"`
  - Lines 38–48: Generates `/etc/VPSManager/userteste/${nome}.sh` and queues via `at`.
- **Issues & Gaps**:
  1. **No Username Format Validation**: If custom username entered, lacks regex validation.
  2. **No Duration Validation**: Non-numeric or negative values for `u_temp` break `at`.
  3. **Critical Daemon Dependency**: Relies on `atd`. If `atd` is disabled or missing, trial accounts **never expire**.
  4. **No Test DB Isolation**: Trial accounts are mixed directly into `usuarios.db` without trial metadata or OS expiration date (`useradd` omits `-e`).

### Task 03: `remover` (Single & Batch User Removal)
- **Code Observations**:
  - Lines 4–19: `remove_ovp()` revokes EasyRSA client certificate, regenerates CRL, and copies CRL to `/etc/openvpn/crl.pem`.
  - Lines 58–64: Disconnects active sessions (`pkill -u`), deletes system account (`userdel -f`), and removes from `usuarios.db`.
  - Lines 72–87: Option 2 performs batch deletion of all accounts in `usuarios.db`.
- **Issues & Gaps**:
  1. **System Account Protection Missing**: Option 2 iterates over `usuarios.db` without verifying `UID >= 1000`. If `root` or a system user is entered into `usuarios.db`, it will be deleted.
  2. **Group Portability**: Hardcoded `nogroup` in `chown nobody:nogroup /etc/openvpn/crl.pem` fails on RHEL/CentOS/Fedora (`nobody:nobody`).
  3. **Python API Discrepancy**: `UserManager.delete_user()` in Python does not revoke OpenVPN certificates.

### Task 04: `sshmonitor` (Active Connection & Session Monitor)
- **Code Observations**:
  - Lines 22–27: Aggregates OpenSSH sessions (`pgrep -u "$user" sshd`), Dropbear (`pgrep -u "$user" dropbear`), and OpenVPN (`grep -E ",${user}," /etc/openvpn/openvpn-status.log`).
  - Lines 33–36: Tracks session elapsed time for OpenSSH sessions via `ps -p "$first_pid" -o etime=`.
  - Lines 44–46: Formats output table.
- **Issues & Gaps**:
  1. **Dropbear/OpenVPN Session Elapsed Time**: `first_pid` is only queried for `sshd`. Non-SSH VPN sessions show `00:00:00`.
  2. **OpenVPN Log Format Assumption**: Assumes comma-separated status log format version 1.
  3. No anti-tamper or malicious license checks found.

### Task 05: `mudardata` (Account Expiration Date Modifier)
- **Code Observations**:
  - Lines 22–28: Queries current expiration date via `chage -l "$u"`.
  - Lines 49–58: Supports both relative days (e.g. `30`) and absolute dates (`YYYY-MM-DD`).
  - Line 60: Updates system expiration via `chage -E "$target_date" "$target_user"`.
- **Issues & Gaps**:
  1. **No Past Date Validation**: Setting dates in the past is accepted without warning, immediately locking user access.
  2. **Missing Python Implementation**: `UserManager` has no method to update expiry dates of existing users.

### Task 06: `alterarlimite` (Connection Limit Modifier)
- **Code Observations**:
  - Lines 22–25: Retrieves and displays current limit from `/root/usuarios.db`.
  - Lines 41–45: Checks that `new_limit` is a positive integer.
  - Lines 47–50: Updates `usuarios.db` via `mktemp` and `mv`.
- **Issues & Gaps**:
  1. **Non-Atomic Rename across Mounts**: `mktemp` in `/tmp` -> `mv` to `/root/usuarios.db`.
  2. **Upper Bound Check**: Prompt mentions `[1-999]`, but arbitrary large integers are accepted.

### Task 07: `alterarsenha` (Silent Password Modifier)
- **Code Observations**:
  - Lines 38–42: Silent input `read -r -s -p`, auto-generates 12 chars if empty.
  - Lines 44–47: Enforces minimum 8 characters length.
  - Line 50: Disconnects active sessions with `pkill -u "$target_user"`.
  - Line 53: Applies new password via `echo "$target_user:$new_pass" | chpasswd`.
- **Issues & Gaps**:
  1. Zero plaintext leaks to disk verified.
  2. Missing Python method in `UserManager`.

### Task 08: `expcleaner` (Expired Account Purge Engine) & `uexpired`
- **Code Observations**:
  - Lines 31–59: Iterates over `usuarios.db`, queries `chage -l`, converts to epoch seconds, and deletes expired accounts.
  - Line 62: Resets `/etc/VPSManager/Exp` to `0`.
- **Issues & Gaps**:
  1. **System Account Protection Missing**: Does not verify `UID >= 1000`.
  2. **Day-End Expiry Window**: `date -d "$expdate"` converts to `00:00:00`. Accounts are purged on the day of expiration instead of 23:59:59.

### Task 09: `infousers` (User Audit Reporting)
- **Code Observations**:
  - Lines 11–40: Iterates over `usuarios.db`, displays Username, Status, Limit, and calculated remaining days.
  - Lines 43–45: Summarizes total accounts and online sessions.
- **Issues & Gaps**:
  1. **Integer Division Truncation**: `diff_days=$(( ( $(date -d "$datauser" +%s) - $(date +%s) ) / 86400 ))` displays `0 Days` for accounts with hours remaining today.
  2. **Online Count Discrepancy**: Line 44 only counts SSH `priv` processes; ignores Dropbear and OpenVPN.

---

## 5. Test Suite & Verification Status

### Python Unit Tests
- Executed: `uv run --with pytest pytest`
- Status: **8 passed in 0.06s** (including `tests/test_users.py`).
- Current tests in `test_users.py` verify basic password generation and basic DB string manipulation.
- **Gaps**: Missing tests for input validation, edge cases, date calculations, trial lifecycle, and UID protection.

### Static Syntax Check
- Executed `bash -n` across all Phase 1 scripts:
  - `Modulos/criarusuario`: **PASS**
  - `Modulos/criarteste`: **PASS**
  - `Modulos/remover`: **PASS**
  - `Modulos/sshmonitor`: **PASS**
  - `Modulos/mudardata`: **PASS**
  - `Modulos/alterarlimite`: **PASS**
  - `Modulos/alterarsenha`: **PASS**
  - `Modulos/expcleaner`: **PASS**
  - `Modulos/uexpired`: **PASS**
  - `Modulos/infousers`: **PASS**
  - `lib/axiom-common.sh`: **PASS**

---

## 6. Actionable Implementation & Remediation Plan

1. **Harden Shell Scripts (Phase 1)**:
   - Add `source lib/axiom-common.sh` and `axiom_require_root` to all 9 scripts.
   - Enforce UID >= 1000 checks in `remover` and `expcleaner`.
   - Update temp file generation to `mktemp /root/usuarios.db.XXXXXX` for atomic replacement.
   - Add trial isolation registry `/etc/VPSManager/trial_users.db` and fallback purge cron.
   - Fix remaining days calculation in `infousers` (`+ 86399` / ceil).
   - Normalize nobody/nogroup handling across Linux distributions.
2. **Synchronize Python `UserManager`**:
   - Implement `modify_limit`, `modify_expiry`, `change_password`, `create_trial_user`, `purge_expired_users`, and OpenVPN CRL revocation.
   - Expand `src/axiom/cli.py` subcommands.
3. **Expand Test Coverage**:
   - Add parameterized unit tests in `tests/test_users.py` covering invalid inputs, boundary limits, trial expiry logic, and system account safety.

# Handoff Report: Phase 1 (User & Account Management - Tasks 1 to 9)

**Author**: Survey Explorer (Phase 1)
**Scope**: Codebase audit of Tasks 1 through 9 for Axiom VPS Manager
**Status**: Survey & Investigation Completed

---

## 1. Observation

Direct code inspection of Phase 1 components yielded the following exact findings:

1. **Task 01 (`Modulos/criarusuario`, `src/axiom/users/manager.py:40-62`)**:
   - `Modulos/criarusuario` validates usernames (`^[a-zA-Z0-9_-]{3,32}$`), positive days/limits, sets expiration with `useradd -e "$final_date"`, pipes password to `chpasswd`, writes limit to `/root/usuarios.db`, and bundles OpenVPN `.ovpn` profiles (`chmod 600`).
   - Line 1 misses sourcing `lib/axiom-common.sh` and lacks `axiom_require_root`.
   - Line 29 weak fallback password generator: `echo "$((RANDOM % 899999 + 100000))"`.
   - Python `UserManager.create_user` does not generate OpenVPN client profiles.

2. **Task 02 (`Modulos/criarteste`, `Modulos/botsshteste:24-68`)**:
   - `Modulos/criarteste:37-48` generates cleanup script `/etc/VPSManager/userteste/${nome}.sh` and queues execution using `at "now + $u_temp min"`.
   - `criarteste` lacks input validation on manual username and duration `u_temp`.
   - Trial accounts are written directly to `/root/usuarios.db` with no dedicated trial database isolation and no OS-level expiry date.
   - If `atd` is disabled/not installed, trial accounts never expire.
   - Python `UserManager` has no trial user creation method.

3. **Task 03 (`Modulos/remover`, `src/axiom/users/manager.py:63-78`)**:
   - `Modulos/remover:4-19` handles OpenVPN certificate revocation (`./easyrsa --batch revoke`, `./easyrsa gen-crl`, `/etc/openvpn/crl.pem`).
   - `Modulos/remover:72-87` (batch user removal) iterates over `/root/usuarios.db` and issues `pkill -u` and `userdel -f` without checking if `UID < 1000`.
   - `Modulos/remover:14` hardcodes `chown nobody:nogroup` which fails on non-Debian distributions (`nobody:nobody`).
   - Python `UserManager.delete_user` lacks OpenVPN certificate revocation.

4. **Task 04 (`Modulos/sshmonitor`, `src/axiom/monitor/stats.py:32-38`)**:
   - `Modulos/sshmonitor:22-27` counts OpenSSH (`pgrep -u "$user" sshd`), Dropbear (`pgrep -u "$user" dropbear`), and OpenVPN (`grep -E ",${user}," /etc/openvpn/openvpn-status.log`).
   - `Modulos/sshmonitor:33-36` calculates session elapsed time only for OpenSSH (`ps -p "$first_pid" -o etime=`), defaulting to `00:00:00` for Dropbear and OpenVPN.
   - Zero license checks or telemetry found.

5. **Task 05 (`Modulos/mudardata`)**:
   - `Modulos/mudardata:49-60` validates relative days or absolute `YYYY-MM-DD` and invokes `chage -E "$target_date" "$target_user"`.
   - Accepts past dates without confirmation.
   - Python `UserManager` has no expiry modification method.

6. **Task 06 (`Modulos/alterarlimite`, `src/axiom/users/manager.py:80-88`)**:
   - `Modulos/alterarlimite:41-50` updates limits in `/root/usuarios.db` via `mktemp` and `mv`.
   - `mktemp` uses `/tmp` by default; across separate filesystems (e.g. `tmpfs` to rootfs), `mv` is not an atomic `rename(2)`.
   - Lacks upper bound limit enforcement.

7. **Task 07 (`Modulos/alterarsenha`)**:
   - `Modulos/alterarsenha:38-54` uses silent input (`read -r -s -p`), validates length >= 8, kills active sessions (`pkill -u`), and pipes password to `chpasswd`.
   - Zero plaintext password leaks to disk or `/tmp`.
   - Python `UserManager` has no `change_password` method.

8. **Task 08 (`Modulos/expcleaner`, `Modulos/uexpired`)**:
   - `Modulos/expcleaner:31-59` purges expired users by comparing `chage -l` epoch against current time, revoking OpenVPN certs, and zeroing `/etc/VPSManager/Exp`.
   - Missing UID < 1000 check.
   - Expiration comparison considers midnight `00:00:00` rather than day-end `23:59:59`.

9. **Task 09 (`Modulos/infousers`, `src/axiom/users/manager.py:26-38`)**:
   - `Modulos/infousers:21-39` displays tabular audit.
   - Line 30 integer division truncates hours into `0 Days`.
   - Line 44 online counter only checks SSH `priv` processes.

10. **Syntax and Test Executions**:
    - `uv run --with pytest pytest`: 8 passed in 0.06s.
    - `bash -n` on all Phase 1 shell scripts: all passed without syntax errors.

---

## 2. Logic Chain

1. **Root Privilege Safety**: Because `Modulos/*` scripts invoke system administration utilities (`useradd`, `userdel`, `chpasswd`, `chage`, `pkill`, `easyrsa`), executing them as non-root causes mid-execution failures and corrupted partial states. Sourcing `lib/axiom-common.sh` and invoking `axiom_require_root` at script entry is necessary.
2. **System Account Protection**: Because `/root/usuarios.db` is a text file that could contain accidental or malicious system usernames, batch deletion loops in `remover` and `expcleaner` that invoke `userdel -f "$user"` without checking `id -u "$user" >= 1000` create a risk of deleting root or daemon accounts. Enforcing `UID >= 1000` and `user != root` prevents destructive operations.
3. **Trial Account Daemon Dependency & Race Conditions**: Because `atd` is not standard on minimal cloud images, relying solely on `at` means unpurged trial accounts can persist indefinitely. Storing trial metadata in `/etc/VPSManager/trial_users.db` and implementing a scheduled fallback sweep in `expcleaner`/`limiter` ensures trial account lifecycles are strictly enforced regardless of daemon availability.
4. **Filesystem Atomicity**: Because POSIX atomic renaming requires source and destination to reside on the same filesystem, creating temporary files in `/tmp` when updating `/root/usuarios.db` creates a non-atomic copy window if `/tmp` is `tmpfs`. Using `mktemp /root/usuarios.db.XXXXXX` ensures same-device atomic replacement.
5. **Python API Parity**: Because Axiom supports both shell and Python CLI/API entry points, `src/axiom/users/manager.py` must support all user lifecycle operations (trial creation, password change, limit adjustment, expiration extension, expired account purging).

---

## 3. Caveats

- **Runtime PAM & Shadow Settings**: Specific password hashing algorithms (Argon2id vs SHA-512 vs yescrypt) depend on the host OS `/etc/pam.d/common-password` or `/etc/login.defs` (`ENCRYPT_METHOD`). Standard `chpasswd` honors system configuration.
- **EasyRSA Directory Structure**: EasyRSA 3 standard PKI paths (`/etc/openvpn/easy-rsa/pki/`) were assumed based on `criarusuario` and `remover`.
- **Operating Environment**: Static analysis and unit test runs were executed locally on Windows via `pwsh`, `uv`, and `bash.exe`. Live system service interactions (`useradd`, `pkill`) require Linux root execution.

---

## 4. Conclusion

The Phase 1 codebase (Tasks 1–9) provides clean, functional baseline implementations free from malicious anti-tamper logic bombs or plaintext disk exposures. However, critical hardening is required across three categories:
1. **Safety & Robustness**: Add `axiom_require_root`, system account UID >= 1000 guards, atomic same-mount database updates, and multi-distro group handling (`nogroup`/`nobody`).
2. **Trial Lifecycle Reliability**: Decouple `criarteste` from strict `atd` dependency by introducing `/etc/VPSManager/trial_users.db` and fallback expiration sweeps.
3. **API & Test Parity**: Extend `src/axiom/users/manager.py` and `src/axiom/cli.py` with missing methods (trial, password, limit, expiry, purge), and expand `tests/test_users.py` with comprehensive validation tests.

---

## 5. Verification Method

To independently verify the survey findings:

1. **Python Unit Tests**:
   ```pwsh
   uv run --with pytest pytest E:\workspace\playground\DRAGON-VPS-MANAGER\tests
   ```
2. **Python Code Formatting & Linting**:
   ```pwsh
   uv run --with ruff ruff check E:\workspace\playground\DRAGON-VPS-MANAGER\src E:\workspace\playground\DRAGON-VPS-MANAGER\tests
   ```
3. **Shell Script Static Syntax Verification**:
   ```pwsh
   Get-ChildItem -Path Modulos, lib -File | ForEach-Object {
       $rel = ($_.FullName.Replace('E:\workspace\playground\DRAGON-VPS-MANAGER\', '').Replace('\', '/'))
       & bash -n $rel
       if ($LASTEXITCODE -eq 0) { "[OK] $rel" } else { "[FAIL] $rel" }
   }
   ```
4. **Inspect Survey Report**:
   Review `E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_explorer_survey_p1\survey_phase1.md` for full module-by-module breakdown.

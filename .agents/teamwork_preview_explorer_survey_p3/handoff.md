# Handoff Report: Phase 3 (Tasks 19–30) & Test Infrastructure Survey

## 1. Observation

### Codebase Inspection & Line References

1. **Task 19 (menu2)**:
   - File: `Modulos/menu` lines 139–249.
   - Line 140: `[[ -e /etc/Plus-torrent ]] && stsf=$(echo -e "\033[1;32m♦ ") || stsf=$(echo -e "\033[1;31m○ ")`
   - Line 184: `[\033[1;36m27\033[1;31m] \033[1;37m◇ \033[1;33mSELF EXECUTION $autm`
   - Line 188: `[\033[1;36m25\033[1;31m] \033[1;37m◇ \033[1;33mTELEGRAM BOT $stsbot`
   - `$stsbot` and `$autm` are displayed in the menu text but are not computed anywhere in the function.

2. **Task 20 (addhost) & Task 21 (delhost)**:
   - File: `Modulos/addhost` lines 28, 39–41:
     ```bash
     if grep -q "^$host" "$payload"; then
     ...
     tmp_file=$(mktemp)
     grep -v "^$" "$payload" > "$tmp_file"
     mv "$tmp_file" "$payload"
     ```
   - File: `Modulos/delhost` lines 28, 33–35:
     ```bash
     if ! grep -q "^$host" "$payload"; then
     ...
     tmp_file=$(mktemp)
     grep -v "^$host" "$payload" > "$tmp_file"
     mv "$tmp_file" "$payload"
     ```
   - Both use unescaped regex `^$host` on dot-prefixed strings and overwrite the payload with a `0600` permission file created by `mktemp`.

3. **Task 22 (reiniciarsistema)**:
   - File: `Modulos/reiniciarsistema` lines 1–4:
     ```bash
     #!/bin/bash
     echo -e "\033[1;31m◇ RESTARTING...\033[0m"
     shutdown -r now
     ```
   - Lacks any interactive confirmation prompt.

4. **Task 23 (reiniciarservicos)**:
   - File: `Modulos/reiniciarservicos` lines 1–36: Gracefully iterates and restarts `sshd`, `ssh`, `axiom-wsproxy`, `axiom-bot`, `caddy`, `wg-quick@wg0`, `xray`, `hysteria-server`, `squid`, `squid3`, `dropbear`, `openvpn`, `stunnel4`.

5. **Task 24 (blockt)**:
   - File: `Modulos/blockt` lines 5, 12–36: Uses flag `/etc/axiom/torrent_blocked` and custom chain `AXIOM_TORRENT`. Drops TCP/UDP 6881–6889 and 51413. Teardown safely removes `FORWARD`/`OUTPUT` jumps, flushes and deletes `AXIOM_TORRENT`.

6. **Task 25 (botssh / axiom-bot & Security Killswitches)**:
   - File: `src/axiom/telegram/bot.py` lines 73–78: `list_users` callback handler lists all accounts without verifying `effective_user.id == self.admin_id`.
   - File: `src/axiom/telegram/bot.py`: Lacks `if __name__ == "__main__":` entrypoint required by `systemd/axiom-bot.service` (`ExecStart=/usr/bin/python3 -m axiom.telegram.bot`).
   - File: `Modulos/bot` line 10: `[[ ! -e /usr/lib/licence ]] && exit 0` (license bomb).
   - File: `Modulos/conexao` line 12: `[[ $(awk -F" " '{print $2}' /usr/lib/licence) == "@DRAGON_VPS_MANAGER" ]] && {` (license bomb).
   - File: `Modulos/bot` lines 230, 318 and `Modulos/botgerador` line 51: Plaintext passwords saved into `/etc/VPSManager/senha/$usuario`.
   - File: `Modulos/botgerador` line 41: `pass=$(perl -e 'print crypt($ARGV[0], "password")' $senha)` (DES crypt with fixed salt).

7. **Task 26 (senharoot)**:
   - File: `Modulos/senharoot` lines 10–27: Uses `read -r -s -p`, verifies confirmation matching, checks length >= 8, updates password via `echo "root:$pass1" | chpasswd`.

8. **Task 27 (autoexec)**:
   - File: `Modulos/menu` lines 109–137: Idempotent toggle of `menu;` in `/etc/profile`. Line 124 contains typo `A◇ㅤCTIVATING`.

9. **Task 28 (attscript / verifatt)**:
   - Files: `Modulos/attscript` lines 59–144, `Modulos/verifatt` lines 1–9, `Install/versao`, `Sistema/versao`.

10. **Task 29 (delscript / uninstall.sh)**:
    - Files: `Modulos/delscript` lines 1–14, `uninstall.sh` lines 1–125.
    - Lines 48–62 disable/remove systemd services. Lines 75–80 clean crontab. Lines 83–93 teardown firewall.
    - Missing cleanup: does not remove `menu;` from `/etc/profile`.

11. **Task 30 (menu)**:
    - File: `Modulos/menu` lines 30–108, 250–421: Primary menu dispatcher and submenu controller.

12. **Static Key Exposure**:
    - File: `stunnel.pem` (repo root): Contains static RSA Private Key and Cloudflare Origin Certificate for `*.kiritossh.xyz`.

### Static and Unit Test Results

- **Shell Static Check (`bash -n`)**:
  - Command: `bash -n` executed across 52 shell scripts.
  - Result: 52/52 passed syntax check.
- **Python Lint & Unit Tests**:
  - Command: `uv run --with pytest --with pytest-asyncio pytest` -> 8 passed in 0.04s.
  - Command: `uv run --with ruff ruff check` -> All checks passed.
- **Web Asset Checks**:
  - Command: `npx @biomejs/biome check web` -> 3 files checked, 0 errors.
  - Command: `npx htmlhint web` -> 1 file scanned, 0 errors.

---

## 2. Logic Chain

1. **Security & Anti-tamper Analysis**:
   - Observation 6 identifies line 10 in `Modulos/bot` (`[[ ! -e /usr/lib/licence ]] && exit 0`) and line 12 in `Modulos/conexao`. Because `/usr/lib/licence` is an artificial license file not provisioned in standard systems, this logic bomb causes silent script failure.
   - Observation 12 identifies `stunnel.pem` containing a live private key in the repository. This violates basic cryptographic hygiene and the project acceptance criteria.
   - Observation 6 shows `/etc/VPSManager/senha/$usuario` storing plaintext passwords. `src/axiom/security/scanner.py` specifically flags this directory as a HIGH severity finding.

2. **Functional Integrity Analysis**:
   - Observation 3 shows `reiniciarsistema` executing `shutdown -r now` immediately without confirmation. Any misclick in the menu triggers an immediate unconfirmed reboot.
   - Observation 1 shows `$stsf` checking `/etc/Plus-torrent`, while Observation 5 shows `blockt` creating `/etc/axiom/torrent_blocked`. This path mismatch prevents `menu2` from ever reflecting the blocked state.
   - Observation 6 shows `src/axiom/telegram/bot.py` missing an `if __name__ == "__main__":` entrypoint and admin check on `list_users`. Without this, the systemd unit `axiom-bot.service` cannot start the daemon, and any user could dump active accounts.
   - Observation 10 shows `uninstall.sh` omitting `/etc/profile` cleanup. Post-uninstallation SSH logins will produce `command not found: menu` errors.

3. **Test Infrastructure Analysis**:
   - Current pytest coverage covers 4 files and 8 test cases.
   - 10 Python modules in `src/axiom/` (bot, firewall, monitor, wireguard, qrcode, backup, api, cli, dashboard) have zero test coverage.
   - No mock test harnesses exist for shell script functional validation (Tier 3) or end-to-end lifecycle validation (Tier 4).

---

## 3. Caveats

- Investigation was performed in read-only mode; no repository files were altered.
- Static checks and unit tests were run using local tools (`uv`, `bash.exe`, `npx`). Kernel-level operations (`iptables`, `systemctl`, `chpasswd`, `shutdown`) were analyzed statically through code inspection rather than executed against a live Linux kernel.
- No other caveats.

---

## 4. Conclusion

Phase 3 is architecturally structured but contains actionable defects:
1. **Critical Security Fixes Needed**: Purge `stunnel.pem` from repository; remove `/usr/lib/licence` killswitch lines from `Modulos/bot` and `Modulos/conexao`; remove plaintext `/etc/VPSManager/senha/` writes; add admin authorization checks to `src/axiom/telegram/bot.py`.
2. **Functional & Usability Fixes Needed**: Add `[y/N]` confirmation prompt to `Modulos/reiniciarsistema`; add `if __name__ == "__main__":` to `src/axiom/telegram/bot.py`; synchronize torrent flag between `blockt` and `menu2`; add `sed -i '/menu;/d' /etc/profile` to `uninstall.sh`; fix typos in `menu` (`autoexec`, `$stsbot`, `$autm`).
3. **Quality & Test Expansion Needed**: Expand pytest coverage across all 10 un-tested Python modules; implement Tier 3 mock functional tests and Tier 4 E2E lifecycle test script.

---

## 5. Verification Method

To independently verify these findings, execute the following commands in `E:\workspace\playground\DRAGON-VPS-MANAGER`:

1. **Static Syntax Verification**:
   ```bash
   for f in install.sh uninstall.sh senharoot.sh Modulos/* Install/*.sh lib/*.sh; do
       if [ -f "$f" ]; then head -n 1 "$f" | grep -qE "bash|sh" && bash -n "$f" && echo "PASS: $f"; fi
   done
   ```
2. **Python Lint & Unit Tests**:
   ```pwsh
   uv run --with pytest --with pytest-asyncio pytest
   uv run --with ruff ruff check
   ```
3. **Web Asset Linting**:
   ```pwsh
   npx --yes @biomejs/biome check web
   npx --yes htmlhint web
   ```
4. **Security Finding Verification**:
   - Inspect `stunnel.pem`: Verify private key exists in repo root.
   - Inspect `Modulos/bot` line 10: Verify `[[ ! -e /usr/lib/licence ]] && exit 0`.
   - Inspect `Modulos/conexao` line 12: Verify `/usr/lib/licence` check.
   - Inspect `Modulos/reiniciarsistema`: Verify missing confirmation prompt.
   - Inspect `src/axiom/telegram/bot.py`: Verify missing `__main__` entrypoint and missing auth on `list_users`.

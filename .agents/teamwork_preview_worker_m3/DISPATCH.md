## 2026-09-01T08:02:28Z
You are the Implementation Worker for Milestone 3 (Phase 3: Advanced Operations, Security & Lifecycle, Tasks 19–30) of Axiom VPS Manager.
Your working directory: E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_worker_m3
Original request file: E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\ORIGINAL_REQUEST.md
Project plan: E:\workspace\playground\DRAGON-VPS-MANAGER\PROJECT.md
Survey handoff: E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_explorer_survey_p3\handoff.md

Tasks:
1. Implement and harden all Phase 3 tasks and repository hygiene:
   - Root cleanup: Delete leaked `stunnel.pem` from repository root.
   - Purge license checks & killswitches: Remove `[[ ! -e /usr/lib/licence ]] && exit 0` from `Modulos/bot`, `Modulos/conexao`, and any other scripts.
   - Purge plaintext password file writes: Remove `/etc/VPSManager/senha/` directory creation and password dumping in `Modulos/bot` and `Modulos/botgerador`.
   - Task 19 (`menu2`): Synchronize torrent indicator with `/etc/axiom/torrent_blocked`, fix `$stsbot` and `$autm` indicators.
   - Task 20 (`addhost`) & Task 21 (`delhost`): Use escaped regex matching for dot-separated domains, preserve permissions when replacing payload file, reload proxy.
   - Task 22 (`reiniciarsistema`): Add interactive confirmation prompt `[y/N]` before rebooting.
   - Task 23 (`reiniciarservicos`): Ensure clean service restart iteration across all protocols and proxies.
   - Task 24 (`blockt`): Ensure AXIOM_TORRENT chain filtering and safe teardown without flushing primary tables.
   - Task 25 (`botssh` / `axiom-bot`): Enforce admin authorization on all bot callbacks (including `list_users`), add `if __name__ == "__main__":` entrypoint to `src/axiom/telegram/bot.py` for systemd execution.
   - Task 26 (`senharoot`): Verify silent input, confirmation matching, chpasswd update.
   - Task 27 (`autoexec`): Idempotent `/etc/profile` toggle, fix typos.
   - Task 28 (`attscript` / `verifatt`): Non-destructive update check against GitHub releases.
   - Task 29 (`delscript` / `uninstall.sh`): Ensure comprehensive teardown including removing `menu;` from `/etc/profile`, backup prompt, systemd unit disabling, cron and firewall cleanup.
   - Task 30 (`menu`): Verify primary menu return and dispatch handling.
   - Python tests: add/expand unit tests in `tests/test_bot.py`, `tests/test_scanner.py`, `tests/test_config.py`.
2. Verify all affected shell scripts pass `bash -n`.
3. Verify Python tests pass (`uv run --with pytest pytest`) and pass `ruff check`.
4. Deliver detailed handoff report in `E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_worker_m3\handoff.md` and send a message when complete.

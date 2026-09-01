## 2026-09-01T08:02:28Z

You are the Implementation Worker for Milestone 2 (Phase 2: Protocols, Tunnels & Network Infrastructure, Tasks 10–18) of Axiom VPS Manager.
Your working directory: E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_worker_m2
Original request file: E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\ORIGINAL_REQUEST.md
Project plan: E:\workspace\playground\DRAGON-VPS-MANAGER\PROJECT.md
Survey handoff: E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_explorer_survey_p2\handoff.md

You MUST read ORIGINAL_REQUEST.md, PROJECT.md, and the Phase 2 survey handoff before modifying any files.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your EXCLUSIVE file write boundaries (do not modify files outside this list):
- Shell modules: `Modulos/conexao`, `Modulos/speedtest`, `Modulos/banner`, `Modulos/otimizar`, `Modulos/userbackup`, `Modulos/limiter`, `Modulos/droplimiter`, `Modulos/badvpn`, `Modulos/detalhes`, `Modulos/slowdns`, `Modulos/slow_dns`, `Modulos/instsqd`
- Python source: `src/axiom/users/backup.py`, `src/axiom/monitor/stats.py`, `src/axiom/monitor/bandwidth.py`, `src/axiom/services/*`
- Systemd units: `systemd/axiom-backup.service`, `systemd/axiom-limiter.service`, `systemd/axiom-badvpn.service`
- Python tests: `tests/test_services.py`, `tests/test_backup.py`, `tests/test_monitor.py`

Your tasks:
1. Implement and harden all Phase 2 tasks:
   - Task 10 (`conexao`): Remove license checks (`/usr/lib/licence`, `/home/vpsmanager`), remove `fun_apchon` / Apache2 webroot exposure (`/var/www/html/openvpn`), replace `iptables -F` with idempotent table rules, use `mktemp` for temp files, update OpenVPN modern ciphers (`data-ciphers AES-256-GCM:...`), remove hardcoded IP from SlowDNS, ensure on-demand dynamic RSA cert generation.
   - Task 11 (`speedtest`): Ensure clean fallback handling.
   - Task 12 (`banner`): Fix trailing HTML tags in option 10; ensure clean ASCII/ANSI text rendering and safe `/etc/bannerssh`.
   - Task 13 (`nload`): Ensure auto-installer and `src/axiom/monitor/bandwidth.py` telemetry.
   - Task 14 (`otimizar`): Verify safe RAM cache drop and swap recycling threshold.
   - Task 15 (`userbackup`): Ensure `Modulos/userbackup` accepts CLI non-interactive argument (`$1`) for `systemd/axiom-backup.service`, chmod 600, encrypted archives in `/root/backups/`.
   - Task 16 (`limiter` / `limit_ssh`): Keep selective excess session termination (`$excess = active_count - limit`), integrate `axiom-limiter.service`.
   - Task 17 (`badvpn`): Deploy BadVPN UDP Gateway on port 7300 using local binary/SHA256 verification, integrate `axiom-badvpn.service`.
   - Task 18 (`detalhes`): Fix typo `OPERATING SYSTEML`, use `uname -m`, enumerate both TCP and UDP listening ports (`ss -tulpn`).
   - Python tests: add/expand unit tests in `tests/test_services.py`, `tests/test_backup.py`, `tests/test_monitor.py`.
2. Verify all affected shell scripts pass `bash -n`.
3. Verify Python tests pass (`uv run --with pytest pytest`) and pass `ruff check`.
4. Deliver detailed handoff report in `E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_worker_m2\handoff.md` and send a message when complete.

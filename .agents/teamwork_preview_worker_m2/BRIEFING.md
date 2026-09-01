# BRIEFING — 2026-09-01T08:03:00Z

## Mission
Implement and harden Milestone 2 (Phase 2: Protocols, Tunnels & Network Infrastructure, Tasks 10–18) of Axiom VPS Manager.

## 🔒 My Identity
- Archetype: teamwork_preview_worker_m2
- Roles: implementer, qa, specialist
- Working directory: E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_worker_m2
- Original parent: 2edbc19b-4c64-46ef-8725-1d5a95f1c1a9
- Milestone: Milestone 2 (Phase 2: Tasks 10-18)

## 🔒 Key Constraints
- Exclusive file write boundaries:
  - Shell modules: `Modulos/conexao`, `Modulos/speedtest`, `Modulos/banner`, `Modulos/otimizar`, `Modulos/userbackup`, `Modulos/limiter`, `Modulos/droplimiter`, `Modulos/badvpn`, `Modulos/detalhes`, `Modulos/slowdns`, `Modulos/slow_dns`, `Modulos/instsqd`
  - Python source: `src/axiom/users/backup.py`, `src/axiom/monitor/stats.py`, `src/axiom/monitor/bandwidth.py`, `src/axiom/services/*`
  - Systemd units: `systemd/axiom-backup.service`, `systemd/axiom-limiter.service`, `systemd/axiom-badvpn.service`
  - Python tests: `tests/test_services.py`, `tests/test_backup.py`, `tests/test_monitor.py`
- Mandatory Integrity: No hardcoding test results, no dummy implementations.
- Verification: bash -n on modified shell scripts, uv run --with pytest pytest, ruff check.

## Current Parent
- Conversation ID: 2edbc19b-4c64-46ef-8725-1d5a95f1c1a9
- Updated: 2026-09-01T08:03:00Z

## Task Summary
- **What to build**: Phase 2 implementation of Protocols, Tunnels & Network Infrastructure (Tasks 10-18):
  - Task 10: `conexao` / OpenVPN / SlowDNS / Squid hardening
  - Task 11: `speedtest` fallback handling
  - Task 12: `banner` ASCII/ANSI clean rendering, safe `/etc/bannerssh`
  - Task 13: `nload` auto-installer & `src/axiom/monitor/bandwidth.py`
  - Task 14: `otimizar` safe RAM cache drop & swap recycling threshold
  - Task 15: `userbackup` CLI non-interactive arg, chmod 600, encrypted archives in `/root/backups/`, `systemd/axiom-backup.service`
  - Task 16: `limiter` / `limit_ssh` selective excess session termination, `systemd/axiom-limiter.service`
  - Task 17: `badvpn` UDP Gateway port 7300, `systemd/axiom-badvpn.service`
  - Task 18: `detalhes` OS typo fix, `uname -m`, TCP+UDP enumeration (`ss -tulpn`)
  - Python services & tests
- **Success criteria**: All bash scripts valid (`bash -n`), pytest tests pass, ruff check passes, handoff report complete.

## Change Tracker
- **Files modified**: None yet
- **Build status**: Not tested yet
- **Pending issues**: None

## Quality Status
- **Build/test result**: TBD
- **Lint status**: TBD
- **Tests added/modified**: TBD

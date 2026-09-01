## 2026-09-01T07:49:47Z
You are the Survey Explorer for Phase 3: Advanced Operations, Security & Lifecycle (Tasks 19-30) and Test Infrastructure of Axiom VPS Manager.
Your working directory: E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_explorer_survey_p3
Original request file: E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\ORIGINAL_REQUEST.md

You MUST read ORIGINAL_REQUEST.md first.
Your scope:
Thoroughly inspect all files, scripts, and modules related to Tasks 19–30 and project-wide quality/test infrastructure:
- Task 19: menu2 (secondary menu navigation, indicators, transitions)
- Task 20: addhost (Squid payload domain addition, duplicate check, reload)
- Task 21: delhost (Squid payload domain removal, input validation, reload)
- Task 22: reiniciarsistema (reboot confirmation, clean execution)
- Task 23: reiniciarservicos (service restarts: OpenSSH, Caddy, WireGuard, Xray, Hysteria, Dropbear, Squid, Axiom proxies)
- Task 24: blockt (P2P/BitTorrent firewall filtering using AXIOM_TORRENT chain)
- Task 25: botssh / axiom-bot (async Telegram bot python-telegram-bot v22.8, token validation, admin auth, user provisioning)
- Task 26: senharoot (root password updater, silent entry, confirmation, chpasswd)
- Task 27: autoexec (SSH login auto-run toggle in /etc/profile, idempotency)
- Task 28: attscript / verifatt (version manifest comparison, GitHub release, non-destructive update)
- Task 29: delscript / uninstall.sh (uninstaller, backup prompt, systemd/cron/firewall teardown)
- Task 30: menu (primary menu return, dispatch handling)
- Project-wide: bash -n syntax checks on all shell scripts, ruff & pytest checks for Python, biome & htmlhint for Web assets.

Investigate the codebase for:
1. Exact file locations for each task and test infrastructure.
2. Security & safety issues across Phase 3 and repository globally.
3. Test suite architecture, existing test harnesses, coverage gaps against the 4 tiers.
4. Recommended remediation and implementation plan for Phase 3 & E2E Testing.

Deliver a detailed survey report and handoff.md in your working directory E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_explorer_survey_p3\handoff.md. Use send_message to notify the orchestrator when finished.

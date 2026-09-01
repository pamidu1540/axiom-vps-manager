# Original User Request

## 2026-09-01T07:47:49Z

Perform an exhaustive, multi-dimensional logical, functional, and security audit of all 30 commands and menu actions in Axiom VPS Manager. Verify that every single module executes correctly, handles errors gracefully, contains zero security vulnerabilities, has no anti-tamper logic bombs or plaintext exposures, and functions as intended.

Working directory: E:\workspace\playground\DRAGON-VPS-MANAGER
Integrity mode: development

---

## Task Breakdown (30 Subtasks for Parallel Verification)

### Phase 1: User & Account Management (Tasks 1–9)
- [ ] Task 01 (criarusuario): Validate user creation, Argon2id/SHA-512 password hashing, chage expiration date setting, connection limit registration in /root/usuarios.db, and invalid input rejection.
- [ ] Task 02 (criarteste): Validate temporary trial account creation, automatic cron expiration timer, session cleanup, and test database isolation.
- [ ] Task 03 (remover): Validate single-user and batch removal, process termination (pkill -u), userdel, /root/usuarios.db cleanup, and OpenVPN certificate revocation.
- [ ] Task 04 (sshmonitor): Validate active SSH, Dropbear, and OpenVPN connection counting, PID tracking, session elapsed timer, and removal of license checks.
- [ ] Task 05 (mudardata): Validate account expiration date extension via relative days and absolute YYYY-MM-DD inputs, chage -E execution, and input sanitization.
- [ ] Task 06 (alterarlimite): Validate connection limit modification in /root/usuarios.db, positive integer validation, and race-condition-free file updates.
- [ ] Task 07 (alterarsenha): Validate user password changes via chpasswd, silent password inputs, and zero plaintext password leaks.
- [ ] Task 08 (expcleaner): Validate expired account batch purging, system account protection (ignoring UID < 1000 and accounts outside usuarios.db), and CRL regeneration.
- [ ] Task 09 (infousers): Validate managed user audit reporting, expiration inspection, and active connection tracking.

### Phase 2: Protocols, Tunnels & Network Infrastructure (Tasks 10–18)
- [ ] Task 10 (conexao): Validate multi-protocol connection modes:
  - Squid Proxy (port management, host whitelisting, config reloading)
  - Dropbear SSH (port multiplexing, init scripts)
  - OpenVPN (Easy-RSA PKI generation, PAM authentication, client profile generation)
  - Stunnel4 (on-demand dynamic RSA cert generation, zero hardcoded keys)
  - SSLH (port multiplexing)
  - SlowDNS (UDP 5300 DNS tunnel daemon setup)
- [ ] Task 11 (speedtest / velocity): Validate internet speed and latency benchmarking with automatic dependency fallback.
- [ ] Task 12 (banner): Validate SSH login banner creation, color formatting, /etc/bannerssh file handling, and Dropbear banner integration.
- [ ] Task 13 (nload): Validate real-time network interface bandwidth visualization and dependency auto-installer.
- [ ] Task 14 (otimizar): Validate RAM buffer/cache drop, swap memory recycling with safety thresholds, and package cache cleaning.
- [ ] Task 15 (userbackup): Validate encrypted local archive generation (/root/backups/), root-only permissions (chmod 600), and elimination of public webroot exposure.
- [ ] Task 16 (limiter / limit_ssh): Validate background connection limiter daemon, ensuring only excess sessions are killed while active connections are kept intact.
- [ ] Task 17 (badvpn): Validate BadVPN UDP Gateway daemon setup on port 7300, binary download integrity, autostart integration, and clean process control.
- [ ] Task 18 (detalhes): Validate system hardware inspection, CPU architecture, RAM consumption, and live TCP/UDP listening port enumeration.

### Phase 3: Advanced Operations, Security & Lifecycle (Tasks 19–30)
- [ ] Task 19 (menu2): Validate secondary menu navigation, status indicators, and screen transitions.
- [ ] Task 20 (addhost): Validate Squid Proxy payload domain addition, duplicate check, and proxy reloading.
- [ ] Task 21 (delhost): Validate Squid Proxy payload domain removal, input validation, and proxy configuration updates.
- [ ] Task 22 (reiniciarsistema): Validate system reboot confirmation and clean execution.
- [ ] Task 23 (reiniciarservicos): Validate graceful service restarts across OpenSSH, Caddy, WireGuard, Xray, Hysteria, Dropbear, Squid, and Axiom proxies.
- [ ] Task 24 (blockt): Validate P2P/BitTorrent traffic filtering using dedicated AXIOM_TORRENT firewall chains without flushing primary tables.
- [ ] Task 25 (botssh / axiom-bot): Validate async Telegram bot setup (python-telegram-bot v22.8), token validation, admin authorization, and user provisioning flow.
- [ ] Task 26 (senharoot): Validate root password updater with silent input entry, confirmation matching, and chpasswd invocation.
- [ ] Task 27 (autoexec): Validate SSH login auto-run toggle in /etc/profile with safe idempotency.
- [ ] Task 28 (attscript / verifatt): Validate version manifest comparison against GitHub release endpoints and non-destructive updater invocation.
- [ ] Task 29 (delscript / uninstall.sh): Validate safe uninstaller with pre-removal backup prompt, systemd unit disabling, cron cleanup, and firewall teardown.
- [ ] Task 30 (menu): Validate primary menu return and dispatch handling.

---

## Acceptance Criteria

### Security & Vulnerability Auditing
- Zero logic bombs (rm -rf /bin), anti-tamper destructive hooks, or telemetry URLs across all 30 scripts.
- Zero plaintext passwords written to filesystem or /tmp/.
- Zero insecure static temp file race conditions (mktemp used throughout).
- No unauthenticated private keys, certificates, or backups stored in /var/www/html/.

### Logical & Functional Correctness
- All 30 commands run with clean exit codes on valid input and produce meaningful error messages on invalid input.
- User connection limits are enforced per-session without terminating all user connections.
- All 52 shell scripts pass bash -n static syntax verification without warnings or errors.
- All Python components pass ruff check and all pytest unit tests pass.
- All Web assets pass biome check and htmlhint.

### Local Execution Rule
- All changes and validation tests remain strictly local in E:\workspace\playground\DRAGON-VPS-MANAGER. No git push operations are executed without explicit approval.

# Phase 2 Survey & Architecture Audit Report
## Axiom VPS Manager — Tasks 10 to 18 (Protocols, Tunnels & Network Infrastructure)

**Surveyor**: Teamwork Explorer (Phase 2)  
**Date**: 2026-09-01  
**Scope**: Tasks 10–18 (conexao, speedtest, banner, nload, otimizar, userbackup, limiter, badvpn, detalhes)  
**Workspace**: `E:\workspace\playground\DRAGON-VPS-MANAGER`

---

## 1. Observation

Direct code inspection of all files associated with Phase 2 (Tasks 10–18) revealed the following exact file locations, line numbers, and verbatim findings:

### 1.1 Task Inventory & File Locations
| Task ID | Component Name | Primary Script / Module Paths | Supporting Files |
|---|---|---|---|
| **Task 10** | `conexao` (Multi-protocol Connection Modes) | `Modulos/conexao` | `Modulos/slow_dns`, `Modulos/slowdns`, `Modulos/instsqd`, `Modulos/open.py`, `Modulos/proxy.py`, `Modulos/wsproxy.py`, `Install/instsqd`, `Install/squid3`, `Install/EasyRSA-3.0.1.tgz`, `stunnel.pem`, `src/axiom/services/wireguard.py`, `src/axiom/services/xray.py`, `src/axiom/services/hysteria.py`, `src/axiom/services/singbox.py` |
| **Task 11** | `speedtest` / `velocity` | `Modulos/speedtest`, `Modulos/menu` (lines 32-70) | `Modulos/menu` (case 11) |
| **Task 12** | `banner` (SSH & Dropbear Login Banner) | `Modulos/banner` | `/etc/bannerssh`, `/etc/ssh/sshd_config`, `/etc/default/dropbear` |
| **Task 13** | `nload` (Interface Bandwidth Visualization) | `Modulos/menu` (lines 366-381) | `src/axiom/monitor/bandwidth.py` |
| **Task 14** | `otimizar` (Memory & Swap Maintenance) | `Modulos/otimizar` | `/proc/sys/vm/drop_caches`, `/proc/meminfo` |
| **Task 15** | `userbackup` (Encrypted Local Archives) | `Modulos/userbackup` | `src/axiom/users/backup.py`, `systemd/axiom-backup.service`, `systemd/axiom-backup.timer` |
| **Task 16** | `limiter` / `limit_ssh` (Excess Session Killer) | `Modulos/limiter`, `Modulos/droplimiter` | `Modulos/menu` (lines 71-107), `Modulos/conexao` (lines 343-348) |
| **Task 17** | `badvpn` (BadVPN UDP Gateway 7300) | `Modulos/badvpn` | `Modulos/badvpn-udpgw`, `Install/badvpn-udpgw` |
| **Task 18** | `detalhes` (System & Port Diagnostics) | `Modulos/detalhes` | `src/axiom/monitor/stats.py` |

---

### 1.2 Verbatim Code Observations & Vulnerability Findings

#### [Task 10] `Modulos/conexao` & Protocol Subcomponents
1. **Anti-Tamper License Gating**:
   - `Modulos/conexao:9`:
     ```bash
     [[ $(awk -F" " '{print $2}' /usr/lib/licence) == "@DRAGON_VPS_MANAGER" ]] && {
     ```
   - `Modulos/conexao:1981`:
     ```bash
     [[ ! -e '/home/vpsmanager' ]] && exit 0
     ```
   - *Finding*: If `/usr/lib/licence` or `/home/vpsmanager` is absent, `conexao` exits silently without running or providing any output.

2. **Webroot Exposure of OpenVPN Client Configs & Certificates**:
   - `Modulos/conexao:957-969` (`fun_apchon`):
     ```bash
     fun_apchon() {
         apt-get install apache2 zip -y
         sed -i "s/Listen 80/Listen 81/g" /etc/apache2/ports.conf
         service apache2 restart
         [[ ! -d /var/www/html ]] && { mkdir /var/www/html; }
         [[ ! -d /var/www/html/openvpn ]] && { mkdir /var/www/html/openvpn; }
         touch /var/www/html/openvpn/index.html
         chmod -R 755 /var/www
         /etc/init.d/apache2 restart
     }
     ```
   - *Finding*: Installs Apache2 listening on public port 81 and exposes `/var/www/html/openvpn` with world-readable permissions (`chmod -R 755 /var/www`), allowing unauthenticated internet users to download `.ovpn` configuration profiles and certificates.

3. **Destructive Global Firewall Flush**:
   - `Modulos/conexao:1336`:
     ```bash
     iptables -F
     ```
   - *Finding*: OpenVPN setup runs `iptables -F`, which flushes and wipes all system firewall filter rules indiscriminately.

4. **Insecure Temp Files in Dropbear & OpenVPN**:
   - `Modulos/conexao:436, 438`:
     ```bash
     grep -v "^PasswordAuthentication yes" /etc/ssh/sshd_config >/tmp/passlogin && mv /tmp/passlogin /etc/ssh/sshd_config
     grep -v "^PermitTunnel yes" /etc/ssh/sshd_config >/tmp/ssh && mv /tmp/ssh /etc/ssh/sshd_config
     ```
   - `Modulos/conexao:1023`:
     ```bash
     grep -v "^duplicate-cn" /etc/openvpn/server.conf >/tmp/tmpass && mv /tmp/tmpass /etc/openvpn/server.conf
     ```
   - *Finding*: Static temp files (`/tmp/passlogin`, `/tmp/ssh`, `/tmp/tmpass`) in world-writable `/tmp` are vulnerable to symlink attacks and race conditions.

5. **Hardcoded SSL Private Key in Repository**:
   - Root file: `stunnel.pem` (Lines 1–56): Contains a committed RSA private key and Cloudflare origin certificate for `*.kiritossh.xyz`.
   - `Modulos/conexao:727`: Generates dynamic RSA cert via `openssl req -new -x509 -days 3650 -nodes -newkey rsa:2048 -subj "/CN=axiom" -keyout /etc/stunnel/stunnel.pem -out /etc/stunnel/stunnel.pem`, but repository still contains the leaked `stunnel.pem` artifact in root.

6. **SlowDNS Daemon & Client Vulnerabilities**:
   - `Modulos/slowdns:26`: `curl -sSL -O https://raw.githubusercontent.com/pamidu1540/axiom-vps-manager/main/Modulos/dns` (unverified binary download over internet).
   - `Modulos/slowdns:61`: Hardcoded external IP address `dns='187.50.250.115'`.
   - `Modulos/slowdns:66-67`: `piddns=$(ps x| grep -w 'dns' | grep -v 'grep'| awk -F' ' {'print $1'}); kill ${piddns}` (reckless matching).
   - `Modulos/slow_dns:25`: Downloads `dns-server` binary over HTTP curl without SHA256 checksum integrity verification.

7. **Deprecated OpenVPN 2.5+/2.6+ Options**:
   - `Modulos/conexao:1300-1301, 1311`:
     ```text
     cipher AES-256-CBC
     comp-lzo yes
     client-cert-not-required
     ```
   - *Finding*: `cipher` is deprecated in favor of `data-ciphers AES-256-GCM:AES-128-GCM:CHACHA20-POLY1305`; `comp-lzo yes` is vulnerable to VORACLE and deprecated; `client-cert-not-required` is replaced by `verify-client-cert none`.

---

#### [Task 11] `Modulos/speedtest` & `Modulos/menu`
- `Modulos/speedtest:10-22`:
  ```bash
  if ! command -v speedtest-cli >/dev/null 2>&1 && ! command -v speedtest >/dev/null 2>&1; then
      echo -e "\033[1;33m[*] Installing speedtest-cli...\033[0m"
      apt-get update -y >/dev/null 2>&1 || true
      apt-get install -y speedtest-cli >/dev/null 2>&1 || pip install speedtest-cli >/dev/null 2>&1 || true
  fi
  if command -v speedtest-cli >/dev/null 2>&1; then
      speedtest-cli --share || speedtest-cli
  elif command -v speedtest >/dev/null 2>&1; then
      speedtest
  ...
  ```
- *Finding*: Properly handles fallback between `speedtest-cli` and `speedtest` package or pip fallback. `Modulos/menu:32-70` duplicates `velocity()` using `--simple`.

---

#### [Task 12] `Modulos/banner`
- `Modulos/banner:85-96`:
  ```bash
  elif [[ "$ban_cor" = "10" ]]; then
  echo "<h$_size>$msg1</h$_size>" >> $local
  /etc/init.d/ssh restart > /dev/null 2>&1
  echo -e "\n\033[1;32m◇ BANNER ADDED!\033[0m"
  sleep 2
  menu
  else
  ...
  fi
  echo "</font></h$_size>" >> $local
  ```
- *Finding*: Option 10 appends `</font></h$_size>` after returning, producing malformed HTML tags. Banner uses HTML tags (`<font color=...>`, `<h1>`) which standard OpenSSH renders as literal text, but mobile VPN clients parse. Requires clean ASCII formatting fallback.

---

#### [Task 13] `Modulos/nload` & `src/axiom/monitor/bandwidth.py`
- `Modulos/menu:368-380`: Automatically installs `nload` via `apt-get install -y nload` if missing before launching `nload`.
- `src/axiom/monitor/bandwidth.py:11-33`: `BandwidthMonitor.get_interface_stats()` parses `vnstat --json` for automated telemetry metrics.

---

#### [Task 14] `Modulos/otimizar`
- `Modulos/otimizar:8-27`:
  ```bash
  apt-get autoremove -y >/dev/null 2>&1 || true
  apt-get autoclean -y >/dev/null 2>&1 || true
  apt-get clean >/dev/null 2>&1 || true
  sync
  echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
  avail_mem_kb=$(awk '/MemAvailable/ {print $2}' /proc/meminfo || echo "0")
  used_swap_kb=$(awk '/SwapTotal/ {t=$2} /SwapFree/ {f=$2} END {print (t-f)}' /proc/meminfo || echo "0")
  if (( avail_mem_kb > used_swap_kb + 204800 && used_swap_kb > 10240 )); then
      swapoff -a 2>/dev/null || true
      swapon -a 2>/dev/null || true
  ```
- *Finding*: Safe RAM drop and swap recycling safety threshold implemented correctly.

---

#### [Task 15] `Modulos/userbackup` & `systemd/axiom-backup.service`
- `Modulos/userbackup:4-36`: Creates root-only encrypted backups in `/root/backups/` with `chmod 600`, uses `mktemp -d`, and eliminates webroot exposure.
- `systemd/axiom-backup.service:7`:
  ```ini
  ExecStart=/opt/axiom/Modulos/userbackup 1
  ```
- `Modulos/userbackup:17`:
  ```bash
  read -r -p "Select an option [0-3]: " opt
  ```
- *Finding*: `systemd/axiom-backup.service` passes argument `1`, but `Modulos/userbackup` does not parse `$1` non-interactively (`opt="${1:-}"`). Running under systemd timer causes the script to hang on `read` without a TTY.

---

#### [Task 16] `Modulos/limiter` & `Modulos/droplimiter`
- `Modulos/limiter:13-23`:
  ```bash
  mapfile -t ssh_pids < <(pgrep -u "$user" -f "sshd:" 2>/dev/null || pgrep -u "$user" sshd 2>/dev/null || true)
  local active_count="${#ssh_pids[@]}"
  if (( active_count > limit )); then
      local excess=$(( active_count - limit ))
      for (( i=0; i<excess; i++ )); do
          pid_to_kill="${ssh_pids[$(( active_count - 1 - i ))]}"
          kill -9 "$pid_to_kill" 2>/dev/null || true
      done
  fi
  ```
- `Modulos/droplimiter:23-34`: Same selective termination logic applied to Dropbear sessions.
- *Finding*: Correctly prunes only excess sessions instead of running destructive `pkill -u "$user"`.
- *Finding*: Daemon autostart relies on legacy `screen -dmS limiter limiter` in `/etc/autostart` instead of a modern systemd service (`axiom-limiter.service`).

---

#### [Task 17] `Modulos/badvpn`
- `Modulos/badvpn:46, 57`:
  ```bash
  screen -dmS udpvpn /bin/badvpn-udpgw --listen-addr 127.0.0.1:7300 --max-clients 10000 --max-connections-for-client 8
  curl -sSL -o /bin/badvpn-udpgw https://raw.githubusercontent.com/pamidu1540/axiom-vps-manager/main/Modulos/badvpn-udpgw 2>/dev/null || true
  ```
- *Finding*: Downloads binary over raw GitHub URL without checksum verification despite local binary existing in `Modulos/badvpn-udpgw` and `Install/badvpn-udpgw`.
- *Finding*: Uses `screen` and `/etc/autostart` instead of systemd unit (`axiom-badvpn.service`).

---

#### [Task 18] `Modulos/detalhes`
- `Modulos/detalhes:7`: Typo `OPERATING SYSTEML`.
- `Modulos/detalhes:40`: `$(uname -p)` returns `unknown` on most standard Linux distributions; must be replaced by `uname -m`.
- `Modulos/detalhes:70`:
  ```bash
  PT=$(lsof -V -i tcp -P -n | grep -v "ESTABLISHED" |grep -v "COMMAND" | grep "LISTEN")
  ```
- *Finding*: Completely omits UDP listening ports (ignoring BadVPN 7300, SlowDNS 5300, WireGuard 51820, and OpenVPN UDP 1194).

---

## 2. Logic Chain

1. **Premise 1**: Axiom VPS Manager requires zero security vulnerabilities, zero anti-tamper logic bombs, zero public webroot credential exposures, safe temp files, and idempotent daemon lifecycle control across Phase 2.
2. **Step 2 (Task 10)**: Line 9 and Line 1981 of `Modulos/conexao` check for `/usr/lib/licence` and `/home/vpsmanager`, which will break functionality when installed as Axiom. Furthermore, `fun_apchon` exposes `/var/www/html/openvpn` on port 81 without authentication, `iptables -F` wipes user firewall rules, and `/tmp/passlogin` introduces race conditions. Therefore, Task 10 requires removing all license checks, eliminating Apache2 webroot exposure, replacing `iptables -F` with targeted rule insertions, and using `mktemp`.
3. **Step 3 (Tasks 11-14)**: `speedtest` and `otimizar` already possess modern fallback mechanisms and memory safety thresholds. `banner` requires fixing the syntax error in option 10 and offering clean text rendering. `nload` operates smoothly with vnStat telemetry backup.
4. **Step 4 (Task 15)**: `userbackup` generates secure `chmod 600` archives in `/root/backups/`, but its systemd service `axiom-backup.service` hangs due to unhandled non-interactive CLI arguments. Adding `opt="${1:-}"` logic resolves systemd timer execution.
5. **Step 5 (Tasks 16-17)**: `limiter` and `droplimiter` successfully preserve legitimate connections by selectively killing only excess PIDs (`$excess = active_count - limit`). Migrating from `screen` / `/etc/autostart` to systemd units (`axiom-limiter.service` and `axiom-badvpn.service`) ensures production resilience. `badvpn` must use the local binary and verify SHA256 checksums if downloaded.
6. **Step 6 (Task 18)**: `detalhes` must inspect both TCP and UDP listening ports (`ss -tulpn` or `lsof -i -P -n`), use `uname -m` for architecture, and fix header typos.

---

## 3. Caveats

- **Scope Boundary**: This survey focuses exclusively on Phase 2 (Tasks 10–18). User management (Tasks 1–9) and advanced operations/lifecycle (Tasks 19–30) are surveyed in parallel by peer explorers.
- **Local Sandbox Execution**: All investigations are read-only and performed locally in `E:\workspace\playground\DRAGON-VPS-MANAGER`. No source code modifications were performed during this turn.
- **Binary Binaries**: Precompiled binaries (`badvpn-udpgw`, `dns-server`, `dns`) are ELF 64-bit executables. In production deployments, architecture checks (x86_64 vs aarch64) must be validated before running.

---

## 4. Conclusion & Remediation Plan

All 9 tasks in Phase 2 have been thoroughly analyzed. The following remediation plan is prepared for implementation:

### Phase 2 Implementation Roadmap (Tasks 10–18)

| Task | Component | Action Items for Implementer |
|---|---|---|
| **Task 10** | `conexao` | 1. Strip license check (`/usr/lib/licence`) and `/home/vpsmanager` exit condition.<br>2. Delete `fun_apchon` / Apache2 webroot exposure `/var/www/html/openvpn`.<br>3. Replace `iptables -F` with idempotent table checks.<br>4. Update OpenVPN config with `data-ciphers AES-256-GCM:AES-128-GCM:CHACHA20-POLY1305` and `verify-client-cert none`.<br>5. Replace `/tmp/passlogin`, `/tmp/ssh` with `mktemp`.<br>6. Remove committed `stunnel.pem` and verify on-demand openssl generation.<br>7. Sanitize `slowdns` and `slow_dns` to remove hardcoded IP `187.50.250.115` and add integrity checksums. |
| **Task 11** | `speedtest` | Unify `Modulos/speedtest` and `menu` velocity function with silent fallback. |
| **Task 12** | `banner` | Fix HTML tag trailing bracket in option 10; add clean ANSI/text formatting and idempotent banner config lines. |
| **Task 13** | `nload` | Maintain auto-installer in `menu` and vnstat JSON telemetry in `src/axiom/monitor/bandwidth.py`. |
| **Task 14** | `otimizar` | Retain safe swap threshold (`avail_mem_kb > used_swap_kb + 204800`) and pagecache drop. |
| **Task 15** | `userbackup` | Update `Modulos/userbackup` to support non-interactive CLI execution (`$1`) for `systemd/axiom-backup.service`. |
| **Task 16** | `limiter` | Retain selective excess PID pruning; add systemd unit `axiom-limiter.service` while keeping screen fallback. |
| **Task 17** | `badvpn` | Add `axiom-badvpn.service` systemd unit; install from local `Install/badvpn-udpgw` with SHA256 integrity check. |
| **Task 18** | `detalhes` | Fix typo `OPERATING SYSTEML`; switch `$(uname -p)` to `uname -m`; enumerate both TCP and UDP listening ports (`ss -tulpn`). |

---

## 5. Verification Method

To independently verify all Phase 2 components after implementation:

1. **Syntax & Static Verification**:
   ```bash
   bash -n Modulos/conexao
   bash -n Modulos/speedtest
   bash -n Modulos/banner
   bash -n Modulos/otimizar
   bash -n Modulos/userbackup
   bash -n Modulos/limiter
   bash -n Modulos/droplimiter
   bash -n Modulos/badvpn
   bash -n Modulos/detalhes
   ```
2. **Python Unit Tests & Linting**:
   ```bash
   pytest tests/test_services.py tests/test_scanner.py -v
   ruff check src/ tests/
   ```
3. **Security Invariant Verification**:
   - Check no webroot directories created under `/var/www/html/`
   - Verify `stunnel.pem` is generated on-demand and not hardcoded
   - Verify `iptables -F` is nowhere in `Modulos/conexao`
   - Verify `mktemp` is used for all temporary file transformations
   - Verify `Modulos/userbackup 1` runs non-interactively and exits code 0.

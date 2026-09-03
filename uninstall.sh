#!/usr/bin/env bash
# ==============================================================================
# Axiom VPS Manager — Clean Uninstaller
# Version: 1.0.1
# License: GPL-3.0
# ==============================================================================

# 1. Self-Re-exec from /tmp if invoked from within /opt/axiom to prevent self-deletion crashes
CURRENT_SCRIPT="${BASH_SOURCE[0]:-$0}"
if [[ "$CURRENT_SCRIPT" != "/tmp/axiom-uninstall.sh" ]]; then
    if cp -f "$CURRENT_SCRIPT" /tmp/axiom-uninstall.sh 2>/dev/null; then
        chmod +x /tmp/axiom-uninstall.sh 2>/dev/null
        exec /tmp/axiom-uninstall.sh "$@"
    fi
fi

CLR_RESET='\033[0m'
CLR_RED='\033[1;31m'
CLR_GREEN='\033[1;32m'
CLR_YELLOW='\033[1;33m'
CLR_BLUE='\033[1;34m'
CLR_CYAN='\033[1;36m'
CLR_BOLD='\033[1m'

clear
echo -e "${CLR_RED}======================================================${CLR_RESET}"
echo -e "${CLR_YELLOW}${CLR_BOLD}       ⚡ Axiom VPS Manager — Uninstaller ⚡          ${CLR_RESET}"
echo -e "${CLR_RED}======================================================${CLR_RESET}\n"

# 2. Require Root Privileges
if [[ "$(id -u)" -ne 0 ]]; then
    echo -e "${CLR_RED}[!] Error: The uninstaller must be run as root.${CLR_RESET}" >&2
    exit 1
fi

AUTO_CONFIRM=0
if [[ "${1:-}" == "-y" || "${1:-}" == "--yes" ]]; then
    AUTO_CONFIRM=1
fi

if [[ $AUTO_CONFIRM -eq 0 ]]; then
    echo -e "${CLR_YELLOW}[!] Warning: This will completely remove Axiom VPS Manager and its background services.${CLR_RESET}\n"
    read -r -p "Are you sure you want to proceed with uninstallation? [y/N]: " confirm
    if [[ ! "$confirm" =~ ^[yY]$ ]]; then
        echo -e "\n${CLR_GREEN}[✓] Uninstallation cancelled. No changes were made.${CLR_RESET}\n"
        exit 0
    fi

    # 3. Offer Backup Option
    echo ""
    read -r -p "Do you want to create a final backup of user data (/root/usuarios.db) before removal? [Y/n]: " backup_choice
    if [[ ! "$backup_choice" =~ ^[nN]$ ]]; then
        BACKUP_FILE="/root/axiom_pre_uninstall_$(date +%Y%m%d_%H%M%S).tar.gz"
        echo -e "${CLR_BLUE}[*] Creating backup archive at $BACKUP_FILE...${CLR_RESET}"
        tar -czf "$BACKUP_FILE" -C / root/usuarios.db etc/axiom etc/VPSManager 2>/dev/null || true
        chmod 600 "$BACKUP_FILE" 2>/dev/null || true
        echo -e "${CLR_GREEN}[✓] Backup preserved at: $BACKUP_FILE${CLR_RESET}\n"
    fi
fi

# 4. Stop and Disable Systemd Daemons & Timers
echo -e "${CLR_BLUE}[*] Stopping and disabling Axiom systemd services...${CLR_RESET}"
AXIOM_SERVICES=(
    "axiom-wsproxy.service"
    "axiom-bot.service"
    "axiom-backup.service"
    "axiom-backup.timer"
    "axiom-limiter.service"
    "axiom-badvpn.service"
)

for svc in "${AXIOM_SERVICES[@]}"; do
    systemctl stop "$svc" 2>/dev/null || true
    systemctl disable "$svc" 2>/dev/null || true
    rm -f "/etc/systemd/system/$svc" 2>/dev/null || true
done

# Kill running auxiliary screen / background proxy sessions
pkill -f "dns-server -udp :5300" 2>/dev/null || true
pkill -f "badvpn-udpgw" 2>/dev/null || true
pkill -f "proxy.py" 2>/dev/null || true
pkill -f "wsproxy.py" 2>/dev/null || true
pkill -f "open.py" 2>/dev/null || true

systemctl daemon-reload 2>/dev/null || true

# 5. Clean Crontab (Remove only Axiom entries without clearing unrelated jobs)
echo -e "${CLR_BLUE}[*] Removing Axiom scheduled cron tasks...${CLR_RESET}"
if crontab -l >/dev/null 2>&1; then
    tmp_cron=$(mktemp 2>/dev/null || echo "/tmp/axiom_cron.tmp")
    crontab -l 2>/dev/null | grep -vE "(verifatt|uexpired|verifbot|onlineapp\.sh|axiom)" > "$tmp_cron" 2>/dev/null || true
    if [[ -s "$tmp_cron" ]]; then
        crontab "$tmp_cron" 2>/dev/null || true
    else
        crontab -r 2>/dev/null || true
    fi
    rm -f "$tmp_cron" 2>/dev/null || true
fi

# 6. Clean Firewall Rules
echo -e "${CLR_BLUE}[*] Removing Axiom firewall chains...${CLR_RESET}"
if command -v nft >/dev/null 2>&1; then
    nft delete table inet axiom 2>/dev/null || true
fi

if command -v iptables >/dev/null 2>&1; then
    iptables -D FORWARD -j AXIOM_TORRENT 2>/dev/null || true
    iptables -D OUTPUT -j AXIOM_TORRENT 2>/dev/null || true
    iptables -F AXIOM_TORRENT 2>/dev/null || true
    iptables -X AXIOM_TORRENT 2>/dev/null || true
fi

# 7. Remove Shell Profile Hooks
echo -e "${CLR_BLUE}[*] Cleaning shell login profiles...${CLR_RESET}"
sed -i '/menu;/d' /etc/profile 2>/dev/null || true
sed -i '/axiom/d' /etc/profile 2>/dev/null || true
sed -i '/autostart/d' /etc/profile 2>/dev/null || true
rm -f /etc/profile.d/axiom.sh 2>/dev/null || true

# 8. Uninstall Python package if installed
if command -v pip3 >/dev/null 2>&1; then
    pip3 uninstall -y axiom-vps-manager >/dev/null 2>&1 || true
fi

# 9. Remove Binary Symlinks and Installation Directories
echo -e "${CLR_BLUE}[*] Removing installation files and symlinks...${CLR_RESET}"
rm -f /usr/local/bin/axiom /bin/axiom /usr/bin/axiom 2>/dev/null || true
rm -f /usr/local/bin/axiom-cli /bin/axiom-cli /usr/bin/axiom-cli 2>/dev/null || true
rm -f /usr/local/bin/menu /bin/menu /usr/bin/menu 2>/dev/null || true
rm -f /usr/local/bin/axiom-uninstall /bin/axiom-uninstall /usr/bin/axiom-uninstall 2>/dev/null || true

rm -rf /opt/axiom
rm -rf /etc/axiom
rm -rf /var/log/axiom
rm -rf /etc/VPSManager
rm -f /etc/IP
rm -f /etc/Plus-torrent
rm -f /etc/autostart

# Clean all module binaries from /usr/local/bin, /bin, and /usr/bin
ALL_BINS=(
    "addhost" "delhost" "alterarsenha" "criarusuario" "expcleaner" "mudardata"
    "remover" "criarteste" "verifbot" "droplimiter" "alterarlimite" "ajuda"
    "sshmonitor" "badvpn" "badvpn-udpgw" "userbackup" "instsqd" "blockt" "otimizar" "speedtest"
    "banner" "senharoot" "reiniciarservicos" "reiniciarsistema" "attscript"
    "conexao" "delscript" "detalhes" "botssh" "botteste" "botgen" "infousers"
    "verifatt" "limiter" "uexpired" "cabecalho" "bot" "botsshteste" "botgerador"
    "slow_dns" "slowdns" "versao" "dns" "dns-server" "onlineapp.sh" "open.py" "proxy.py" "wsproxy.py" "autoexec" "menu2"
)

for bin in "${ALL_BINS[@]}"; do
    rm -f "/usr/local/bin/$bin" "/bin/$bin" "/usr/bin/$bin" 2>/dev/null || true
done

echo -e "\n${CLR_GREEN}======================================================${CLR_RESET}"
echo -e "${CLR_GREEN}${CLR_BOLD}  ✔ Axiom VPS Manager Has Been Completely Removed     ${CLR_RESET}"
echo -e "${CLR_GREEN}======================================================${CLR_RESET}\n"

# 10. Clean temp uninstaller script and terminate any orphaned menu loops
rm -f /tmp/axiom-uninstall.sh 2>/dev/null || true
pkill -f "axiom" 2>/dev/null || true
pkill -f "/opt/axiom/Modulos/menu" 2>/dev/null || true
exit 0

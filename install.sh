#!/usr/bin/env bash
# ==============================================================================
# Axiom VPS Manager — Modern, Secure & High-Performance Installer
# Version: 1.0.2
# License: GPL-3.0
# Repository: https://github.com/pamidu1540/axiom-vps-manager
# ==============================================================================

set -euo pipefail

AXIOM_VERSION="1.0.2"
REPO_OWNER="pamidu1540"
REPO_NAME="axiom-vps-manager"
REPO_BRANCH="main"
RAW_BASE_URL="https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${REPO_BRANCH}"
GITHUB_REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}"

INSTALL_DIR="/opt/axiom"
BACKUP_DIR="/root/backups"

CLR_RESET='\033[0m'
CLR_RED='\033[1;31m'
CLR_GREEN='\033[1;32m'
CLR_YELLOW='\033[1;33m'
CLR_BLUE='\033[1;34m'
CLR_CYAN='\033[1;36m'
CLR_BOLD='\033[1m'

clear
echo -e "${CLR_CYAN}======================================================${CLR_RESET}"
echo -e "${CLR_YELLOW}${CLR_BOLD}       ⚡ Axiom VPS Manager — Installer v${AXIOM_VERSION} ⚡       ${CLR_RESET}"
echo -e "${CLR_CYAN}======================================================${CLR_RESET}\n"

# 1. Assert Root
if [[ "$(id -u)" -ne 0 ]]; then
    echo -e "${CLR_RED}[!] Error: This installer must be run as root.${CLR_RESET}" >&2
    exit 1
fi

# 2. OS and Architecture Pre-flight Checks
echo -e "${CLR_BLUE}[*] Performing system pre-flight checks...${CLR_RESET}"

if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    OS_NAME="${ID:-unknown}"
    OS_VER="${VERSION_ID:-0}"
else
    echo -e "${CLR_RED}[!] Unsupported Linux distribution: missing /etc/os-release.${CLR_RESET}" >&2
    exit 1
fi

if [[ "$OS_NAME" != "ubuntu" && "$OS_NAME" != "debian" ]]; then
    echo -e "${CLR_YELLOW}[!] Warning: Axiom is optimized for Ubuntu 22.04+ and Debian 12+. Continuing...${CLR_RESET}"
fi

# 3. Update repositories and install dependencies
echo -e "${CLR_BLUE}[*] Updating package index and installing core dependencies...${CLR_RESET}"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y >/dev/null 2>&1 || true

PACKAGES=(
    "python3"
    "python3-pip"
    "python3-setuptools"
    "curl"
    "wget"
    "unzip"
    "tar"
    "jq"
    "lsof"
    "net-tools"
    "nftables"
    "iptables"
    "cron"
    "at"
    "procps"
    "bc"
    "ca-certificates"
    "openssh-server"
    "screen"
    "git"
    "nload"
)

for pkg in "${PACKAGES[@]}"; do
    if ! dpkg -s "$pkg" >/dev/null 2>&1; then
        echo -e "    -> Installing $pkg..."
        apt-get install -y "$pkg" >/dev/null 2>&1 || true
    fi
done

# Ensure python symlink points to python3
if ! command -v python >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
    ln -sf "$(command -v python3)" /usr/bin/python 2>/dev/null || true
    ln -sf "$(command -v python3)" /usr/local/bin/python 2>/dev/null || true
fi

# 4. Configure Shells & SSH Server for VPS Tunneling
echo -e "${CLR_BLUE}[*] Hardening and configuring SSH server for VPN tunnels...${CLR_RESET}"

# Register non-interactive shells in /etc/shells so password logins are never rejected
if ! grep -q "^/bin/false" /etc/shells 2>/dev/null; then
    echo "/bin/false" >> /etc/shells
fi
if ! grep -q "^/usr/sbin/nologin" /etc/shells 2>/dev/null; then
    echo "/usr/sbin/nologin" >> /etc/shells
fi

# Configure SSH daemon for password authentication and tunneling
mkdir -p /etc/ssh/sshd_config.d
cat << 'EOF' > /etc/ssh/sshd_config.d/99-axiom.conf
# Axiom VPS Manager — SSH Tunneling Configuration
Port 22
PasswordAuthentication yes
PermitRootLogin yes
PermitTunnel yes
TCPKeepAlive yes
ClientAliveInterval 60
ClientAliveCountMax 3
Banner /etc/bannerssh
EOF
chmod 644 /etc/ssh/sshd_config.d/99-axiom.conf

# Also patch main sshd_config for systems that do not include sshd_config.d/
if [[ -f /etc/ssh/sshd_config ]]; then
    sed -i -E 's/^#?Port 22/Port 22/' /etc/ssh/sshd_config 2>/dev/null || true
    sed -i -E 's/^#?PasswordAuthentication (no|yes)/PasswordAuthentication yes/' /etc/ssh/sshd_config 2>/dev/null || true
    sed -i -E 's/^#?PermitRootLogin .*/PermitRootLogin yes/' /etc/ssh/sshd_config 2>/dev/null || true
    if ! grep -q "^PasswordAuthentication yes" /etc/ssh/sshd_config 2>/dev/null; then
        echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
    fi
    if ! grep -q "^PermitTunnel yes" /etc/ssh/sshd_config 2>/dev/null; then
        echo "PermitTunnel yes" >> /etc/ssh/sshd_config
    fi
fi

# Enable IPv4 Kernel Forwarding permanently
mkdir -p /etc/sysctl.d
echo "net.ipv4.ip_forward=1" > /etc/sysctl.d/99-axiom.conf
sysctl -p /etc/sysctl.d/99-axiom.conf >/dev/null 2>&1 || sysctl --system >/dev/null 2>&1 || true

# Safely restart SSH
if systemctl is-active --quiet sshd 2>/dev/null; then
    systemctl restart sshd 2>/dev/null || true
elif systemctl is-active --quiet ssh 2>/dev/null; then
    systemctl restart ssh 2>/dev/null || true
else
    service ssh restart >/dev/null 2>&1 || service sshd restart >/dev/null 2>&1 || true
fi

# 5. Create Directory Layout
echo -e "${CLR_BLUE}[*] Creating directory structures...${CLR_RESET}"
mkdir -p -m 755 "$INSTALL_DIR"
mkdir -p -m 700 "$BACKUP_DIR"
mkdir -p -m 755 /var/log/axiom
mkdir -p -m 755 /etc/axiom
mkdir -p -m 755 /etc/axiom/lib
mkdir -p -m 755 /etc/VPSManager
mkdir -p -m 755 /etc/VPSManager/userteste
mkdir -p -m 755 /etc/VPSManager/senha
mkdir -p -m 700 /etc/VPSManager/.tmp
mkdir -p -m 755 /etc/openvpn
mkdir -p -m 755 /var/www/html/server
touch /root/usuarios.db
chmod 600 /root/usuarios.db 2>/dev/null || true

# 6. Ingest or Download Codebase
echo -e "${CLR_BLUE}[*] Fetching Axiom components from repository...${CLR_RESET}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"
if [[ -n "$SCRIPT_DIR" && -d "$SCRIPT_DIR/Modulos" && -f "$SCRIPT_DIR/install.sh" ]]; then
    echo -e "    -> Installing from local workspace ($SCRIPT_DIR)..."
    cp -rf "$SCRIPT_DIR"/* "$INSTALL_DIR/" 2>/dev/null || true
else
    echo -e "    -> Fetching latest release archive from ${GITHUB_REPO_URL}..."
    TMP_DIR=$(mktemp -d)
    if curl -fsSL "${GITHUB_REPO_URL}/archive/refs/heads/${REPO_BRANCH}.tar.gz" -o "$TMP_DIR/axiom.tar.gz"; then
        tar -xzf "$TMP_DIR/axiom.tar.gz" -C "$TMP_DIR"
        EXTRACTED_DIR=$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)
        if [[ -n "$EXTRACTED_DIR" && -d "$EXTRACTED_DIR/Modulos" ]]; then
            cp -rf "$EXTRACTED_DIR"/* "$INSTALL_DIR/"
        fi
        rm -rf "$TMP_DIR"
    else
        echo -e "    -> Falling back to git clone..."
        rm -rf "$TMP_DIR"
        git clone --depth 1 "${GITHUB_REPO_URL}.git" "$INSTALL_DIR" || true
    fi
fi

# Ensure correct executable permissions
chmod -R 755 "$INSTALL_DIR"/Modulos/* 2>/dev/null || true
chmod -R 755 "$INSTALL_DIR"/lib/* 2>/dev/null || true
chmod 755 "$INSTALL_DIR"/install.sh 2>/dev/null || true
chmod 755 "$INSTALL_DIR"/uninstall.sh 2>/dev/null || true

# Sync common library to /etc/axiom/lib
if [[ -d "$INSTALL_DIR/lib" ]]; then
    cp -rf "$INSTALL_DIR/lib"/* /etc/axiom/lib/ 2>/dev/null || true
    chmod -R 755 /etc/axiom/lib/* 2>/dev/null || true
fi

# Populate /etc/VPSManager dependencies
if [[ -f "$INSTALL_DIR/Install/ShellBot.sh" ]]; then
    cp -f "$INSTALL_DIR/Install/ShellBot.sh" /etc/VPSManager/ShellBot.sh
    chmod 755 /etc/VPSManager/ShellBot.sh
fi
for vps_tool in bot botgerador botsshteste open.py proxy.py wsproxy.py cabecalho; do
    if [[ -f "$INSTALL_DIR/Modulos/$vps_tool" ]]; then
        cp -f "$INSTALL_DIR/Modulos/$vps_tool" "/etc/VPSManager/$vps_tool"
        chmod 755 "/etc/VPSManager/$vps_tool"
    fi
done
if [[ -f "$INSTALL_DIR/Install/EasyRSA-3.0.1.tgz" ]]; then
    cp -f "$INSTALL_DIR/Install/EasyRSA-3.0.1.tgz" /etc/openvpn/EasyRSA-3.0.1.tgz 2>/dev/null || true
fi

# 7. Install Systemd Services
echo -e "${CLR_BLUE}[*] Configuring background daemons and systemd units...${CLR_RESET}"
if [[ -d "$INSTALL_DIR/systemd" ]]; then
    for s_file in "$INSTALL_DIR"/systemd/*.service; do
        if [[ -f "$s_file" ]]; then
            cp -f "$s_file" /etc/systemd/system/
            chmod 644 "/etc/systemd/system/$(basename "$s_file")"
        fi
    done
    systemctl daemon-reload 2>/dev/null || true
fi

# Enable auxiliary timers & cron
systemctl enable --now atd 2>/dev/null || true
systemctl enable --now cron 2>/dev/null || systemctl enable --now crond 2>/dev/null || true

# 8. Setup /etc/autostart & Cron Watchdogs
if [[ ! -f /etc/autostart ]]; then
    cat << 'EOF' > /etc/autostart
#!/usr/bin/env bash
# Axiom VPS Manager — Service Watchdog & Auto-Start
clear
EOF
    chmod +x /etc/autostart
fi

# Register automated crontab tasks safely
echo -e "${CLR_BLUE}[*] Registering system maintenance crontabs...${CLR_RESET}"
(
    crontab -l 2>/dev/null | grep -vE "(uexpired|onlineapp|verifatt|autostart)" || true
    echo "@reboot /etc/autostart"
    echo "* * * * * /etc/autostart"
    echo "0 */6 * * * /usr/local/bin/uexpired"
    echo "*/1 * * * * /usr/local/bin/onlineapp.sh"
    echo "@daily /usr/local/bin/verifatt"
) | crontab - 2>/dev/null || true

# 9. Setup CLI Symlinks for ALL modules and commands
echo -e "${CLR_BLUE}[*] Registering global command symlinks in /usr/local/bin, /usr/bin, and /bin...${CLR_RESET}"
if [[ -d "$INSTALL_DIR/Modulos" ]]; then
    for mod in "$INSTALL_DIR/Modulos"/*; do
        if [[ -f "$mod" ]]; then
            mod_name=$(basename "$mod")
            chmod 755 "$mod" 2>/dev/null || true
            ln -sf "$mod" "/usr/local/bin/$mod_name"
            ln -sf "$mod" "/bin/$mod_name" 2>/dev/null || true
            ln -sf "$mod" "/usr/bin/$mod_name" 2>/dev/null || true
        fi
    done
fi

# Uninstaller link
if [[ -f "$INSTALL_DIR/uninstall.sh" ]]; then
    chmod 755 "$INSTALL_DIR/uninstall.sh"
    ln -sf "$INSTALL_DIR/uninstall.sh" /usr/local/bin/axiom-uninstall
    ln -sf "$INSTALL_DIR/uninstall.sh" /bin/axiom-uninstall 2>/dev/null || true
    ln -sf "$INSTALL_DIR/uninstall.sh" /usr/bin/axiom-uninstall 2>/dev/null || true
fi

# 10. Global PATH Profile & Boot Auto-Launch Hook
cat << 'EOF' > /etc/profile.d/axiom.sh
export PATH="/opt/axiom/Modulos:/usr/local/bin:/usr/bin:/bin:$PATH"
export PYTHONPATH="/opt/axiom/src:${PYTHONPATH:-}"

# Auto-launch Axiom Menu on interactive root login when enabled
if [[ -t 0 && "$-" == *i* && -z "${SSH_ORIGINAL_COMMAND:-}" && -f /etc/axiom/autolaunch ]]; then
    if [[ "$(id -u)" -eq 0 && -x /usr/local/bin/axiom ]]; then
        /usr/local/bin/axiom
    fi
fi
EOF
chmod 644 /etc/profile.d/axiom.sh 2>/dev/null || true

# Also hook /root/.bashrc for interactive VM consoles / subshells
if [[ -f /root/.bashrc ]] && ! grep -q "axiom/autolaunch" /root/.bashrc 2>/dev/null; then
    cat << 'EOF' >> /root/.bashrc

# Axiom VPS Manager — VM Console Auto-Launch
if [[ -t 0 && "$-" == *i* && -z "${SSH_ORIGINAL_COMMAND:-}" && -f /etc/axiom/autolaunch ]]; then
    if [[ "$(id -u)" -eq 0 && -x /usr/local/bin/axiom ]]; then
        /usr/local/bin/axiom
    fi
fi
EOF
fi

# Enable auto-launch by default on fresh install
touch /etc/axiom/autolaunch 2>/dev/null || true

# Configure clean Axiom login banner for VM / SSH login
cat << 'EOF' > /etc/issue.net
⚡ Axiom VPS Manager Node (Authorized Access Only) ⚡
EOF
cp -f /etc/issue.net /etc/motd 2>/dev/null || true

# 11. Version metadata files
if [[ -f "$INSTALL_DIR/Install/versao" ]]; then
    cp "$INSTALL_DIR/Install/versao" /etc/axiom/versao 2>/dev/null || true
    cp "$INSTALL_DIR/Install/versao" /bin/versao 2>/dev/null || true
    cp "$INSTALL_DIR/Install/versao" /opt/axiom/versao 2>/dev/null || true
    cp "$INSTALL_DIR/Install/versao" /etc/VPSManager/versao 2>/dev/null || true
fi

# 12. Record Public IP Address
PUBLIC_IP=$(curl -s -4 --connect-timeout 5 ifconfig.me || curl -s -4 --connect-timeout 5 icanhazip.com || echo "127.0.0.1")
echo "$PUBLIC_IP" > /etc/IP

# 13. Install Python package if Python 3 environment is present
if command -v pip3 >/dev/null 2>&1; then
    echo -e "${CLR_BLUE}[*] Installing Axiom Python package...${CLR_RESET}"
    pip3 install --break-system-packages -e "$INSTALL_DIR" 2>/dev/null || pip3 install -e "$INSTALL_DIR" 2>/dev/null || true
fi

# 14. Primary CLI Entrypoint Assertion (Axiom Interactive TUI)
# Ensure /usr/local/bin/axiom ALWAYS launches Modulos/menu
ln -sf "$INSTALL_DIR/Modulos/menu" /usr/local/bin/axiom
ln -sf "$INSTALL_DIR/Modulos/menu" /bin/axiom 2>/dev/null || true
ln -sf "$INSTALL_DIR/Modulos/menu" /usr/bin/axiom 2>/dev/null || true
rm -f /usr/local/bin/menu /bin/menu /usr/bin/menu 2>/dev/null || true

echo -e "\n${CLR_GREEN}======================================================${CLR_RESET}"
echo -e "${CLR_GREEN}${CLR_BOLD}  ✔ Axiom VPS Manager Installed Successfully!         ${CLR_RESET}"
echo -e "${CLR_GREEN}======================================================${CLR_RESET}\n"
echo -e "${CLR_YELLOW}Main CLI Command :${CLR_RESET} ${CLR_CYAN}axiom${CLR_RESET}"
echo -e "${CLR_YELLOW}Public IP        :${CLR_RESET} ${CLR_CYAN}${PUBLIC_IP}${CLR_RESET}"
echo -e "${CLR_YELLOW}Repository       :${CLR_RESET} ${CLR_CYAN}${GITHUB_REPO_URL}${CLR_RESET}\n"

#!/usr/bin/env bash
# ==============================================================================
# Axiom VPS Manager — Modern, Secure & High-Performance Installer
# Version: 1.0.0
# License: MIT
# ==============================================================================

set -euo pipefail

AXIOM_VERSION="1.0.0"
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
    echo -e "${CLR_YELLOW}[!] Warning: Axiom is designed for Ubuntu 22.04+ and Debian 12+. Continuing anyway...${CLR_RESET}"
fi

# 3. Update repositories and install dependencies
echo -e "${CLR_BLUE}[*] Updating package index and installing dependencies...${CLR_RESET}"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y >/dev/null

PACKAGES=(
    "python3"
    "python3-pip"
    "curl"
    "wget"
    "unzip"
    "tar"
    "jq"
    "lsof"
    "net-tools"
    "nftables"
    "cron"
    "openssh-server"
)

for pkg in "${PACKAGES[@]}"; do
    if ! dpkg -s "$pkg" >/dev/null 2>&1; then
        echo -e "    -> Installing $pkg..."
        apt-get install -y "$pkg" >/dev/null 2>&1 || true
    fi
done

# 4. Create Directory Layout
echo -e "${CLR_BLUE}[*] Creating directory structures...${CLR_RESET}"
mkdir -p -m 755 "$INSTALL_DIR"
mkdir -p -m 700 "$BACKUP_DIR"
mkdir -p -m 755 /var/log/axiom
mkdir -p -m 755 /etc/VPSManager
mkdir -p -m 755 /etc/VPSManager/userteste
mkdir -p -m 700 /etc/VPSManager/.tmp
touch /root/usuarios.db

# 5. Copy or Setup Codebase
if [[ -d "$(pwd)/Modulos" ]]; then
    cp -r "$(pwd)"/* "$INSTALL_DIR/" 2>/dev/null || true
fi

# Ensure permissions
chmod -R 755 "$INSTALL_DIR"/Modulos/* 2>/dev/null || true
chmod 755 "$INSTALL_DIR"/lib/* 2>/dev/null || true

# 6. Setup CLI Symlink
ln -sf "$INSTALL_DIR/Modulos/menu" /usr/local/bin/axiom
ln -sf "$INSTALL_DIR/Modulos/menu" /usr/local/bin/menu

# 7. Record IP Address
PUBLIC_IP=$(curl -s -4 --connect-timeout 5 ifconfig.me || curl -s -4 --connect-timeout 5 icanhazip.com || echo "127.0.0.1")
echo "$PUBLIC_IP" > /etc/IP

echo -e "\n${CLR_GREEN}======================================================${CLR_RESET}"
echo -e "${CLR_GREEN}${CLR_BOLD}  ✔ Axiom VPS Manager Installed Successfully!         ${CLR_RESET}"
echo -e "${CLR_GREEN}======================================================${CLR_RESET}\n"
echo -e "${CLR_YELLOW}Main CLI Command :${CLR_RESET} ${CLR_CYAN}axiom${CLR_RESET} or ${CLR_CYAN}menu${CLR_RESET}"
echo -e "${CLR_YELLOW}Public IP        :${CLR_RESET} ${CLR_CYAN}${PUBLIC_IP}${CLR_RESET}"
echo -e "${CLR_YELLOW}Documentation    :${CLR_RESET} ${CLR_CYAN}https://github.com/januda-ui/DRAGON-VPS-MANAGER${CLR_RESET}\n"

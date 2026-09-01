#!/usr/bin/env bash
# ==============================================================================
# Axiom VPS Manager — Modern, Secure & High-Performance Installer
# Version: 1.0.0
# License: GPL-3.0
# Repository: https://github.com/pamidu1540/axiom-vps-manager
# ==============================================================================

set -euo pipefail

AXIOM_VERSION="1.0.0"
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
    "screen"
    "git"
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
mkdir -p -m 755 /etc/axiom
mkdir -p -m 755 /etc/axiom/lib
mkdir -p -m 755 /etc/VPSManager
mkdir -p -m 755 /etc/VPSManager/userteste
mkdir -p -m 700 /etc/VPSManager/.tmp
touch /root/usuarios.db
chmod 600 /root/usuarios.db 2>/dev/null || true

# 5. Ingest or Download Codebase
echo -e "${CLR_BLUE}[*] Fetching Axiom components from GitHub repository...${CLR_RESET}"

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

# 6. Setup CLI Symlinks for ALL modules and commands
echo -e "${CLR_BLUE}[*] Registering global command symlinks in /usr/local/bin and /bin...${CLR_RESET}"
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

# Main entrypoints & aliases
ln -sf "$INSTALL_DIR/Modulos/menu" /usr/local/bin/axiom
ln -sf "$INSTALL_DIR/Modulos/menu" /bin/axiom 2>/dev/null || true
ln -sf "$INSTALL_DIR/Modulos/menu" /usr/bin/axiom 2>/dev/null || true
ln -sf "$INSTALL_DIR/Modulos/menu" /usr/local/bin/menu
ln -sf "$INSTALL_DIR/Modulos/menu" /bin/menu 2>/dev/null || true
ln -sf "$INSTALL_DIR/Modulos/menu" /usr/bin/menu 2>/dev/null || true

if [[ -f "$INSTALL_DIR/uninstall.sh" ]]; then
    chmod 755 "$INSTALL_DIR/uninstall.sh"
    ln -sf "$INSTALL_DIR/uninstall.sh" /usr/local/bin/axiom-uninstall
    ln -sf "$INSTALL_DIR/uninstall.sh" /bin/axiom-uninstall 2>/dev/null || true
    ln -sf "$INSTALL_DIR/uninstall.sh" /usr/bin/axiom-uninstall 2>/dev/null || true
fi

# 7. Global PATH Profile
cat << 'EOF' > /etc/profile.d/axiom.sh
export PATH="/opt/axiom/Modulos:/usr/local/bin:/usr/bin:/bin:$PATH"
EOF
chmod 644 /etc/profile.d/axiom.sh 2>/dev/null || true

# 8. Version metadata files
if [[ -f "$INSTALL_DIR/Install/versao" ]]; then
    cp "$INSTALL_DIR/Install/versao" /etc/axiom/versao 2>/dev/null || true
    cp "$INSTALL_DIR/Install/versao" /bin/versao 2>/dev/null || true
    cp "$INSTALL_DIR/Install/versao" /opt/axiom/versao 2>/dev/null || true
    cp "$INSTALL_DIR/Install/versao" /etc/VPSManager/versao 2>/dev/null || true
fi

# 9. Record IP Address
PUBLIC_IP=$(curl -s -4 --connect-timeout 5 ifconfig.me || curl -s -4 --connect-timeout 5 icanhazip.com || echo "127.0.0.1")
echo "$PUBLIC_IP" > /etc/IP

# 10. Install Python package if Python 3 environment is present
if command -v pip3 >/dev/null 2>&1; then
    echo -e "${CLR_BLUE}[*] Installing Axiom Python package...${CLR_RESET}"
    pip3 install --break-system-packages -e "$INSTALL_DIR" 2>/dev/null || pip3 install -e "$INSTALL_DIR" 2>/dev/null || true
fi

echo -e "\n${CLR_GREEN}======================================================${CLR_RESET}"
echo -e "${CLR_GREEN}${CLR_BOLD}  ✔ Axiom VPS Manager Installed Successfully!         ${CLR_RESET}"
echo -e "${CLR_GREEN}======================================================${CLR_RESET}\n"
echo -e "${CLR_YELLOW}Main CLI Command :${CLR_RESET} ${CLR_CYAN}axiom${CLR_RESET} or ${CLR_CYAN}menu${CLR_RESET}"
echo -e "${CLR_YELLOW}Public IP        :${CLR_RESET} ${CLR_CYAN}${PUBLIC_IP}${CLR_RESET}"
echo -e "${CLR_YELLOW}Repository       :${CLR_RESET} ${CLR_CYAN}${GITHUB_REPO_URL}${CLR_RESET}\n"

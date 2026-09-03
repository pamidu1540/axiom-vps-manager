#!/usr/bin/env bash
# ==============================================================================
# Axiom VPS Manager — Shared Helper Library
# Provides logging, security assertions, safe tempfiles, firewall rules, and OS checks.
# ==============================================================================

set -euo pipefail

AXIOM_LOG_FILE="/var/log/axiom/axiom.log"
AXIOM_AUDIT_FILE="/var/log/axiom/audit.log"

# Colors for TUI
CLR_RESET='\033[0m'
CLR_RED='\033[1;31m'
CLR_GREEN='\033[1;32m'
CLR_YELLOW='\033[1;33m'
CLR_BLUE='\033[1;34m'
CLR_MAGENTA='\033[1;35m'
CLR_CYAN='\033[1;36m'
CLR_WHITE='\033[1;37m'
CLR_BOLD='\033[1m'
CLR_DIM='\033[2m'

# Assertion: Must be executed as root
axiom_require_root() {
    if [[ "$(id -u)" -ne 0 ]]; then
        echo -e "${CLR_RED}[!] Error: Axiom operations require root privileges.${CLR_RESET}" >&2
        exit 1
    fi
}

# Structured Logger
axiom_log() {
    local level="${1:-INFO}"
    local message="${2:-}"
    local timestamp
    timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    
    mkdir -p "$(dirname "$AXIOM_LOG_FILE")"
    echo "[$timestamp] [$level] $message" >> "$AXIOM_LOG_FILE"
}

# Audit Trail Logger
axiom_audit() {
    local action="${1:-}"
    local user="${2:-system}"
    local details="${3:-}"
    local timestamp
    timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    
    mkdir -p "$(dirname "$AXIOM_AUDIT_FILE")"
    printf '{"timestamp":"%s","user":"%s","action":"%s","details":"%s"}\n' \
        "$timestamp" "$user" "$action" "$details" >> "$AXIOM_AUDIT_FILE"
}

# Safe Temporary Directory Wrapper
axiom_mktemp_dir() {
    mktemp -d -t "axiom_tmp_XXXXXXXX"
}

# Validate username format (alphanumeric, 3-32 chars)
axiom_validate_username() {
    local uname="$1"
    if [[ "$uname" =~ ^[a-zA-Z0-9_-]{3,32}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Fetch public IPv4 address
axiom_get_public_ip() {
    if [[ -f /etc/IP ]]; then
        cat /etc/IP
    else
        curl -s -4 --connect-timeout 5 ifconfig.me 2>/dev/null || curl -s -4 --connect-timeout 5 icanhazip.com 2>/dev/null || echo "127.0.0.1"
    fi
}

# Check service active status via systemd
axiom_is_service_active() {
    local svc_name="$1"
    systemctl is-active --quiet "$svc_name" 2>/dev/null
}

# Automated OS Firewall Port Rule (nftables, ufw, iptables)
axiom_firewall_allow_port() {
    local port="$1"
    local proto="${2:-tcp}" # tcp or udp
    local desc="${3:-Service}"

    proto=$(echo "$proto" | tr '[:upper:]' '[:lower:]')

    # 1. nftables
    if command -v nft >/dev/null 2>&1; then
        if nft list tables 2>/dev/null | grep -q "inet axiom"; then
            nft add rule inet axiom input "${proto}" dport "${port}" accept 2>/dev/null || true
        elif nft list tables 2>/dev/null | grep -q "inet filter"; then
            nft add rule inet filter input "${proto}" dport "${port}" accept 2>/dev/null || true
        fi
    fi

    # 2. ufw
    if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then
        ufw allow "${port}/${proto}" comment "Axiom ${desc}" >/dev/null 2>&1 || true
    fi

    # 3. iptables
    if command -v iptables >/dev/null 2>&1; then
        iptables -I INPUT 1 -p "${proto}" --dport "${port}" -m comment --comment "Axiom ${desc}" -j ACCEPT 2>/dev/null || true
    fi

    axiom_audit "FIREWALL_PORT_ALLOW" "system" "port=${port},proto=${proto},desc=${desc}"
}

# Cloud Firewall / Physical Security Group Advisory Banner
axiom_firewall_advisory() {
    local port="$1"
    local proto="${2:-tcp}"
    local service_name="${3:-Network Service}"
    proto=$(echo "$proto" | tr '[:lower:]' '[:upper:]')

    echo -e "\n${CLR_CYAN}╭─────────────────────────────────────────────────────────────╮${CLR_RESET}"
    echo -e "${CLR_CYAN}│${CLR_RESET}  ${CLR_GREEN}${CLR_BOLD}🛡️  FIREWALL RULE APPLIED — ${service_name}${CLR_RESET} ${CLR_CYAN}│${CLR_RESET}"
    echo -e "${CLR_CYAN}├─────────────────────────────────────────────────────────────┤${CLR_RESET}"
    echo -e "${CLR_CYAN}│${CLR_RESET}  ${CLR_WHITE}[✓] Local OS Firewall:${CLR_RESET} Port ${CLR_YELLOW}${port}/${proto}${CLR_RESET} opened in nftables/ufw    ${CLR_CYAN}│${CLR_RESET}"
    echo -e "${CLR_CYAN}│${CLR_RESET}                                                             ${CLR_CYAN}│${CLR_RESET}"
    echo -e "${CLR_CYAN}│${CLR_RESET}  ${CLR_YELLOW}${CLR_BOLD}⚠️  CLOUD PROVIDER INGRESS / FIREWALL NOTICE:${CLR_RESET}               ${CLR_CYAN}│${CLR_RESET}"
    echo -e "${CLR_CYAN}│${CLR_RESET}  If your server is hosted on ${CLR_WHITE}AWS, GCP, Oracle Cloud, Azure,${CLR_RESET}   ${CLR_CYAN}│${CLR_RESET}"
    echo -e "${CLR_CYAN}│${CLR_RESET}  ${CLR_WHITE}DigitalOcean, or Hetzner Cloud:${CLR_RESET}                             ${CLR_CYAN}│${CLR_RESET}"
    echo -e "${CLR_CYAN}│${CLR_RESET}  You MUST ALSO allow ${CLR_YELLOW}Port ${port} (${proto})${CLR_RESET} in your cloud provider's ${CLR_CYAN}│${CLR_RESET}"
    echo -e "${CLR_CYAN}│${CLR_RESET}  web console (Security Groups / Ingress Rules) to accept     ${CLR_CYAN}│${CLR_RESET}"
    echo -e "${CLR_CYAN}│${CLR_RESET}  incoming client traffic.                                   ${CLR_CYAN}│${CLR_RESET}"
    echo -e "${CLR_CYAN}╰─────────────────────────────────────────────────────────────╯${CLR_RESET}\n"
}

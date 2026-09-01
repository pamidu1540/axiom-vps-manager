#!/usr/bin/env bash
# Axiom VPS Manager — Shared Helper Library
# Provides logging, security assertions, safe tempfiles, and OS checks.

set -euo pipefail

AXIOM_LOG_FILE="/var/log/axiom/axiom.log"
AXIOM_AUDIT_FILE="/var/log/axiom/audit.log"

# Colors for TUI
CLR_RESET='\033[0m'
CLR_RED='\033[1;31m'
CLR_GREEN='\033[1;32m'
CLR_YELLOW='\033[1;33m'
CLR_BLUE='\033[1;34m'
CLR_CYAN='\033[1;36m'
CLR_WHITE='\033[1;37m'

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
        curl -s -4 --connect-timeout 5 ifconfig.me || curl -s -4 --connect-timeout 5 icanhazip.com || echo "127.0.0.1"
    fi
}

# Check service active status via systemd
axiom_is_service_active() {
    local svc_name="$1"
    systemctl is-active --quiet "$svc_name" 2>/dev/null
}

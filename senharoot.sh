#!/usr/bin/env bash
set -euo pipefail

[[ "$(id -u)" -ne 0 ]] && { echo "Error: Must be run as root." >&2; exit 1; }

SSHD_CONFIG="/etc/ssh/sshd_config"

if [[ -f "$SSHD_CONFIG" ]]; then
    # Enable root login
    sed -i -E 's/^#?PermitRootLogin.*/PermitRootLogin yes/' "$SSHD_CONFIG"
    sed -i -E 's/^PermitRootLogin (prohibit-password|without-password)/PermitRootLogin yes/' "$SSHD_CONFIG"

    # Enable password authentication safely without truncation
    if grep -qE '^#?PasswordAuthentication' "$SSHD_CONFIG"; then
        sed -i -E 's/^#?PasswordAuthentication.*/PasswordAuthentication yes/' "$SSHD_CONFIG"
    else
        echo "PasswordAuthentication yes" >> "$SSHD_CONFIG"
    fi

    # Restart SSH daemon
    if systemctl is-active --quiet sshd; then
        systemctl restart sshd
    elif systemctl is-active --quiet ssh; then
        systemctl restart ssh
    else
        service ssh restart 2>/dev/null || service sshd restart 2>/dev/null || true
    fi
fi

echo -e "\033[1;32mSet the root password:\033[0m"
passwd root
rm -f "$0"

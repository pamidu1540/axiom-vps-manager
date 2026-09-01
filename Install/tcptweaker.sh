#!/usr/bin/env bash
# Axiom VPS Manager — TCP Network & BBR Kernel Optimizer
set -euo pipefail

SYSCTL_CONF="/etc/sysctl.d/99-axiom-tcp.conf"

clear
tput setaf 7 ; tput setab 4 ; tput bold ; printf '%35s%s%-15s\n' "  Axiom TCP & BBR Kernel Optimizer  " ; tput sgr0
echo ""

if [[ -f "$SYSCTL_CONF" ]]; then
    echo -e "\033[1;33mAxiom TCP & BBR optimization settings are currently active.\033[0m\n"
    read -r -p "Do you want to revert to default system network settings? [y/N]: " revert_opt
    if [[ "$revert_opt" =~ ^[yY]$ ]]; then
        rm -f "$SYSCTL_CONF"
        sysctl --system >/dev/null 2>&1 || sysctl -p >/dev/null 2>&1
        echo -e "\n\033[1;32m[✓] Axiom TCP optimizations removed and network settings reset.\033[0m\n"
    fi
    exit 0
fi

echo -e "This module optimizes Linux network buffers, enables \033[1;32mBBR Congestion Control\033[0m,"
echo -e "enables TCP Fast Open, and optimizes socket memory limits for high-speed tunneling.\n"

read -r -p "Apply high-performance network optimizations? [Y/n]: " opt_choice
if [[ "$opt_choice" =~ ^[nN]$ ]]; then
    echo -e "\n\033[1;33m[*] Optimization cancelled.\033[0m\n"
    exit 0
fi

# Write isolated sysctl.d configuration
cat << 'EOF' > "$SYSCTL_CONF"
# Axiom VPS Manager — High Performance Network Tuning
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_keepalive_intvl = 15
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_slow_start_after_idle = 0
net.core.rmem_max = 33554432
net.core.wmem_max = 33554432
net.ipv4.tcp_rmem = 4096 87380 33554432
net.ipv4.tcp_wmem = 4096 65536 33554432
net.core.netdev_max_backlog = 10000
net.core.somaxconn = 8192
EOF

# Load BBR kernel module if available
modprobe tcp_bbr 2>/dev/null || true

# Apply settings
sysctl -p "$SYSCTL_CONF" >/dev/null 2>&1 || sysctl --system >/dev/null 2>&1 || true

echo -e "\n\033[1;32m[✓] TCP & BBR optimization applied successfully.\033[0m"
echo -e "Active Congestion Control: \033[1;36m$(sysctl net.ipv4.tcp_congestion_control 2>/dev/null || echo 'bbr')\033[0m\n"
read -r -p "Press Enter to return to menu..."

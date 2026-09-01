#!/usr/bin/env bash
# Axiom VPS Manager — Online Users Metrics for Web Server
set -euo pipefail

mkdir -p /var/www/html/server 2>/dev/null || true
ps -x | grep sshd | grep -v root | grep priv | wc -l > /var/www/html/server/online 2>/dev/null || true
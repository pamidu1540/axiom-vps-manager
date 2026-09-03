#!/usr/bin/env bash
# ==============================================================================
# Axiom VPS Manager — Online Users Metrics for Web Server
# ==============================================================================

mkdir -p /var/www/html/server 2>/dev/null || true
count=$(ps x 2>/dev/null | grep sshd | grep -v root | grep -c priv || echo "0")
echo "$count" > /var/www/html/server/online 2>/dev/null || true
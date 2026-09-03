#!/usr/bin/env bash
# ==============================================================================
# Axiom VPS Manager — Online Users Metrics for Web Server
# ==============================================================================

mkdir -p /var/www/html/server 2>/dev/null || true
count=$(ps x 2>/dev/null | grep sshd | grep -v root | grep priv | wc -l)
count=$(echo "$count" | tr -dc '0-9')
echo "${count:-0}" > /var/www/html/server/online 2>/dev/null || true
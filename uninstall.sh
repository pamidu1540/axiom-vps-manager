#!/usr/bin/env bash
set -euo pipefail
[[ ${EUID} -eq 0 ]] || { echo 'Run as root.' >&2; exit 1; }
if [[ ${1:-} != --yes ]]; then
    read -r -p 'Remove Axiom application? Configuration, backups and managed accounts will remain. [y/N] ' answer
    [[ $answer == y || $answer == Y ]] || exit 0
fi
[[ -d /opt/axiom && ! -L /opt/axiom && -f /opt/axiom/pyproject.toml ]] || {
    echo 'Expected application directory not found; refusing removal.' >&2; exit 1;
}
for unit in axiom-api.service axiom-bot.service axiom-backup.service axiom-backup.timer axiom-expiry.service axiom-expiry.timer; do
    installed="/etc/systemd/system/$unit"
    if [[ -f "$installed" ]] && cmp -s "$installed" "/opt/axiom/systemd/$unit"; then
        systemctl disable --now "$unit" 2>/dev/null || true
        rm -- "$installed"
    elif [[ -e "$installed" ]]; then
        echo "Review modified unit manually: $installed" >&2
        exit 1
    fi
done
for name in axiom axiom-cli axiom-uninstall; do
    target=$(readlink "/usr/local/bin/$name" || true)
    case "$target" in /opt/axiom/*) rm -- "/usr/local/bin/$name" ;; esac
done
systemctl daemon-reload
# Fixed, verified application path only. User data remains outside this directory.
rm -rf -- /opt/axiom
echo 'Application removed. /etc/axiom, /root/backups and managed accounts remain.'
echo 'Expiry timers are stopped. Review or remove remaining managed accounts explicitly.'

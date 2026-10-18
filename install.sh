#!/usr/bin/env bash
# Install from a reviewed checkout. Does not configure SSH or enable network services.
set -euo pipefail
umask 077
[[ ${EUID} -eq 0 ]] || { echo 'Run as root.' >&2; exit 1; }
source /etc/os-release
case "${ID}:${VERSION_ID}" in
    ubuntu:24.04|debian:12|debian:13) ;;
    *) echo 'Requires Ubuntu 24.04 or Debian 12/13 with Python 3.11+.' >&2; exit 1 ;;
esac
command -v systemctl >/dev/null || { echo 'systemd is required.' >&2; exit 1; }
src=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
[[ -f "$src/pyproject.toml" && -d "$src/src/axiom" ]] || {
    echo 'Clone the repository and run install.sh from that checkout.' >&2; exit 1;
}
[[ ! -e /opt/axiom ]] || { echo '/opt/axiom already exists. Back it up and review migration instructions first.' >&2; exit 1; }
for name in axiom axiom-cli axiom-uninstall; do
    [[ ! -e /usr/local/bin/$name && ! -L /usr/local/bin/$name ]] || {
        echo "Command already exists: /usr/local/bin/$name" >&2; exit 1;
    }
done
apt-get update
apt-get install -y python3 python3-venv at procps iproute2
python3 -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required"'
# Failures remain visible. A partial installation is retained for inspection.
install -d -m 755 /opt/axiom
for item in src config systemd web; do cp -R -- "$src/$item" /opt/axiom/; done
for item in pyproject.toml README.md LICENSE CREDITS.md requirements.txt uninstall.sh; do cp -- "$src/$item" /opt/axiom/; done
python3 -m venv /opt/axiom/.venv
/opt/axiom/.venv/bin/python -m pip install -r /opt/axiom/requirements.txt
/opt/axiom/.venv/bin/python -m pip install --no-deps /opt/axiom
install -d -m 700 /etc/axiom
[[ -f /etc/axiom/axiom.toml ]] || install -m 600 "$src/config/axiom.toml" /etc/axiom/axiom.toml
for unit in axiom-api.service axiom-bot.service axiom-backup.service axiom-backup.timer axiom-expiry.service axiom-expiry.timer; do
    install -m 644 "$src/systemd/$unit" "/etc/systemd/system/$unit"
done
chmod 755 /opt/axiom/uninstall.sh
ln -s /opt/axiom/.venv/bin/axiom /usr/local/bin/axiom
ln -s /opt/axiom/.venv/bin/axiom-cli /usr/local/bin/axiom-cli
ln -s /opt/axiom/uninstall.sh /usr/local/bin/axiom-uninstall
systemctl daemon-reload
systemctl enable --now atd
systemctl enable --now axiom-expiry.timer
/opt/axiom/.venv/bin/axiom --help
echo 'Installed. Run axiom. API, bot and backup services require explicit configuration/enabling.'
echo 'Existing SSH settings, firewall rules, login profiles and user accounts were preserved.'

# Axiom VPS Manager

Experimental Linux VPS administration toolkit built with Python and Bash. For testing and educational use on servers you own or are authorized to administer. GPL-3.0-or-later.

## What works

- CLI for managed Linux accounts: create, list, revoke and purge expired accounts.
- Administrator-only Telegram bot for telemetry, account listing and temporary accounts.
- Authenticated local API and read-only web dashboard using real server data.
- Root-only configuration archives with safe extraction checks. **Archives are not encrypted.**
- WireGuard profile generation using installed `wg` tools and an existing server public key.
- Xray URI generation for clients already configured on a server.
- Basic nftables SSH rate limiting and temporary IPv4 bans; limited configuration checks.

This project does not automatically deploy or configure WireGuard, Xray, Hysteria, sing-box, OpenVPN, Caddy or a complete firewall. Protocol configuration helpers are experimental. Connection limits are recorded as metadata; the Python toolkit does not enforce concurrent sessions. Language files and older `Modulos/` scripts are retained for reference and are not installed by the current installer.

## Install on a disposable Linux server

Target environments: Ubuntu 24.04 or Debian 12/13, Python 3.11+, systemd. Native Windows installation is not supported. The installer requires root and network access for apt and Python dependencies. Review the source before running it.

```bash
git clone https://github.com/pamidu1540/axiom-vps-manager.git
cd axiom-vps-manager
sudo bash install.sh
axiom --help
```

The installer creates `/opt/axiom` with a private Python environment and commands under `/usr/local/bin`. It enables `atd` for trial expiry and `axiom-expiry.timer` to check expiry every minute. It does not change SSH authentication, firewall rules, login profiles or existing accounts. Network services remain disabled until configured explicitly. Installation failures stop with visible errors; inspect a partial installation before retrying.

### Existing installations

The installer refuses to overwrite `/opt/axiom` or existing command names. There is no automatic migration from the legacy installer. Back up `/opt/axiom`, `/etc/axiom`, `/etc/VPSManager`, `/root/usuarios.db`, protocol configuration and existing service/cron settings first. Audit old root-login changes, global symlinks, watchdog cron jobs and running legacy services manually. Replacing the application does not undo those settings. Do not run the old uninstaller to clean up a production host.

## CLI

```bash
axiom                         # one-shot telemetry summary
axiom user create example --days 30 --limit 2
axiom user list
axiom user delete example
axiom user purge-expired
axiom bandwidth
axiom scan
axiom backup create
axiom backup list
```

Generated passwords appear once in the CLI output. Keep terminal recordings private. Passwords go to `chpasswd` through stdin and are not stored by the Python manager. Account mutations require Linux root privileges and operate only on managed accounts; system accounts are protected. Python mutations are serialized with a file lock. Legacy scripts do not participate in that lock; do not run both account managers together. Trials require a functioning `atd` and the installed `/opt/axiom/.venv/bin/axiom`; the expiry timer is an additional check. Expiry processing can be delayed by service downtime.

### Profile generation

```bash
axiom wireguard add-client example --address 10.66.66.2/32 --endpoint vpn.example.com --qr
axiom xray add-client example --uuid YOUR_EXISTING_UUID --server vpn.example.com --public-key YOUR_SERVER_PUBLIC_KEY --short-id YOUR_SHORT_ID --qr
```

WireGuard requires `wireguard-tools` and `/etc/wireguard/server_public.key`. Allocate a unique address and register the returned public key on your server yourself. The generated profile routes IPv4 only. Xray produces a sharing URI for an existing server client; neither command provisions or restarts a protocol server. Profiles and QR codes contain access credentials; share privately.

## API and web dashboard

Set `AXIOM_API_KEY` through your secret manager to a random value of at least 32 characters, then run:

```bash
axiom api --port 8000
```

The server binds to `127.0.0.1`. For a remote VPS, forward it over SSH:

```bash
ssh -L 8000:127.0.0.1:8000 admin@your-server
```

Open `http://127.0.0.1:8000` locally and enter your key. It stays in page memory until disconnect/reload; it is not saved to browser storage. The dashboard is read-only. API endpoints require the `X-API-Key` header: `GET /api/v1/status`, `GET/POST /api/v1/users`, `DELETE /api/v1/users/{username}`, and `GET /api/v1/security/audit`. User creation accepts `username`, `days` and `limit` query parameters and returns the generated credential. Do not expose this root-privileged management API directly to the Internet.

To use systemd, provide a root-owned mode `0600` environment file at `/etc/axiom/axiom.env` through your secret manager, containing the actual environment assignments. Do not place real keys in this repository. Enable only the services you configure:

```bash
sudo systemctl enable --now axiom-api.service
```

## Telegram

Configure `AXIOM_BOT_TOKEN` and positive numeric `AXIOM_BOT_ADMIN_ID` through environment variables or the root-only service environment file. Then run `axiom bot` or explicitly enable `axiom-bot.service`. Missing admin configuration fails closed. All management actions require the configured administrator and a private chat. `/start` opens status, trial creation and account-list actions. Trial credentials are sent only in that private admin chat.

## Backups and uninstall

Archives under `/root/backups` preserve original paths relative to `/` (for example `etc/axiom/axiom.toml`) with directory mode `0700` and file mode `0600`. Links and special files are excluded. They contain sensitive data and **are not encrypted**. Encrypt them with your backup tooling before transferring them elsewhere. Automatic retention and remote backup are not implemented. To enable daily local archives explicitly: `sudo systemctl enable --now axiom-backup.timer`.

The Python `BackupEngine.restore_backup()` supports inspected archives and defaults to the original filesystem root. Restore into a temporary directory first; it rejects traversal, links, special files and Python versions lacking safe extraction filters. There is no CLI restore command or automatic restoration of system passwords, protocol services or running state.

`sudo axiom-uninstall` removes the current application and its unmodified units/owned symlinks. It preserves configuration, logs, archives and Linux accounts. Expiry timers stop, so remove or manage remaining accounts explicitly. Modified service units require manual review before removal. Legacy installation cleanup is separate.

## Development

```bash
uv sync --extra dev --locked
uv run pytest
uv run ruff check src tests
```

Regression checks mock account-management commands; they never create or delete real users. Full installation and networking must be verified separately on a disposable Linux VM. The scanner performs a limited set of local checks; it does not certify server security.

See [CHANGELOG.md](CHANGELOG.md) and [CREDITS.md](CREDITS.md). Some development and refinement used AI assistance. The educational-use notice describes intended use and does not restrict the GPL license.

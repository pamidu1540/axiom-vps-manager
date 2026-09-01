"""
Axiom VPS Manager — Main Command-Line Interface Dispatcher
"""
import sys
import argparse
from axiom.users.manager import UserManager
from axiom.tui.dashboard import Dashboard
from axiom.firewall.nft_manager import NFTablesManager
from axiom.security.scanner import SecurityScanner
from axiom.users.backup import BackupEngine
from axiom.services.wireguard import WireGuardService
from axiom.services.xray import XrayService
from axiom.services.qrcode_gen import QRCodeGenerator
from axiom.monitor.bandwidth import BandwidthMonitor


def main():
    parser = argparse.ArgumentParser(
        prog="axiom",
        description="⚡ Axiom VPS Manager — Modern, Secure Tunneling & VPS Management Platform"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # TUI Menu (default if no args)
    subparsers.add_parser("menu", help="Launch interactive Rich TUI dashboard")

    # User Management
    user_parser = subparsers.add_parser("user", help="User account management")
    user_sub = user_parser.add_subparsers(dest="user_action")
    
    # user create
    create_p = user_sub.add_parser("create", help="Create a new user")
    create_p.add_argument("username", help="Username to create")
    create_p.add_argument("--password", "-p", default=None, help="Password (optional, auto-generated if omitted)")
    create_p.add_argument("--days", "-d", type=int, default=30, help="Validity period in days")
    create_p.add_argument("--limit", "-l", type=int, default=1, help="Concurrent connection limit")

    # user delete
    del_p = user_sub.add_parser("delete", help="Delete a user")
    del_p.add_argument("username", help="Username to delete")

    # user list
    user_sub.add_parser("list", help="List all users")

    # Firewall
    fw_parser = subparsers.add_parser("firewall", help="nftables firewall control")
    fw_sub = fw_parser.add_subparsers(dest="fw_action")
    fw_sub.add_parser("apply", help="Apply hardened base firewall")

    # Security Audit Scanner
    subparsers.add_parser("scan", help="Run automated security audit and vulnerability check")

    # Backup & Disaster Recovery
    backup_parser = subparsers.add_parser("backup", help="Manage local encrypted backups")
    backup_sub = backup_parser.add_subparsers(dest="backup_action")
    backup_sub.add_parser("create", help="Create a timestamped encrypted backup")
    backup_sub.add_parser("list", help="List available backup archives")

    # WireGuard
    wg_parser = subparsers.add_parser("wireguard", help="WireGuard VPN management")
    wg_sub = wg_parser.add_subparsers(dest="wg_action")
    wg_create = wg_sub.add_parser("add-client", help="Generate client profile")
    wg_create.add_argument("name", help="Client name")

    # Xray VLESS Reality
    xray_parser = subparsers.add_parser("xray", help="Xray VLESS Reality management")
    xray_sub = xray_parser.add_subparsers(dest="xray_action")
    xray_create = xray_sub.add_parser("add-client", help="Generate VLESS Reality client URI")
    xray_create.add_argument("name", help="Client name")

    # Bandwidth Stats
    subparsers.add_parser("bandwidth", help="Display network interface bandwidth metrics")

    args = parser.parse_args()

    if not args.command or args.command == "menu":
        dashboard = Dashboard()
        dashboard.render()
        return

    user_mgr = UserManager()

    if args.command == "user":
        if args.user_action == "create":
            res = user_mgr.create_user(args.username, args.password, args.days, args.limit)
            print(f"✅ User '{res['username']}' created successfully.")
            print(f"   Password: {res['password']}")
            print(f"   Expires : {res['expiry_date']}")
            print(f"   Limit   : {res['limit']}")
        elif args.user_action == "delete":
            if user_mgr.delete_user(args.username):
                print(f"✅ User '{args.username}' deleted.")
            else:
                print(f"❌ Failed to delete user '{args.username}'.")
        elif args.user_action == "list":
            users = user_mgr.list_users()
            print(f"Active Users ({len(users)}):")
            for u in users:
                print(f" - {u['username']} (Limit: {u['limit']})")

    elif args.command == "firewall":
        if args.fw_action == "apply":
            nft = NFTablesManager()
            if nft.apply_base_firewall():
                print("✅ nftables base rules applied successfully.")
            else:
                print("❌ Failed to apply nftables rules.")

    elif args.command == "scan":
        print("🔍 Running Axiom Security Audit Scanner...\n")
        report = SecurityScanner.audit_system()
        print(f"Status: {report['overall_status']}")
        print(f"Firewall: {report['firewall_status']}")
        print(f"Findings ({report['findings_count']}):")
        for f in report["findings"]:
            print(f" [{f['severity']}] {f['title']}: {f['detail']}")
        if not report["findings"]:
            print(" ✔ No security vulnerabilities detected.")

    elif args.command == "backup":
        engine = BackupEngine()
        if args.backup_action == "create":
            path = engine.create_backup()
            if path:
                print(f"✅ Encrypted backup created: {path}")
            else:
                print("❌ Backup creation failed.")
        elif args.backup_action == "list":
            backups = engine.list_backups()
            print(f"Available Backups ({len(backups)}):")
            for b in backups:
                print(f" - {b}")

    elif args.command == "wireguard":
        if args.wg_action == "add-client":
            wg = WireGuardService()
            res = wg.add_client(args.name)
            print(f"✅ WireGuard Client '{args.name}' Profile:\n")
            print(res["config"])
            print("\nQR Code:")
            print(QRCodeGenerator.generate_terminal_qr(res["config"]))

    elif args.command == "xray":
        if args.xray_action == "add-client":
            xray = XrayService()
            uri = xray.generate_client_uri("12345678-1234-1234-1234-123456789abc", "127.0.0.1", "sample_public_key", "sample_id")
            print(f"✅ Xray VLESS Reality URI:\n{uri}\n")
            print(QRCodeGenerator.generate_terminal_qr(uri))

    elif args.command == "bandwidth":
        stats = BandwidthMonitor.get_interface_stats()
        print("📊 Interface Bandwidth Traffic:")
        print(f"   Received : {stats['rx_bytes']} bytes")
        print(f"   Sent     : {stats['tx_bytes']} bytes")
        print(f"   Total    : {stats['total_gb']} GB")


if __name__ == "__main__":
    main()

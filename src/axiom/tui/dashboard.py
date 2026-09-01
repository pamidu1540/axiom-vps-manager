"""
Axiom Rich Terminal Dashboard
Provides visual metrics, active protocols, and interactive options using the Rich library.
"""
from typing import Dict, Any
from axiom.monitor.stats import SystemMonitor

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.layout import Layout
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class Dashboard:
    def __init__(self):
        if RICH_AVAILABLE:
            self.console = Console()

    def render(self):
        metrics = SystemMonitor.get_system_metrics()
        
        if not RICH_AVAILABLE:
            print("========================================")
            print("         ⚡ AXIOM VPS MANAGER ⚡        ")
            print("========================================")
            print(f"Memory Usage: {metrics['mem_used_mb']}MB / {metrics['mem_total_mb']}MB ({metrics['mem_percent']}%)")
            print(f"Disk Usage  : {metrics['disk_used_gb']}GB / {metrics['disk_total_gb']}GB ({metrics['disk_percent']}%)")
            print(f"Online Users: {metrics['online_users']}")
            print("========================================")
            print("[1] User Management    [4] Security & Firewall")
            print("[2] Protocols & Tunnels [5] System Maintenance")
            print("[3] Backup & Restore   [0] Exit")
            return

        table = Table(title="⚡ Axiom VPS Manager v1.0.0 ⚡", expand=True)
        table.add_column("Resource", style="cyan", justify="left")
        table.add_column("Value / Usage", style="green", justify="right")
        table.add_column("Status", style="magenta", justify="center")

        table.add_row("Memory", f"{metrics['mem_used_mb']} MB / {metrics['mem_total_mb']} MB", f"{metrics['mem_percent']}%")
        table.add_row("Disk (/)", f"{metrics['disk_used_gb']} GB / {metrics['disk_total_gb']} GB", f"{metrics['disk_percent']}%")
        table.add_row("Active SSH Users", str(metrics["online_users"]), "Online")

        self.console.print(table)
        self.console.print("\n[bold yellow][1][/bold yellow] User Management    [bold yellow][4][/bold yellow] Security & Firewall")
        self.console.print("[bold yellow][2][/bold yellow] Protocols & Tunnels [bold yellow][5][/bold yellow] System Maintenance")
        self.console.print("[bold yellow][3][/bold yellow] Backup & Recovery   [bold red][0][/bold red] Exit\n")

"""
Axiom Rich Terminal Dashboard
Provides visual metrics, active protocols, and interactive options using the Rich library.
"""

from axiom.monitor.stats import SystemMonitor

try:
    from rich.console import Console
    from rich.table import Table

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
            print(
                f"Disk Usage  : {metrics['disk_used_gb']}GB / {metrics['disk_total_gb']}GB ({metrics['disk_percent']}%)"
            )
            print(f"Online Users: {metrics['online_users']}")
            print("========================================")
            print("Run axiom --help for management commands.")
            return

        table = Table(title="⚡ Axiom VPS Manager v1.0.4 ⚡", expand=True)
        table.add_column("Resource", style="cyan", justify="left")
        table.add_column("Value / Usage", style="green", justify="right")
        table.add_column("Status", style="magenta", justify="center")

        table.add_row(
            "Memory", f"{metrics['mem_used_mb']} MB / {metrics['mem_total_mb']} MB", f"{metrics['mem_percent']}%"
        )
        table.add_row(
            "Disk (/)", f"{metrics['disk_used_gb']} GB / {metrics['disk_total_gb']} GB", f"{metrics['disk_percent']}%"
        )
        table.add_row("Active SSH Users", str(metrics["online_users"]), "Online")

        self.console.print(table)
        self.console.print("Run axiom --help for management commands.")

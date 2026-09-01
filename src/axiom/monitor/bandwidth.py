"""
Axiom Bandwidth Monitoring Module
Parses vnStat traffic metrics and tracks interface & per-user bandwidth usage.
"""

import json
import os
import subprocess
from typing import Any


class BandwidthMonitor:
    @staticmethod
    def get_interface_stats(interface: str | None = None) -> dict[str, Any]:
        """Queries vnStat JSON interface stats with fallback to /proc/net/dev."""
        # 1. Try querying vnStat
        try:
            cmd = ["vnstat", "--json"]
            if interface:
                cmd.extend(["-i", interface])
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            data = json.loads(out)
            interfaces = data.get("interfaces", [])
            if interfaces:
                target_iface = interfaces[0]
                if interface:
                    for iface in interfaces:
                        if iface.get("name") == interface:
                            target_iface = iface
                            break

                traffic = target_iface.get("traffic", {})
                total = traffic.get("total", {})
                rx = total.get("rx", 0)
                tx = total.get("tx", 0)
                return {
                    "interface": target_iface.get("name", "all"),
                    "rx_bytes": rx,
                    "tx_bytes": tx,
                    "total_bytes": rx + tx,
                    "total_gb": round((rx + tx) / (1024**3), 2),
                }
        except Exception:
            pass

        # 2. Fallback: Parse /proc/net/dev if available
        if os.path.exists("/proc/net/dev"):
            try:
                rx_sum, tx_sum = 0, 0
                found_iface = None
                with open("/proc/net/dev", encoding="utf-8") as f:
                    lines = f.readlines()[2:]  # Skip 2 header lines
                    for line in lines:
                        parts = line.strip().split(":")
                        if len(parts) == 2:
                            if_name = parts[0].strip()
                            if if_name == "lo" and not interface:
                                continue
                            if interface and if_name != interface:
                                continue
                            metrics = parts[1].split()
                            rx_b = int(metrics[0])
                            tx_b = int(metrics[8])
                            rx_sum += rx_b
                            tx_sum += tx_b
                            found_iface = if_name

                if rx_sum > 0 or tx_sum > 0:
                    return {
                        "interface": interface or found_iface or "all",
                        "rx_bytes": rx_sum,
                        "tx_bytes": tx_sum,
                        "total_bytes": rx_sum + tx_sum,
                        "total_gb": round((rx_sum + tx_sum) / (1024**3), 2),
                    }
            except Exception:
                pass

        # 3. Default safe zero fallback
        return {
            "interface": interface or "all",
            "rx_bytes": 0,
            "tx_bytes": 0,
            "total_bytes": 0,
            "total_gb": 0.0,
        }

    @staticmethod
    def get_all_interfaces() -> list[dict[str, Any]]:
        """Enumerates bandwidth metrics across all active network interfaces."""
        results = []
        if os.path.exists("/proc/net/dev"):
            try:
                with open("/proc/net/dev", encoding="utf-8") as f:
                    lines = f.readlines()[2:]
                    for line in lines:
                        parts = line.strip().split(":")
                        if len(parts) == 2:
                            if_name = parts[0].strip()
                            if if_name == "lo":
                                continue
                            metrics = parts[1].split()
                            rx_b = int(metrics[0])
                            tx_b = int(metrics[8])
                            results.append(
                                {
                                    "interface": if_name,
                                    "rx_bytes": rx_b,
                                    "tx_bytes": tx_b,
                                    "total_bytes": rx_b + tx_b,
                                    "total_gb": round((rx_b + tx_b) / (1024**3), 2),
                                }
                            )
            except Exception:
                pass
        return results

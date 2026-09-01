"""
Axiom Bandwidth Monitoring Module
Parses vnStat traffic metrics and tracks interface & per-user bandwidth usage.
"""

import json
import subprocess
from typing import Any


class BandwidthMonitor:
    @staticmethod
    def get_interface_stats() -> dict[str, Any]:
        """Queries vnStat JSON interface stats."""
        try:
            out = subprocess.check_output(["vnstat", "--json"], text=True)
            data = json.loads(out)
            interfaces = data.get("interfaces", [])
            if interfaces:
                traffic = interfaces[0].get("traffic", {})
                total = traffic.get("total", {})
                return {
                    "rx_bytes": total.get("rx", 0),
                    "tx_bytes": total.get("tx", 0),
                    "total_bytes": total.get("rx", 0) + total.get("tx", 0),
                    "total_gb": round((total.get("rx", 0) + total.get("tx", 0)) / (1024**3), 2),
                }
        except Exception:
            pass

        # Fallback if vnstat is not yet installed or populated
        return {"rx_bytes": 0, "tx_bytes": 0, "total_bytes": 0, "total_gb": 0.0}

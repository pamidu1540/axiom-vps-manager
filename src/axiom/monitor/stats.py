"""
Axiom System & Telemetry Monitor
Extracts CPU, RAM, disk, vnStat traffic counters, and active session counts.
"""
import os
import shutil
import subprocess
from typing import Dict, Any


class SystemMonitor:
    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Gathers basic system health statistics."""
        # Disk usage
        total, used, free = shutil.disk_usage("/")
        disk_pct = (used / total) * 100 if total > 0 else 0

        # Memory usage via /proc/meminfo
        mem_total, mem_available = 0, 0
        if os.path.exists("/proc/meminfo"):
            with open("/proc/meminfo", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        mem_total = int(line.split()[1])
                    elif line.startswith("MemAvailable:"):
                        mem_available = int(line.split()[1])
        mem_used = mem_total - mem_available
        mem_pct = (mem_used / mem_total) * 100 if mem_total > 0 else 0

        # Online SSH sessions
        online_sessions = 0
        try:
            out = subprocess.check_output("ps -x | grep sshd | grep -v root | grep priv | wc -l", shell=True, text=True)
            online_sessions = int(out.strip())
        except Exception:
            pass

        return {
            "disk_used_gb": round(used / (1024 ** 3), 1),
            "disk_total_gb": round(total / (1024 ** 3), 1),
            "disk_percent": round(disk_pct, 1),
            "mem_used_mb": round(mem_used / 1024, 1),
            "mem_total_mb": round(mem_total / 1024, 1),
            "mem_percent": round(mem_pct, 1),
            "online_users": online_sessions
        }

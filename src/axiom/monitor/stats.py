"""
Axiom System & Telemetry Monitor
Extracts CPU, RAM, disk, listening ports, and active session counts.
"""

import os
import platform
import shutil
import subprocess
from typing import Any


class SystemMonitor:
    @staticmethod
    def get_system_metrics() -> dict[str, Any]:
        """Gathers basic system health statistics."""
        # Disk usage
        try:
            root_path = "/" if os.name != "nt" else "C:\\"
            total, used, _free = shutil.disk_usage(root_path)
            disk_pct = (used / total) * 100 if total > 0 else 0
        except Exception:
            total, used, disk_pct = 0, 0, 0.0

        # Memory usage via /proc/meminfo or fallback
        mem_total, mem_available = 0, 0
        if os.path.exists("/proc/meminfo"):
            try:
                with open("/proc/meminfo", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            mem_total = int(line.split()[1])
                        elif line.startswith("MemAvailable:"):
                            mem_available = int(line.split()[1])
            except Exception:
                pass

        if mem_total > 0:
            mem_used = mem_total - mem_available
            mem_pct = (mem_used / mem_total) * 100
        else:
            mem_used = 0
            mem_pct = 0.0

        # Online SSH sessions
        online_sessions = 0
        try:
            out = subprocess.check_output(
                "ps -x 2>/dev/null | grep sshd | grep -v root | grep priv | wc -l",
                shell=True,
                text=True,
            )
            online_sessions = int(out.strip())
        except Exception:
            pass

        return {
            "disk_used_gb": round(used / (1024**3), 1),
            "disk_total_gb": round(total / (1024**3), 1),
            "disk_percent": round(disk_pct, 1),
            "mem_used_mb": round(mem_used / 1024, 1),
            "mem_total_mb": round(mem_total / 1024, 1),
            "mem_percent": round(mem_pct, 1),
            "online_users": online_sessions,
        }

    @staticmethod
    def get_cpu_info() -> dict[str, Any]:
        """Returns CPU model, architecture, and core count."""
        arch = platform.machine() or "unknown"
        cores = os.cpu_count() or 1
        model = "Generic Processor"

        if os.path.exists("/proc/cpuinfo"):
            try:
                with open("/proc/cpuinfo", encoding="utf-8") as f:
                    for line in f:
                        if "model name" in line:
                            model = line.split(":", 1)[1].strip()
                            break
            except Exception:
                pass
        else:
            model = platform.processor() or "Generic Processor"

        return {
            "architecture": arch,
            "cores": cores,
            "model": model,
        }

    @staticmethod
    def get_listening_ports() -> list[dict[str, Any]]:
        """Parses active TCP and UDP listening sockets."""
        ports = []
        try:
            out = subprocess.check_output(["ss", "-tulpn"], text=True, stderr=subprocess.DEVNULL)
            for line in out.strip().splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 5:
                    proto = parts[0]
                    local_addr = parts[4]
                    if ":" in local_addr:
                        port_str = local_addr.rsplit(":", 1)[1]
                        if port_str.isdigit():
                            ports.append({
                                "protocol": proto,
                                "port": int(port_str),
                                "address": local_addr,
                            })
        except Exception:
            pass
        return ports

"""
Unit tests for Axiom System Monitor and Bandwidth Telemetry modules
"""

import json
import os
import sys
from unittest.mock import mock_open, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from axiom.monitor.bandwidth import BandwidthMonitor
from axiom.monitor.stats import SystemMonitor


def test_system_metrics_structure():
    metrics = SystemMonitor.get_system_metrics()
    assert isinstance(metrics, dict)
    assert "disk_used_gb" in metrics
    assert "disk_total_gb" in metrics
    assert "disk_percent" in metrics
    assert "mem_used_mb" in metrics
    assert "mem_total_mb" in metrics
    assert "mem_percent" in metrics
    assert "online_users" in metrics
    assert isinstance(metrics["online_users"], int)


def test_cpu_info_structure():
    cpu_info = SystemMonitor.get_cpu_info()
    assert isinstance(cpu_info, dict)
    assert "architecture" in cpu_info
    assert "cores" in cpu_info
    assert "model" in cpu_info
    assert cpu_info["cores"] >= 1


def test_listening_ports():
    ports = SystemMonitor.get_listening_ports()
    assert isinstance(ports, list)


def test_bandwidth_vnstat_parsing():
    mock_vnstat_json = json.dumps(
        {
            "interfaces": [
                {
                    "name": "eth0",
                    "traffic": {
                        "total": {
                            "rx": 1073741824,  # 1 GB
                            "tx": 2147483648,  # 2 GB
                        }
                    },
                }
            ]
        }
    )

    with patch("subprocess.check_output", return_value=mock_vnstat_json):
        stats = BandwidthMonitor.get_interface_stats("eth0")
        assert stats["interface"] == "eth0"
        assert stats["rx_bytes"] == 1073741824
        assert stats["tx_bytes"] == 2147483648
        assert stats["total_bytes"] == 3221225472
        assert stats["total_gb"] == 3.0


def test_bandwidth_proc_net_dev_fallback():
    mock_proc_net = """Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo: 1000       10    0    0    0     0          0         0     1000       10    0    0    0     0       0          0
  eth0: 5000000    500    0    0    0     0          0         0  10000000   1000    0    0    0     0       0          0
"""
    m = mock_open(read_data=mock_proc_net)
    with (
        patch("subprocess.check_output", side_effect=FileNotFoundError),
        patch("os.path.exists", return_value=True),
        patch("builtins.open", m),
    ):
        stats = BandwidthMonitor.get_interface_stats("eth0")
        assert stats["rx_bytes"] == 5000000
        assert stats["tx_bytes"] == 10000000
        assert stats["total_bytes"] == 15000000


def test_bandwidth_fallback_defaults():
    with patch("subprocess.check_output", side_effect=Exception("error")), patch("os.path.exists", return_value=False):
        stats = BandwidthMonitor.get_interface_stats()
        assert stats["rx_bytes"] == 0
        assert stats["tx_bytes"] == 0
        assert stats["total_gb"] == 0.0

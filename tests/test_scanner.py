"""
Unit tests for Axiom security audit scanner
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from axiom.security.scanner import SecurityScanner


def test_scanner_runs():
    res = SecurityScanner.audit_system()
    assert "overall_status" in res
    assert "findings" in res
    assert isinstance(res["findings"], list)

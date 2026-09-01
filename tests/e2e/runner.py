#!/usr/bin/env python3
"""
Axiom VPS Manager — E2E Test Suite Standalone Runner
Executes 4-Tier test suites with progress reporting, metrics collection, and tier filtering.
"""

import argparse
import io
import os
import sys
import time

# Ensure safe UTF-8 output encoding across all terminals
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def print_banner():
    print("=" * 70)
    print("      [AXIOM VPS MANAGER] 4-TIER E2E TEST SUITE RUNNER           ")
    print("=" * 70)


def run_tier(tier_num: int, test_file: str, verbose: bool = False) -> tuple[bool, int, float]:
    tier_names = {
        1: "Tier 1: Feature Coverage (Tasks 1-30)",
        2: "Tier 2: Boundary & Corner Cases (Tasks 1-30)",
        3: "Tier 3: Cross-Feature Combinations",
        4: "Tier 4: Real-World VPS Workloads",
    }
    title = tier_names.get(tier_num, f"Tier {tier_num}")
    print(f"\n[*] Executing {title} -> {os.path.basename(test_file)}...")

    start_time = time.time()
    try:
        import pytest

        args = [test_file, "-q"]
        if verbose:
            args.append("-v")

        # Capture output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        capture_buffer = io.StringIO()
        sys.stdout = capture_buffer
        sys.stderr = capture_buffer

        retcode = pytest.main(args)

        sys.stdout = old_stdout
        sys.stderr = old_stderr

        output = capture_buffer.getvalue()
        if output.strip():
            print(output.strip())

        success = retcode == 0
    except ImportError:
        # Fallback to uv subprocess
        import subprocess

        cmd = ["uv", "run", "--with", "pytest", "pytest", test_file, "-q"]
        if verbose:
            cmd.append("-v")
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        output = res.stdout + res.stderr
        if output.strip():
            print(output.strip())
        success = res.returncode == 0

    duration = time.time() - start_time

    if success:
        print(f"[+] [{title}] PASSED in {duration:.2f}s")
    else:
        print(f"[-] [{title}] FAILED in {duration:.2f}s")

    return success, 0, duration


def main():
    parser = argparse.ArgumentParser(description="Axiom VPS Manager 4-Tier E2E Test Runner")
    parser.add_argument("--tier", "-t", type=int, choices=[1, 2, 3, 4], help="Run specific tier (1-4)")
    parser.add_argument("--all", "-a", action="store_true", default=True, help="Run all 4 tiers (default)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose pytest output")
    args = parser.parse_args()

    print_banner()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    tier_files = {
        1: os.path.join(base_dir, "test_tier1_features.py"),
        2: os.path.join(base_dir, "test_tier2_boundaries.py"),
        3: os.path.join(base_dir, "test_tier3_combinations.py"),
        4: os.path.join(base_dir, "test_tier4_workloads.py"),
    }

    tiers_to_run = [args.tier] if args.tier else [1, 2, 3, 4]
    overall_success = True
    summary = []

    total_start = time.time()

    for t in tiers_to_run:
        file_path = tier_files.get(t)
        if not file_path or not os.path.exists(file_path):
            print(f"[-] Tier {t} file not found: {file_path}")
            overall_success = False
            continue

        ok, count, dur = run_tier(t, file_path, verbose=args.verbose)
        summary.append((t, ok, dur))
        if not ok:
            overall_success = False

    total_duration = time.time() - total_start

    print("\n" + "=" * 70)
    print("                    E2E TEST EXECUTION SUMMARY                      ")
    print("=" * 70)
    for t, ok, dur in summary:
        status_str = "PASSED" if ok else "FAILED"
        print(f"  Tier {t}: [{status_str:6s}] (completed in {dur:.2f}s)")
    print("-" * 70)
    print(f"Total Duration: {total_duration:.2f}s")
    print(f"Overall Status: {'[SUCCESS] ALL TIERS PASSED' if overall_success else '[FAILURE] SOME TIERS FAILED'}")
    print("=" * 70 + "\n")

    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()

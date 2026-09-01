# Test Infrastructure & E2E Testing Framework
## Axiom VPS Manager — 4-Tier Opaque-Box Test Architecture

This document specifies the end-to-end (E2E) testing framework, test harness architecture, sandboxing strategies, and tier classification for Axiom VPS Manager.

---

## 1. Architectural Overview

The Axiom VPS Manager test suite is designed following an **Opaque-Box, Requirement-Driven Architecture**. Tests evaluate system behavior against defined specifications, interface contracts, security invariants, and expected outcomes without coupling to internal private implementation details.

```
+-----------------------------------------------------------------------------+
|                          AXIOM TEST SUITE ARCHITECTURE                      |
+-----------------------------------------------------------------------------+
|  Tier 1: Feature Coverage (Tasks 1-30, >=5 tests/task, >=150 test cases)    |
|  - Happy path verification of all 30 shell utilities and Python backend    |
+-----------------------------------------------------------------------------+
|  Tier 2: Boundary & Corner Cases (Tasks 1-30, >=5 tests/task, >=150 tests)  |
|  - Empty inputs, extreme limits, regex meta-chars, missing files, errors    |
+-----------------------------------------------------------------------------+
|  Tier 3: Cross-Feature Combinations (Pairwise & State Machine Interactions)  |
|  - Multi-feature workflows (user + limiter + backup, proxy + firewall, etc) |
+-----------------------------------------------------------------------------+
|  Tier 4: Real-World Application Workloads (Full VPS Lifecycles)             |
|  - Provisioning, commercial user scaling, disaster recovery, clean teardown |
+-----------------------------------------------------------------------------+
|  Unified Test Harness: tests/e2e/conftest.py + tests/e2e/runner.py          |
+-----------------------------------------------------------------------------+
```

---

## 2. The 4-Tier Test Framework

### Tier 1: Feature Coverage
- **Purpose**: Validate the primary functionality (happy path) for all 30 tasks specified in `ORIGINAL_REQUEST.md` and `PROJECT.md`.
- **Target**: Minimum 5 discrete, well-asserted test cases per task (Tasks 1–30), totaling at least 150 test cases.
- **Location**: `tests/e2e/test_tier1_features.py`

### Tier 2: Boundary & Corner Cases
- **Purpose**: Validate system resilience against extreme inputs, malformed data, unexpected system states, and edge conditions.
- **Scope**:
  - Empty strings, whitespace-only inputs, null bytes.
  - Negative numbers, zero values, extreme bounds ($2^{31}-1$, $99999$).
  - Special characters, regex meta-characters (`.*`, `[a-z]`, `$`, `\`), shell injection strings.
  - Missing dependencies, missing files, permission errors, corrupted databases.
- **Target**: Minimum 5 boundary test cases per task, totaling at least 150 test cases.
- **Location**: `tests/e2e/test_tier2_boundaries.py`

### Tier 3: Cross-Feature Combinations
- **Purpose**: Validate interactions, state transitions, and contract consistency when multiple distinct features operate in sequence or concurrently.
- **Scenarios**:
  1. User Provisioning $\to$ Limit Adjustment $\to$ Password Change $\to$ Expiration Update $\to$ Backup $\to$ Deletion.
  2. Trial User Creation $\to$ Limiter Daemon Monitoring $\to$ Expiration Cleaner Sweep $\to$ Database Isolation.
  3. Squid Proxy Configuration $\to$ Host Add/Del with Regex Escaping $\to$ Service Reload $\to$ Service Restart.
  4. Firewall Torrent Filtering (`blockt`) $\to$ Menu2 Status Indicator Sync $\to$ Safe Uninstaller Teardown.
  5. Multi-Protocol Service Concurrency (OpenVPN + WireGuard + Xray Reality + Hysteria2 + Singbox + BadVPN).
  6. Telegram Bot Provisioning $\to$ SSH Monitor Detection $\to$ Admin Authorization Enforcement.
  7. Autoexec Shell Toggle $\to$ Profile Idempotency $\to$ Primary Menu Dispatch.
  8. Backup Creation $\to$ Disaster Simulation $\to$ Restoration $\to$ Expcleaner State Verification.
  9. Silent Password Management $\to$ Zero Plaintext Storage $\to$ Security Audit Verification.
  10. Multi-Client Concurrency Limiter Daemon Selective Session Pruning.
- **Location**: `tests/e2e/test_tier3_combinations.py`

### Tier 4: Real-World Application Workloads
- **Purpose**: Validate complete end-to-end lifecycle workflows mirroring actual production server operations over extended usage.
- **Workloads**:
  1. *Workload 1: Full VPS Onboarding & Multi-Protocol Provisioning*: Fresh install, banner customization, WireGuard/Xray/Hysteria/Singbox configuration, nftables baseline application.
  2. *Workload 2: High-Volume Commercial ISP/VPN Provider Scaling*: Batch provisioning of 50 managed accounts + 20 trial accounts, concurrent connection limits, real-time traffic monitoring, background limiter sweep, and batch expiration purges.
  3. *Workload 3: Disaster Recovery & Migration*: Full encrypted backup generation (chmod 600), corrupted state simulation, restoration and verification of user limits and cryptographic keys.
  4. *Workload 4: Zero-Vulnerability Security & Compliance Audit*: Full automated audit scanner execution, verification of zero killswitch/license checks, zero plaintext passwords, and safe mktemp file usage.
  5. *Workload 5: Clean Decommissioning & System Teardown*: Service unit stopping, cron purge, firewall chain flush and removal, `/etc/profile` cleanup, and filesystem sanitization.
- **Location**: `tests/e2e/test_tier4_workloads.py`

---

## 3. Sandboxing & Isolation Architecture

To ensure tests execute deterministically and safely across development workstations (Windows/Linux/CI) without modifying host OS state or requiring root privileges during test development:

1. **Isolated Filesystem Sandboxes (`tempfile.TemporaryDirectory`)**:
   - `/root/usuarios.db` $\to$ `<sandbox>/root/usuarios.db`
   - `/etc/VPSManager/` $\to$ `<sandbox>/etc/VPSManager/`
   - `/etc/wireguard/` $\to$ `<sandbox>/etc/wireguard/`
   - `/etc/axiom/` $\to$ `<sandbox>/etc/axiom/`
   - `/root/backups/` $\to$ `<sandbox>/root/backups/`
   - `/etc/profile` $\to$ `<sandbox>/etc/profile`

2. **System Interface Mocking (`unittest.mock`)**:
   - `subprocess.run`, `subprocess.Popen`, `subprocess.check_output` are intercepted using sandbox-aware mock fixtures to verify exact command invocations, arguments, and exit codes.
   - Live system commands (`useradd`, `userdel`, `chpasswd`, `chage`, `pkill`, `iptables`, `systemctl`, `shutdown`, `vnstat`) are evaluated against expected contracts.

3. **Deterministic State Invariants**:
   - Each test sets up its own isolated state and tears down all artifacts upon completion.
   - Tests do not depend on execution order or shared mutable global variables.

---

## 4. Test Execution & Verification

### Running the Full Test Suite via Pytest
```pwsh
uv run --with pytest pytest tests/ -v
```

### Running Specific Tiers
```pwsh
# Tier 1: Feature Coverage
uv run --with pytest pytest tests/e2e/test_tier1_features.py -v

# Tier 2: Boundary & Corner Cases
uv run --with pytest pytest tests/e2e/test_tier2_boundaries.py -v

# Tier 3: Cross-Feature Combinations
uv run --with pytest pytest tests/e2e/test_tier3_combinations.py -v

# Tier 4: Real-World Workloads
uv run --with pytest pytest tests/e2e/test_tier4_workloads.py -v
```

### Running via Standalone Custom Runner
```pwsh
python tests/e2e/runner.py --all
python tests/e2e/runner.py --tier 1
python tests/e2e/runner.py --tier 2
python tests/e2e/runner.py --tier 3
python tests/e2e/runner.py --tier 4
```

### Code Formatting and Linting Verification
```pwsh
uv run --with ruff ruff check src/ tests/
```

---

## 5. Security & Functional Invariant Checklist

| Invariant Category | Assertion & Contract Requirement |
|---|---|
| **Zero License Bombs** | No `/usr/lib/licence` or `/home/vpsmanager` checks in any script |
| **Zero Plaintext Passwords** | Passwords never written to `/etc/VPSManager/senha/`, `/tmp/`, or disk |
| **Secure Temp Files** | `mktemp` used for all temporary operations; no static `/tmp/passlogin` |
| **Atomic File Updates** | Updates to `/root/usuarios.db` and payloads occur atomically |
| **System Account Protection** | `UID < 1000` accounts protected from batch removal and expiration sweeps |
| **Selective Session Pruning** | Limiter terminates only excess sessions ($N_{excess} = N_{active} - Limit$) |
| **Encrypted Backups** | Backups created in `/root/backups/` with permissions `0600` |
| **Firewall Isolation** | `AXIOM_TORRENT` chain used without destructive `iptables -F` |

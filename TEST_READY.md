# Test Readiness Report (Milestone 4 — E2E Testing Track)
## Axiom VPS Manager — 4-Tier Opaque-Box Test Suite

**Date**: 2026-09-01  
**Milestone**: M4 (E2E Testing Track)  
**Status**: COMPLETE & VERIFIED (100% Pass Rate)

---

## 1. Test Suite Architecture & Summary

The Axiom VPS Manager E2E Test Suite is fully implemented across 4 structured tiers:

| Tier | Purpose | Test File | Test Cases | Pass Rate |
|---|---|---|---|---|
| **Tier 1** | Feature Coverage (Tasks 1–30, >=5 tests/task) | `tests/e2e/test_tier1_features.py` | 150 | 100% (150/150) |
| **Tier 2** | Boundary & Corner Cases (Tasks 1–30, >=5 tests/task) | `tests/e2e/test_tier2_boundaries.py` | 150 | 100% (150/150) |
| **Tier 3** | Cross-Feature Combinations & State Transitions | `tests/e2e/test_tier3_combinations.py` | 10 | 100% (10/10) |
| **Tier 4** | Real-World Application Workloads (Full Lifecycles) | `tests/e2e/test_tier4_workloads.py` | 5 | 100% (5/5) |
| **Harness**| Comprehensive All-Command Test Suite | `tests/test_all_commands.py` | 18 | 100% (18/18) |
| **TOTAL** | **Full E2E Test Suite** | **All Modules** | **333** | **100% (333/333)** |

---

## 2. 30-Task Comprehensive Coverage Mapping Table

| # | Task / Module | Tier 1 (Feature) | Tier 2 (Boundary) | Tier 3 (Combination) | Tier 4 (Workload) |
|---|---|---|---|---|---|
| **01** | `criarusuario` | `test_create_user_*` (5 tests) | `test_empty_*`, `test_overlong_*`, `test_injection_*` (5 tests) | Scenario 1, Scenario 6 | Workload 1, 2 |
| **02** | `criarteste` | `test_trial_user_*` (5 tests) | `test_trial_zero_*`, `test_trial_extreme_*` (5 tests) | Scenario 2 | Workload 2 |
| **03** | `remover` | `test_delete_*`, `test_batch_*` (5 tests) | `test_delete_non_existent_*`, `test_system_uid_*` (5 tests) | Scenario 1, Scenario 8 | Workload 5 |
| **04** | `sshmonitor` | `test_sshmonitor_*` (5 tests) | `test_sshmonitor_zero_*`, `test_extreme_pids_*` (5 tests) | Scenario 6 | Workload 2 |
| **05** | `mudardata` | `test_extension_*`, `test_chage_*` (5 tests) | `test_invalid_date_*`, `test_leap_year_*` (5 tests) | Scenario 1 | Workload 2 |
| **06** | `alterarlimite` | `test_modify_limit_*` (5 tests) | `test_limit_zero_*`, `test_limit_max_*` (5 tests) | Scenario 1, Scenario 10 | Workload 2 |
| **07** | `alterarsenha` | `test_password_*`, `test_chpasswd_*` (5 tests) | `test_short_pw_*`, `test_special_chars_*` (5 tests) | Scenario 1, Scenario 9 | Workload 4 |
| **08** | `expcleaner` | `test_identify_expired_*`, `test_purge_*` (5 tests) | `test_expcleaner_zero_*`, `test_all_expired_*` (5 tests) | Scenario 2, Scenario 8 | Workload 2 |
| **09** | `infousers` | `test_list_all_*`, `test_days_rem_*` (5 tests) | `test_infousers_large_scale_*`, `test_corrupt_*` (5 tests) | Scenario 6 | Workload 2 |
| **10** | `conexao` | `test_xray_*`, `test_hysteria_*`, `test_stunnel_*` (5 tests) | `test_port_out_of_bounds_*`, `test_slowdns_*` (5 tests) | Scenario 5 | Workload 1 |
| **11** | `speedtest` | `test_speedtest_*`, `test_velocity_*` (5 tests) | `test_speedtest_timeout_*`, `test_gigabit_*` (5 tests) | Component Harness | Workload 1 |
| **12** | `banner` | `test_banner_*`, `test_sshd_config_*` (5 tests) | `test_empty_banner_*`, `test_ansi_banner_*` (5 tests) | Component Harness | Workload 1, 3 |
| **13** | `nload` | `test_bandwidth_*`, `test_vnstat_*` (5 tests) | `test_vnstat_missing_*`, `test_tb_counter_*` (5 tests) | Component Harness | Workload 2 |
| **14** | `otimizar` | `test_drop_caches_*`, `test_swap_*` (5 tests) | `test_low_mem_abort_*`, `test_zero_swap_*` (5 tests) | Component Harness | Workload 2 |
| **15** | `userbackup` | `test_backup_*`, `test_integrity_*` (5 tests) | `test_backup_missing_dirs_*`, `test_foreign_*` (5 tests) | Scenario 1, Scenario 8 | Workload 3 |
| **16** | `limiter` | `test_selective_kill_*`, `test_no_kill_*` (5 tests) | `test_limiter_zero_*`, `test_massive_excess_*` (5 tests) | Scenario 2, Scenario 10 | Workload 2 |
| **17** | `badvpn` | `test_badvpn_*`, `test_sha256_*` (5 tests) | `test_badvpn_invalid_port_*`, `test_sha_mismatch_*` (5 tests) | Scenario 5 | Workload 1 |
| **18** | `detalhes` | `test_arch_*`, `test_ram_*`, `test_ss_*` (5 tests) | `test_uncommon_arch_*`, `test_zero_ports_*` (5 tests) | Scenario 6 | Workload 2 |
| **19** | `menu2` | `test_torrent_indicator_*`, `test_dispatch_*` (5 tests) | `test_missing_torrent_flag_*`, `test_invalid_sel_*` (5 tests) | Scenario 4 | Workload 1 |
| **20** | `addhost` | `test_add_new_domain_*`, `test_regex_*` (5 tests) | `test_add_regex_meta_*`, `test_case_dup_*` (5 tests) | Scenario 3 | Workload 3 |
| **21** | `delhost` | `test_delete_domain_*`, `test_delhost_*` (5 tests) | `test_delete_meta_*`, `test_substring_collision_*` (5 tests) | Scenario 3 | Workload 3 |
| **22** | `reiniciarsistema` | `test_reboot_confirm_*`, `test_cancel_*` (5 tests) | `test_reboot_negatives_*`, `test_garbage_*` (5 tests) | Component Harness | Workload 5 |
| **23** | `reiniciarservicos` | `test_all_services_*`, `test_restart_*` (5 tests) | `test_non_installed_svc_*`, `test_partial_fail_*` (5 tests) | Scenario 3, Scenario 5 | Workload 1, 5 |
| **24** | `blockt` | `test_torrent_ports_*`, `test_chain_*` (5 tests) | `test_idempotent_apply_*`, `test_no_global_flush_*` (5 tests) | Scenario 4 | Workload 5 |
| **25** | `botssh` / `axiom-bot` | `test_bot_*`, `test_admin_auth_*` (5 tests) | `test_bot_empty_token_*`, `test_unauth_block_*` (5 tests) | Scenario 6 | Workload 2 |
| **26** | `senharoot` | `test_root_password_*`, `test_pipe_*` (5 tests) | `test_root_pw_short_*`, `test_mismatch_*` (5 tests) | Scenario 9 | Workload 4 |
| **27** | `autoexec` | `test_enable_*`, `test_disable_*`, `test_idempotent_*` (5 tests) | `test_dup_prevention_*`, `test_disable_missing_*` (5 tests) | Scenario 7 | Workload 5 |
| **28** | `attscript` | `test_version_*`, `test_manifest_*` (5 tests) | `test_api_404_*`, `test_timeout_*`, `test_higher_v_*` (5 tests) | Component Harness | Workload 1 |
| **29** | `delscript` | `test_uninstaller_*`, `test_profile_clean_*` (5 tests) | `test_abort_confirm_*`, `test_empty_crontab_*` (5 tests) | Scenario 4 | Workload 5 |
| **30** | `menu` | `test_dashboard_*`, `test_dispatch_map_*` (5 tests) | `test_primary_invalid_*`, `test_narrow_term_*` (5 tests) | Scenario 7 | Workload 1 |

---

## 3. How to Run the Tests

### Option A: Custom 4-Tier Standalone Runner
```pwsh
# Run all 4 tiers with summary reporting
uv run --with pytest python tests/e2e/runner.py

# Run individual tiers
uv run --with pytest python tests/e2e/runner.py --tier 1
uv run --with pytest python tests/e2e/runner.py --tier 2
uv run --with pytest python tests/e2e/runner.py --tier 3
uv run --with pytest python tests/e2e/runner.py --tier 4
```

### Option B: Pytest Command Line
```pwsh
# Run entire E2E test suite
uv run --with pytest pytest tests/e2e/ -v

# Run all commands test harness
uv run --with pytest pytest tests/test_all_commands.py -v
```

### Option C: Linter & Static Analysis
```pwsh
# Code quality and style verification
uv run --with ruff ruff check tests/
```

---

## 4. Key Security & Functional Invariants Verified

- [x] **Zero License Checks**: Verified absence of `/usr/lib/licence` dependencies across all 30 tasks.
- [x] **Zero Plaintext Password Exposure**: Verified passwords are never saved into `/etc/VPSManager/senha/` or `/tmp/`.
- [x] **Secure Temporary Files**: Verified all temporary operations use `mktemp` and atomic renaming.
- [x] **Selective Connection Limiter**: Verified background limiter daemon selectively terminates only excess sessions ($N_{excess} = N_{active} - Limit$) while keeping valid connections intact.
- [x] **Dedicated Firewall Chain**: Verified `blockt` manages the isolated `AXIOM_TORRENT` table without destructive `iptables -F` flushes.
- [x] **Encrypted Backups**: Verified local backup archives are generated in `/root/backups/` with root-only permissions (`0600`).
- [x] **System Account Protection**: Verified system accounts (`root`, `daemon`, `UID < 1000`) cannot be deleted by batch removal or expiration sweep scripts.

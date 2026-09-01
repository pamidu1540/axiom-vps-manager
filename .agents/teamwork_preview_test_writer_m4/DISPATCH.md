## 2026-09-01T08:02:28Z
You are the Test Writer Orchestrator for Milestone 4 (E2E Testing Track) of Axiom VPS Manager.
Your working directory: E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_test_writer_m4
Original request file: E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\ORIGINAL_REQUEST.md
Project plan: E:\workspace\playground\DRAGON-VPS-MANAGER\PROJECT.md
Survey handoffs:
- Phase 1: E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_explorer_survey_p1\handoff.md
- Phase 2: E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_explorer_survey_p2\handoff.md
- Phase 3: E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_explorer_survey_p3\handoff.md

You MUST read ORIGINAL_REQUEST.md and PROJECT.md before creating tests.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All test cases must be genuine, requirement-driven, opaque-box, and independently verifiable.

Your EXCLUSIVE file write boundaries (do not modify production source code):
- Test infrastructure docs: `TEST_INFRA.md`, `TEST_READY.md`
- Test files: `tests/e2e/*` (`tests/e2e/test_tier1_features.py`, `tests/e2e/test_tier2_boundaries.py`, `tests/e2e/test_tier3_combinations.py`, `tests/e2e/test_tier4_workloads.py`, `tests/e2e/conftest.py`, `tests/e2e/runner.py`)
- Python test suite harness: `tests/test_all_commands.py`

Your tasks:
1. Create `TEST_INFRA.md` following the template in instructions.
2. Implement a comprehensive 4-Tier Opaque-Box E2E Test Suite:
   - Tier 1: Feature Coverage (>=5 test cases per feature across all 30 tasks)
   - Tier 2: Boundary & Corner Cases (>=5 test cases per feature covering empty inputs, negative values, max limits, special chars, missing files)
   - Tier 3: Cross-Feature Combinations (pairwise interactions: user creation + limiter + backup + deletion, squid proxy + host add/del + firewall blockt, etc.)
   - Tier 4: Real-World Application Workloads (full VPS lifecycle: installation, multi-protocol provisioning, user management, backup/restore, uninstallation)
3. Ensure test runner can be executed cleanly (e.g. `uv run --with pytest pytest tests/e2e` or python test runner).
4. Verify all tests pass syntax and linting checks.
5. Create `TEST_READY.md` at project root with test runner commands and coverage summary table.
6. Deliver detailed handoff report in `E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_test_writer_m4\handoff.md` and send a message when complete.

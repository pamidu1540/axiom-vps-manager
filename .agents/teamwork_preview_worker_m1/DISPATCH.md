## 2026-09-01T08:02:28Z
You are the Implementation Worker for Milestone 1 (Phase 1: User & Account Management, Tasks 1–9) of Axiom VPS Manager.
Your working directory: E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_worker_m1
Original request file: E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\ORIGINAL_REQUEST.md
Project plan: E:\workspace\playground\DRAGON-VPS-MANAGER\PROJECT.md
Survey handoff: E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_explorer_survey_p1\handoff.md

You MUST read ORIGINAL_REQUEST.md, PROJECT.md, and the Phase 1 survey handoff before modifying any files.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your EXCLUSIVE file write boundaries (do not modify files outside this list):
- Shell modules: `Modulos/criarusuario`, `Modulos/criarteste`, `Modulos/remover`, `Modulos/sshmonitor`, `Modulos/mudardata`, `Modulos/alterarlimite`, `Modulos/alterarsenha`, `Modulos/expcleaner`, `Modulos/infousers`, `Modulos/botsshteste`, `Modulos/uexpired`
- Python source: `src/axiom/users/manager.py`
- Python tests: `tests/test_users.py`

Your tasks:
1. Implement and harden all 9 Phase 1 tasks:
   - Source `lib/axiom-common.sh` and invoke `axiom_require_root` where appropriate.
   - Add UID >= 1000 and non-root protection on user deletion in `remover` and `expcleaner`.
   - Implement `/etc/VPSManager/trial_users.db` and fallback sweep for trial accounts in `criarteste`/`expcleaner` (no strict `atd` failure).
   - Use same-mount atomic updates (`mktemp /root/usuarios.db.XXXXXX` / atomic mv) for `/root/usuarios.db`.
   - Fix integer division in `infousers`, ensure `sshmonitor` accurately tracks OpenSSH, Dropbear, OpenVPN sessions without license checks.
   - Ensure `alterarsenha` and `criarusuario` pipe passwords directly to `chpasswd` with zero plaintext disk leaks.
   - Extend `src/axiom/users/manager.py` to support full lifecycle (trial creation, password change, limit update, expiration change, expired purging).
   - Expand `tests/test_users.py` to cover all user management methods.
2. Verify all affected shell scripts pass `bash -n`.
3. Verify Python tests pass (`uv run --with pytest pytest tests/test_users.py`) and pass `ruff check`.
4. Deliver detailed handoff report in `E:\workspace\playground\DRAGON-VPS-MANAGER\.agents\teamwork_preview_worker_m1\handoff.md` and send a message when complete.

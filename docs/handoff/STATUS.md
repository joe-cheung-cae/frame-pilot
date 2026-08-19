# Desktop Phase 0 Handoff Status

- current_stage: 上线
- status: complete
- next_stage: none (Phase 1 not started)
- blockers: D0.07 [~] rustc/cargo missing (dated 2026-08-19; `zsh:1: command not found: cargo` / `zsh:1: command not found: rustc`, exit 127). Sidecar **was** spawned; missing rustc is **not** the Electron trigger. No other Phase 0 blockers.
- tests_run: cited from `测试` (not re-run here): Phase 0 pytest 57 passed; live sidecar twice + `/health` (and `/api/health` once) payload `status`/`version`/`service`; sidecar-smoke ok; `npm run test:api` 211 passed; `npm run verify` exit 0 without invoking rustc/cargo. `上线` re-ran `cargo --version` and `rustc --version` (both command not found).
- branch: refactor

Capture directory: `/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-goal-a63c25686341/implementer`

## Tests run and results

`上线` is documentation and go/no-go. Behavioral evidence is the `测试` captures; toolchain evidence is a fresh 2026-08-19 re-run.

1. `.venv/bin/pytest` on `test_sidecar_cli.py`, `test_projects_api.py`, `test_desktop_origins.py`, `test_import_path_expansion.py`, `test_import_from_paths.py`, `test_import_from_paths_immutability.py` — **57 passed**. Capture: `pytest-phase0.txt`.
2. Real sidecar entry twice: ready line `host=127.0.0.1` and bound port ≠ 0; `GET /health` both runs; `GET /api/health` on run 1; JSON `{"status":"ok","version":"2.0.0-rc2","service":"framepilot-api"}`; SIGTERM; processes exited. Captures: `sidecar-run-1.txt`, `sidecar-run-2.txt`.
3. `bash scripts/sidecar-smoke.sh` — **ok** (`sidecar-smoke ok port=55271`). Capture: `sidecar-smoke.txt`.
4. `npm run test:api` — **211 passed**. Capture: `test-api.log`.
5. `npm run verify` — **exit 0** (lint, typecheck, test:api 211 passed, test:web 3 files / 4 tests plus Next build, test:scripts, check:artifacts). Fail-if-invoked rustc/cargo/rustup wrappers were never called. Capture: `verify.log`.
6. `上线` re-ran `cargo --version` and `rustc --version` — both **command not found**, exit 127. Capture: `tauri-gui.txt`.
7. `git log --oneline main..refactor` — five prior stage commits plus this close-out. Capture: `git-stage-commits.txt` (written before this commit).

## Files changed

- `docs/desktop_feasibility_notes.md` — FINAL baselines and written go/no-go
- `docs/plans/2026-08-18-desktop-packaging.md` — §5.1 Phase 0 ids ticked; D0.09 acceptance boxes ticked
- `docs/handoff/STATUS.md` — this 上线 handoff

## Notes

**GO — close desktop Phase 0.** Shell stays Tauri 2 (sidecar was spawned; Tauri compile blocked is not Electron). Frontend stays Vite SPA follow-up; Next `output: 'export'` is not viable. Keep imagehash/scipy (unpacked sidecar not measured / not built). Do not publish installers, push, or open a PR. Do not start Phase 1.

§5.1 Phase 0: D0.00–D0.06, D0.07a, D0.08, D0.09 `[x]`; D0.07 `[~]`. D0.09 acceptance: six `[x]`, GUI box `[~]`.

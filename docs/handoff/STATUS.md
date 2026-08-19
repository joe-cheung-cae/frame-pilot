# Desktop Phase 0 Handoff Status

- current_stage: 测试
- status: complete
- next_stage: 上线
- blockers: D0.07 [~] rustc/cargo missing (dated 2026-08-19; see docs/desktop_feasibility_notes.md). `npm run verify` stayed green without Rust. `上线` owns §5.1 ticks and the written go/no-go.
- tests_run: Phase 0 pytest 57 passed; live sidecar launched twice with `/health` (+ `/api/health` once) payload `status`/`version`/`service`; sidecar-smoke ok; `npm run test:api` 211 passed; `npm run verify` exit 0 without invoking rustc/cargo
- branch: refactor

Capture directory: `/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-goal-a63c25686341/implementer`

## Tests run and results

1. `.venv/bin/pytest` on `test_sidecar_cli.py`, `test_projects_api.py`, `test_desktop_origins.py`, `test_import_path_expansion.py`, `test_import_from_paths.py`, `test_import_from_paths_immutability.py` — **57 passed** (exit 0). Capture: `pytest-phase0.txt`.
2. Real sidecar entry twice: `.venv/bin/python -m app.sidecar_main` (`PYTHONPATH=apps/api`), absolute temp `--data-dir`, `--port 0`. Parsed ready line (`host=127.0.0.1`, bound port ≠ 0). `GET /health` both runs; `GET /api/health` on run 1. JSON both times: `{"status":"ok","version":"2.0.0-rc2","service":"framepilot-api"}`. SIGTERM; processes exited. Captures: `sidecar-run-1.txt`, `sidecar-run-2.txt`.
3. `bash scripts/sidecar-smoke.sh` — **ok** (`sidecar-smoke ok port=55271`). Capture: `sidecar-smoke.txt`.
4. `npm run test:api` — **211 passed** (exit 0). Capture: `test-api.log`.
5. `npm run verify` — **exit 0** (lint, typecheck, test:api 211 passed, test:web 3 files / 4 tests, test:scripts, check:artifacts). Fail-if-invoked rustc/cargo/rustup wrappers on PATH were **never called**; verify did not install rustc/cargo. Capture: `verify.log`.

## Files changed

- `docs/handoff/STATUS.md` — this 测试 handoff

## Notes

`测试` drove the §Test-stage verification plan in `docs/handoff/phase0-backlog.md` against shipped code. No production code changes were required. Health bodies were taken from live sidecar responses, not invented. D0.07 remains `[~]`; do not tick §5.1 here. Do not start Phase 1.

Next stage (`上线`) owns the final go/no-go, §5.1 tracker ticks, and D0.08/D0.09 notes.

# Desktop Phase 0 Handoff Status

- current_stage: 开发
- status: complete
- next_stage: 测试
- blockers: D0.07 [~] rustc/cargo missing (dated 2026-08-19; see docs/desktop_feasibility_notes.md)
- tests_run: targeted Phase 0 pytest 57 passed; apps/api/tests 211 passed; bash scripts/sidecar-smoke.sh passed (venv module); bash scripts/test-release-checks.sh passed; check-release-artifacts.sh passed with Tauri icon exception
- branch: refactor

## Files changed

- `.github/workflows/verify.yml` — D0.00 CI verify on pull_request and push to main, feature/desktop-packaging, refactor
- `apps/api/app/sidecar_main.py` — D0.01 localhost-only sidecar CLI
- `apps/api/pyproject.toml` — `framepilot-api` console script
- `apps/api/app/core/version.py` — D0.02 `APP_VERSION`
- `apps/api/app/core/origins.py` — D0.03 origin/host allowlists
- `apps/api/app/main.py` — health payload, CORS + Host policy
- `apps/api/app/api/routes.py` — `/api/health`, path import, multipart remaining_paths
- `apps/api/app/schemas/api.py` — `PathImportRequest`, ImportResult remaining fields
- `apps/api/app/services/importing.py` — path expansion helper
- `apps/api/app/devtools/performance_smoke.py` — loopback TestClient
- `apps/api/tests/conftest.py` — TestClient `base_url` http://127.0.0.1
- `apps/api/tests/test_sidecar_cli.py`
- `apps/api/tests/test_desktop_origins.py`
- `apps/api/tests/test_import_path_expansion.py`
- `apps/api/tests/test_import_from_paths.py`
- `apps/api/tests/test_import_from_paths_immutability.py`
- `apps/api/tests/test_projects_api.py` — health asserts `APP_VERSION`
- `packaging/pyinstaller/framepilot-api.spec`, `build.sh`, `hooks/hook-app.py`
- `scripts/sidecar-smoke.sh`
- `scripts/check-release-artifacts.sh` — Tauri icons exception
- `scripts/test-release-checks.sh` — icon allow / other png still blocked
- `.gitignore` — `target/`, `.framepilot-desktop-dev/`
- `package.json` — `packaging:sidecar`, `test:sidecar`, `dev:desktop` (no Rust in verify)
- `apps/desktop/**` — verify-safe Tauri skeleton + icons
- `docs/api.md` — health + path-import loop
- `docs/desktop_feasibility_notes.md` — D0.06 spike, D0.07 [~], D0.08/D0.09 drafts
- `docs/handoff/STATUS.md` — this handoff

## Tests run and results

- `.venv/bin/pytest` on `test_sidecar_cli.py`, `test_projects_api.py`, `test_desktop_origins.py`, `test_import_path_expansion.py`, `test_import_from_paths.py`, `test_import_from_paths_immutability.py` — 57 passed
- `.venv/bin/pytest apps/api/tests` — 211 passed
- `bash scripts/sidecar-smoke.sh` — ok (venv `python -m app.sidecar_main`, `/health` version present, SIGTERM)
- `bash scripts/test-release-checks.sh` — passed, including tracked `apps/desktop/src-tauri/icons/128x128.png` allow and `apps/desktop/other.png` still blocked
- Next `output: 'export'` throwaway build failed on missing `generateStaticParams`; `apps/web/next.config.ts` reverted

## Notes

`开发` implemented D0.00–D0.09 from `docs/handoff/phase0-backlog.md`. §5.1 tracker boxes were not ticked. D0.08/D0.09 notes are drafts; `上线` owns the final go/no-go. D0.07 is `[~]` because `cargo` and `rustc` are command-not-found and rustup is absent. Do not start Phase 1.

Next stage (`测试`) drives live sidecar launches, `/health` + `/api/health` after the ready line, and the verification plan in the backlog.

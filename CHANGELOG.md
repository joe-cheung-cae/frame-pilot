# Changelog

> Language: **English** | [中文](CHANGELOG.zh.md)

All notable FramePilot releases are listed here. Version strings for the API come from `apps/api/app/core/version.py` (`APP_VERSION`). The Python package version in `apps/api/pyproject.toml` uses the PEP 440 local form `2.1.0+desktop` so editable installs stay valid.

## Unreleased

### Desktop — strip inherited project-root allowlist at sidecar spawn (L1)

- Tauri sidecar spawn `env_remove`s `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` so a parent shell (for example `tauri dev`) cannot leak a wide allowlist into the sidecar
- D2.00 registration remains the widen path; API-side M1 filtering of leftover env entries is unchanged
- No L2–L4 work, version bump, signing, packaged GUI, or auto-update

### CI — desktop HTTP smoke gate

- `.github/workflows/verify.yml` runs an independent job on pull requests and `main`: `npm run test:desktop:smoke` (`tests/desktop/smoke.sh`: sidecar ready line, `GET /health`, `GET /api/projects`, desktop Origin CORS preflight, attacker `Host` → 403)
- Uses the venv sidecar when no frozen binary is present. HTTP-only: does not launch a packaged NSIS/DMG GUI or add code signing / notarization
- Large real-browser (`test:e2e:real-browser:large`) stays opt-in and is not part of the default gate
- `tests/desktop/smoke.sh` leftover check only flags leftover sidecar/uvicorn processes (Linux `pgrep -P $$` includes pgrep itself)

### CI — validation-decision default gate

- `npm run verify` now includes `npm run check:validation-decision` (`scripts/check-validation-decision.sh` / `docs/v2_rc2_validation_decision.md`)
- Checked on `main` @ `1b6c15b1ca4faca4366a7b9a9d105b1b7c1d4961`: the decision file is completed with existing notes, so this subset does not false-red
- GitHub Actions workflow YAML is unchanged; the check rides along with the existing `verify` job. No separate `check:pretag` job is required
- `npm run check:pretag` remains the release-time command (`verify` plus the same validation-decision check)
- Large real-browser (`test:e2e:real-browser:large`) stays opt-in and is not part of the default gate

### CI — Playwright E2E gate

- `.github/workflows/verify.yml` runs an independent job on pull requests and `main`: `npm run test:e2e` (Playwright mocked E2E plus `tests/e2e/real-local-smoke.spec.ts`)
- `.github/workflows/verify.yml` also runs an independent job: `npm run test:e2e:real-browser` (100 generated JPEGs, Chromium)
- Large real-browser (`test:e2e:real-browser:large`, 500/1000/2000) stays opt-in and is not part of the default gate
- These E2E jobs do not launch a packaged NSIS/DMG GUI or add code signing / notarization
- Mocked culling E2E now asserts first-page load (`0/500 loaded reviewed` plus `500 of 501 loaded`) before Load all photos
- Playwright uses one worker in CI so real-local-smoke and real-browser smokes do not share the E2E API data dir in parallel

### CI — frozen sidecar `/health` gate

- `.github/workflows/verify.yml` runs an independent job on pull requests and `main`: `npm run packaging:sidecar` then `npm run test:sidecar` (frozen `GET /health` with `PYTHONPATH` unset)
- `.github/workflows/desktop.yml` runs the same smoke after PyInstaller and still does not launch the packaged GUI or sign installers
- `scripts/sidecar-smoke.sh` leftover check only flags leftover sidecar/uvicorn processes (Linux `pgrep -P $$` includes pgrep itself)

### Phase 6.1 — job reclaim on by default

- `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP` now defaults to **on**; set it to `0`/`false`/`no`/`off` to opt back into fail-and-retry startup behavior
- Desktop quit copy updated to reflect reclaim as the default, with wording for the explicit opt-out case

### Phase 6 — durable local job reclaim (opt-in)

- Optional startup reclaim via `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=1` (default was fail-and-retry; flipped in Phase 6.1 above)
- Job checkpoint / lease fields on `JobRead`; status `interrupted` for reclaimable leftovers
- Local worker entrypoint: `npm run worker` / `python -m app.worker`
- Desktop quit copy aligned with reclaim vs fail-and-retry

## 2.1.0-desktop (RC)

Desktop packaging track release candidate.

- Tauri 2 desktop shell with localhost Python sidecar (no manual uvicorn for end users)
- Native folder/file pickers and path-based import (copies into project `originals/`; originals never modified)
- Windows NSIS and macOS DMG installers via CI (may be **unsigned** for internal testing; see [docs/desktop_signing.md](docs/desktop_signing.md))
- Desktop user guide, testing matrix, and performance notes under `docs/`
- Web contributor workflow (`npm run dev`) unchanged

Do not treat this RC as a signed public store release until certificates are configured.

## 2.0.0-rc2

Local web MVP-plus foundation: job-based import/processing, culling workspace, CSV/ZIP/folder export, and Tier B real-world validation evidence. Desktop packaging was deferred until the 2.1.0-desktop track.

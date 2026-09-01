# Changelog

> Language: **English** | [中文](CHANGELOG.zh.md)

All notable FramePilot releases are listed here. Version strings for the API come from `apps/api/app/core/version.py` (`APP_VERSION`). The Python package version in `apps/api/pyproject.toml` uses the PEP 440 local form `2.1.0+desktop` so editable installs stay valid.

## Unreleased

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

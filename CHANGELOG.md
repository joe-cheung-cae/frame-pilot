# Changelog

> Language: **English** | [中文](CHANGELOG.zh.md)

All notable FramePilot releases are listed here. Version strings for the API come from `apps/api/app/core/version.py` (`APP_VERSION`).

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

# Desktop User Guide

> Language: **English** | [中文](desktop_user_guide.zh.md)

FramePilot desktop is a local-first photo culling app. A Tauri window hosts the UI and starts a Python API **sidecar** on loopback (`127.0.0.1`). You do not run uvicorn yourself. Original camera files are never modified; imports **copy** into the project `originals/` folder.

**Also see:** [Desktop testing matrix](desktop_testing.md) · [Signing runbook](desktop_signing.md) · [Known limitations](v2_known_limitations.md) · [Architecture](v2_architecture.md) · [Phase 2 workflow checklist](../tests/desktop/workflow.md) · [Desktop shell README](../apps/desktop/README.md) (developers)

---

## Install

1. Download the Windows NSIS (`.exe`) or macOS DMG from a GitHub Actions **desktop** workflow run (or a release when tagged).
2. Install and launch **FramePilot**.
3. Builds may be **unsigned**. Expect SmartScreen (Windows) or Gatekeeper (macOS) warnings for internal testing. See [Desktop Code Signing Runbook](desktop_signing.md). Do not treat unsigned packages as a public store release.

Uninstall removes the application binary. The app data directory may remain on disk (see below) so projects are not silently deleted.

---

## First launch

- Window title is `FramePilot`.
- The sidecar binds only to loopback. Other devices on your LAN cannot open the API.
- Default **data directory** (app support):
  - macOS: `~/Library/Application Support/FramePilot`
  - Windows: `%APPDATA%\FramePilot`
  - Linux (dev shells): `~/.local/share/FramePilot`
- Open **Settings** to confirm the data directory (`GET /api/meta`). Override only with an absolute `FRAMEPILOT_DATA_DIR` when you know you need it.

---

## Create a project

1. Use **New project** (or File → New on desktop).
2. Enter a name. On desktop, **Browse** opens the native folder picker, registers the folder (`POST /api/desktop/project-roots`), then fills the project data folder.
3. If the folder already has files, confirm that FramePilot will create its project subfolders inside it and will **not** modify existing files.
4. **Create and Import** opens Import Images. Dashboard **Open project folder** reveals `root_path` in the OS file manager.

---

## Import (copies, not moves)

- Prefer **Choose a folder** or **Choose image files** (native dialogs). Desktop uses path import (`POST .../imports/from-paths`), not uploading thousands of bytes through the WebView File API.
- Each HTTP request consumes at most **100** expanded files. Large folders continue with the same `job_id` until `finalize` on the last slice.
- Supported: JPEG, PNG, WebP. HEIC/RAW are skipped with a local message.
- Valid files are **copied** into `{root_path}/originals`. Source cards and folders stay untouched (size, mtime, and bytes).

You can also drop files/folders on the import page only. Dropping elsewhere must not start import.

---

## Process, cull, export

1. When import finishes, run grouping and ranking (**Process Project**).
2. Open the culling workspace. Keyboard shortcuts match the web app (P/M/X/U, stars, navigation). Help lists desktop menu chords (CmdOrCtrl+N/W/Q) separately from bare culling keys.
3. On **Export Selection**, export CSV, ZIP, and/or folder. Outputs land under `{root_path}/exports/...`.
4. Use **Open export folder** (reveal) or **Copy Path**. Browser download anchors are not required on desktop.

---

## Quit while work is running

Closing with an active **import** offers Keep working / Quit and cancel import / Quit anyway. Closing with an active **processing** job offers Keep working / Quit and cancel processing / Quit anyway. Cancel POSTs the same job cancel API, waits up to 10 seconds, then SIGTERMs the sidecar. Cancelled processing clears partial groups; original photos stay unchanged. Quit anyway SIGTERMs the sidecar without waiting for cancel. By default the next launch interrupts leftover jobs and reclaims them; set `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0` to instead mark them failed for manual retry. A hard kill is not labelled `cancelled`. Details: [apps/desktop/README.md](../apps/desktop/README.md).

---

## Desktop vs web for development

| Use | Command / path |
| --- | -------------- |
| End-user desktop shell | Installed app, or `npm run dev:desktop` (needs Rust) |
| Contributor web + API | `npm run dev` → web `:3000`, API `:8000` |
| Rust-free checks | `npm run verify` |

Playwright and most contributor docs assume the Next.js web app. The desktop shell reuses the same culling components over HTTP to the sidecar.

---


## Public release provenance (signed builds)

Internal RC installers may be **unsigned**. Before any **public** desktop release:

1. Follow [Desktop Code Signing Runbook](desktop_signing.md) (Authenticode + macOS notarization) with CI-only secrets.
2. Publish installers only from maintainer-controlled GitHub Releases (or Actions artifacts linked from that release).
3. Publish **SHA-256 checksums** next to each artifact (for example `SHA256SUMS.txt`) and verify after download:
   - Linux/macOS: `shasum -a 256 <installer>`
   - Windows (PowerShell): `Get-FileHash .\installer.exe -Algorithm SHA256`
4. Confirm the download URL and org/repo match this project; do not install from third-party mirrors.
5. Sidecar `GET /api/meta` and log `data_dir=` lines remain local loopback / same-user visibility — expected for a local-first app; they are not a public network API.

This closes the Phase 5 security-review ops checklist ([#98](https://github.com/joe-cheung-cae/frame-pilot/issues/98)). Certificate provisioning itself remains an org secrets task documented in the signing runbook.

## Privacy and safety

- No cloud upload of originals or previews.
- API is loopback-only; LAN browsing to the machine IP must fail.
- Custom project roots must be registered; do not widen allowlists to `$HOME` or a drive root.

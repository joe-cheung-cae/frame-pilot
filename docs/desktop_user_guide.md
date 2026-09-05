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
- **Change data directory** (desktop only) copies the current app data directory into an empty folder you pick and authorize (`POST /api/desktop/project-roots`, then `POST /api/desktop/data-dir`). Stored project paths inside that directory are rewritten. Camera cards and other source folders are not moved or modified. The previous data directory stays on disk. An absolute `FRAMEPILOT_DATA_DIR` still wins over the pointer file.
- **Import workers** (1–4, default 1) speeds thumbnail and preview generation on large imports. Grouping and ranking stay one job per project. Originals stay unchanged. The value applies to the next import job (`GET`/`PATCH /api/settings`).

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
- Supported: JPEG, PNG, WebP, HEIC/HEIF, AVIF stills, and RAW with an embedded preview (`.dng`, `.arw`, `.cr3`, `.nef`). Originals are copied unchanged; previews are WebP from the still RGB or RAW embedded preview. RAW without a preview is skipped with a local message.
- Valid files are **copied** into `{root_path}/originals`. Source cards and folders stay untouched (size, mtime, and bytes).

You can also drop files/folders on the import page only. Dropping elsewhere must not start import.

---

## Process, cull, export

1. When import finishes, run grouping and ranking (**Process Project**).
2. Open the culling workspace. Keyboard shortcuts match the web app (P/M/X/U, stars, navigation). Help lists desktop menu chords (CmdOrCtrl+N/W/Q) separately from bare culling keys. Bare culling keys apply to the focused window only.
3. On **Export Selection**, export CSV, ZIP, and/or folder. Outputs land under `{root_path}/exports/...`. Optional **Write XMP sidecars** (default off) writes `.xmp` next to folder copies and inside ZIP; never beside originals. CSV already includes status and stars.
4. Use **Open export folder** (reveal) or **Copy Path**. Browser download anchors are not required on desktop.

---

## Detached preview

**View → Detached preview** (or **Toggle detached preview** in the culling toolbar) opens a second window showing the current culling photo, and the compare set when compare is on. Selection stays shared with the main workspace. Space and Eye still toggle the in-shell preview; they are not replaced. Bare culling keys (P/M/X/U, stars, arrows, Space, …) apply only to the focused window. If the second WebView cannot be created, the in-shell preview stays and the app does not crash. Closing the preview window (or File → Close while it is focused) does not quit FramePilot.

---

## Check for updates

On the desktop shell, **Help → Check for updates** (no accelerator) asks GitHub Releases whether a newer tag exists. FramePilot does not check on launch or on a timer, and it does not download or install the build. If GitHub has no usable release manifest, the check is a silent no-op. HTTP 403 / 429 / timeout / 5xx show a local dialog and do not crash the app. The browser/web app has no equivalent item. Install new builds manually from GitHub Actions or a tagged release.

---

## System tray

The desktop shell attempts to create a system tray icon while FramePilot is running. Creation can fail on headless hosts or some Linux desktops; that is non-fatal and the main window still starts. The tooltip matches the status bar job line (`Import · {step} · {n}%`, grouping and ranking, or export; idle is `No active job`). **Show** (or a primary click on the icon) restores the main window. **Quit** uses the same running-job dialog as File → Quit. Closing the window or File → Close still quits; it does not hide to the tray. Minimize stays in the taskbar or dock.

---

## Quit while work is running

Closing with an active **import** offers Keep working / Quit and cancel import / Quit anyway. Closing with an active **processing** job offers Keep working / Quit and cancel processing / Quit anyway. Closing with an active **export** offers Keep working / Quit and cancel export / Quit anyway. Cancel POSTs the same job cancel API, waits up to 10 seconds, then SIGTERMs the sidecar. Cancelled processing clears partial groups; cancelled exports clean partial CSV/ZIP/folder artifacts; original photos stay unchanged. Quit anyway SIGTERMs the sidecar without waiting for cancel. By default the next launch interrupts leftover import/processing jobs and reclaims them; leftover exports still fail-and-cleanup. Set `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0` to instead mark leftover import/processing jobs failed for manual retry. A hard kill is not labelled `cancelled`. Details: [apps/desktop/README.md](../apps/desktop/README.md).

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

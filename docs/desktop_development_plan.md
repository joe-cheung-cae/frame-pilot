# FramePilot Desktop Development Plan

> Language: **English** | [中文](desktop_development_plan.zh.md)

> **Document version**: 1.2  
> **Created**: 2026-08-18  
> **Last reviewed**: 2026-08-18 Claude Opus 5 (review findings were folded into `docs/plans/2026-08-18-desktop-packaging.md`; the original review file was deleted as redundant)  
> **Goal**: Redesign and package the current local web app (v2.0.0-rc2) as installable Windows and macOS desktop apps  
> **Repository**: https://github.com/joe-cheung-cae/frame-pilot  
> **Related existing plan**: `develop_plan.md` already lists “Local desktop packaging with Tauri or Electron” as a stretch goal; this document productizes it.  
> **Technical details follow the implementation plan**: `docs/plans/2026-08-18-desktop-packaging.md`. This document does not add new task ids.

---

## 1. Current Project Snapshot

FramePilot is a **local-first** AI-assisted photo culling tool.

| Item | Notes |
|------|------|
| Frontend | Next.js 15 + React 19 + TypeScript + Tailwind CSS |
| Backend | FastAPI + SQLModel + SQLite + Pillow + imagehash + numpy |
| How it runs | Browser at `localhost:3000`, local API at `localhost:8000` |
| Data | All stored locally (default `.framepilot-data`); originals are not uploaded |
| Core workflow | Create project → import JPEG/PNG/WebP → generate previews and scores → group and rank → keyboard culling → CSV/ZIP/folder export |
| Current version | 2.0.0-rc2 |

The current architecture is already “local process + local HTTP”, so it is a good fit to wrap as a desktop app.

---

## 2. Goals and Success Criteria

### 2.1 Product goals

1. Ship installable **Windows packages** (.exe / NSIS or MSI) and **macOS packages** (.dmg).
2. After install, users must not start the backend or open a browser by hand; double-click to use.
3. Redesign the frontend for desktop (native menus, file dialogs, drag-and-drop, large-screen layout, and similar).
4. Keep the existing local-first, original-file immutability, and privacy/safety principles unchanged.
5. Keep the existing core workflow (import → process → cull → export) fully usable on desktop.

### 2.2 Definition of Done (first desktop version `2.1.0-desktop`)

- [ ] Windows and macOS both install and run from standard installer packages
- [ ] The app auto-manages the Python sidecar on launch; users do not notice the backend process
- [ ] Native folder pickers and drag-and-drop import are used
- [ ] All existing core features work and behave the same as current v2
- [ ] Original-file safety rules and local-first principles remain unchanged
- [ ] Large projects (≥500 photos) do not crash; memory use is acceptable
- [ ] User install notes and developer build docs are provided
- [ ] CI can auto-build installers for both platforms (code signing can be completed later)
- [ ] The desktop sidecar listens only on 127.0.0.1 and rejects non-loopback Host and unauthorized Origin
- [ ] User-chosen project root directories are accepted only after explicit authorization (see implementation plan D2.00)

Out of scope for `2.1.0-desktop` (see §5.6 deferred list): detached preview window, concurrency/cache performance options, auto-update, and system tray (optional if time allows).

---

## 3. Technology Choice

### 3.1 Recommended approach: Tauri 2 + Python Sidecar

| Approach | Installer size | Memory | Native capability | Migration cost | Recommendation |
|------|------------|------|----------|----------|--------|
| **Tauri 2 + Python Sidecar** | Small (system WebView) | Low | Strong | Medium | ★★★★★ |
| Electron + Python Sidecar | Large (bundled Chromium) | High | Strong | Lower | ★★★☆☆ |
| Full native rewrite (Qt / Flutter) | Medium | Medium | Strongest | Very high | ★☆☆☆☆ |

**Why Tauri 2:**

- Installer size and runtime memory are substantially smaller than Electron, which matters for a photo-heavy app.
- Stronger default security (least privilege by default; no Node in the renderer).
- Official support for Windows NSIS/MSI and macOS DMG, plus code signing and notarization.
- Built-in sidecar process management, which fits bundling the FastAPI backend.
- Solid desktop capabilities: native file dialogs, menus, drag-and-drop, single-instance control.

### 3.2 Backend packaging

- Use **PyInstaller** (or evaluate Nuitka) to build `apps/api` into a standalone executable.
- Dependencies: fastapi, uvicorn, pillow, imagehash, numpy, sqlmodel, python-multipart, and similar.
- Start, monitor, and stop it as a Tauri sidecar with the main app.

### 3.3 Frontend adaptation (locked: dual-shell, single component library)

The Phase 0 `output: 'export'` attempt is a one-time investigation only (implementation plan D0.06); **the conclusion is expected to be not viable**: dynamic UUID routes under `projects/[projectId]/...` cannot be statically prerendered.

Locked approach:

- Keep `apps/web` as Next.js for browser development and Playwright; **do not migrate or delete it**.
- Add `apps/desktop` as a Tauri 2 + Vite + React SPA (React Router).
- Both shells share `apps/web/src/components`, `src/lib`, and `src/store`. Shared files must not import `next/link` or `next/navigation` directly; they go through a navigation adapter (D1.01).
- The Vite side must provide its own `@` path alias, PostCSS/Tailwind config, and reuse `globals.css` (D1.03a).

Communication: `http://127.0.0.1:<port>`, with the port allocated by Tauri and injected before the frontend loads. Tauri IPC is used only for dialogs, paths, and revealing items in the file manager.

### 3.4 Data directory

| Platform | Default data directory |
|------|----------------|
| macOS | `~/Library/Application Support/FramePilot` |
| Windows | `%APPDATA%\FramePilot` |
| Linux (development only; not a release target) | `~/.local/share/FramePilot` |

Override with `FRAMEPILOT_DATA_DIR`. The desktop sidecar must take an explicit `--data-dir`: a frozen executable's working directory is unpredictable, so falling back to a CWD-relative `.framepilot-data` is forbidden.

---

## 4. Target Architecture

```text
FramePilot Desktop
├── Tauri Shell (Rust main process)
│   ├── Window / menus / system tray (optional)
│   ├── Start, health-check, and graceful shutdown of the Python sidecar
│   ├── Native file / folder pickers
│   ├── Single-instance control
│   └── Auto-update (later, optional)
├── Frontend (static assets, loaded in the system WebView)
│   └── Existing React components + desktop adapter
└── Python Backend Sidecar (standalone executable)
    ├── FastAPI (127.0.0.1, fixed or dynamic port)
    ├── SQLite metadata
    └── Local project directories (originals / thumbnails / previews / exports / …)
```

**Core principles:**

- Do not upload originals; do not modify original files.
- Keep frontend/backend responsibility boundaries aligned with the current v2 architecture.
- The desktop shell owns process lifecycle.

---

## 5. Frontend UI Redesign Principles

The existing culling workspace already has a strong keyboard-first design. Desktop should strengthen native feel on that foundation, not start over.

### 5.1 Native window and menus

- Standard menu bar: File / Edit / View / Project / Help
- System shortcuts (Cmd/Ctrl + matching menu items)
- Remember window state (position, size, maximized)

### 5.2 Native filesystem interaction

- Use Tauri native dialogs to create/open projects and choose import folders
- Support dragging a whole folder from Finder / Explorer to import
- Open project paths and export paths in the system file manager in one click

### 5.3 Culling workspace desktop optimization

- Use large screens: resizable sidebars, optional detached preview window
- Clear status bar and processing progress feedback
- Keep and strengthen existing keyboard shortcuts (arrows, P/M/X/U, 1–5, 0, Space, Z, C, G, F, E, and similar)
- Full-screen preview and compare modes
- Keep the current virtual-list and lazy-load strategy for large projects

### 5.4 Settings and system integration

- Theme follows the system (dark / light)
- Data-directory management and performance options (concurrency, cache)
- Optional system tray (show progress during background work)
- About page and a check-for-updates entry

### 5.5 Visual consistency

- Keep the current Tailwind look
- Add desktop-typical spacing, layering, and focus management to reduce a “web page” feel

### 5.6 Explicitly deferred (not in `2.1.0-desktop`)

| Item | Reason | Target version |
|------|------|----------|
| Detached preview window (§5.3) | Needs a second WebView, cross-window state sync, and a second keyboard-focus manager | 2.2 |
| Performance options: concurrency, cache (§5.4) | Backend import/processing is currently single-thread sequential; a concurrency model is required first | 2.2 |
| Auto-update and “Check for updates” entry (§5.4, §6 Phase 4) | Needs a hosted update manifest; must stay strictly optional and must not block launch | 2.2 |
| System tray (§5.4) | Not a DoD item; implement only if Phase 3 finishes early (D3.06) | 2.1 optional / 2.2 |
| Changing the data directory (§5.4) | Involves migration and project-path rewrite; 2.1 is read-only display only (D3.03) | 2.2 |

If any of the above is skipped, it must be written into [docs/v2_known_limitations.md](v2_known_limitations.md) (D5.05).

---

## 6. Phased Development Plan

Total estimated effort (one full-time person or strong AI assistance): **about 6–10 weeks**.

### Phase 0: Feasibility and desktop-required APIs (about 3–5 days)

**Goal**: Prove the sidecar can be packaged and hosted, and land the backend APIs desktop depends on.

Tasks (authoritative split is implementation plan D0.00–D0.09):

1. CI verify workflow first (D0.00), so later commits can be verified.
2. Sidecar CLI: loopback-only bind, explicit `--data-dir`, machine-readable ready line.
3. Health check carries version; Origin and Host allowlists support desktop mode.
4. Path-based import API (chunked requests; originals stay read-only).
5. PyInstaller one-dir packaging and headless smoke.
6. Minimal Tauri window + sidecar start and health check (needs a host with a usable WebView).
7. Record size, startup time, and memory baselines; write a go/no-go.

Acceptance (by environment):

- **Headless host (for example WSL2)**: sidecar starts, `/health` is healthy, process exits after SIGTERM; path import does not modify original files; `npm run test:api` and `npm run verify` pass; Tauri tasks are marked blocked-gui, with commands and errors recorded in [docs/desktop_feasibility_notes.md](desktop_feasibility_notes.md).
- **GUI host (Windows / macOS / CI)**: at least one platform shows an empty shell window with “API ready”; two-platform window proof can wait until Phase 4 CI is done.

Phase 0 must not block for lack of GUI, but two-platform window evidence is required before shipping `2.1.0-desktop`.

---

### Phase 1: Desktop shell and sidecar foundation (about 1.5–2 weeks)

**Goal**: The desktop app can start fully in development mode.

Tasks:

1. Add `apps/desktop` (or repo-root `src-tauri`) and integrate Tauri 2.
2. Implement sidecar lifecycle: start, health check, graceful shutdown, crash-restart policy.
3. Map the data directory to the user-standard location, with env-var override.
4. Add `apps/desktop`: Vite + React SPA, reusing `apps/web/src/components`, `src/lib`, and `src/store` (**do not** turn `apps/web` into a static export).
5. Basic window create/close and single-instance control.
6. Dev script: `tauri dev` starts frontend + sidecar in one step.

Deliverables:

- A desktop app that runs on a developer machine via `tauri dev`
- Directory layout and build-script notes

Acceptance:

- After launch, the frontend can reach backend health check and project-list APIs

---

### Phase 2: Native filesystem and core workflow (about 1.5–2 weeks)

**Goal**: The full workflow works in the desktop environment.

Tasks:

1. Replace the browser File API with native file/folder pickers.
2. Support drag-and-drop folder import.
3. Desktop-ize project create, open, and recent-project list.
4. Verify the Import → Process → Culling → Export path end to end.
5. Handle cross-platform path, permission, and drive-letter differences.
6. Open export results in the system file manager.

Deliverables:

- A functionally complete desktop workflow

Acceptance:

- Complete one full cull-and-export pass with synthetic or real JPEG
- Originals were not modified or deleted

---

### Phase 3: UI redesign and polish (about 2 weeks)

**Goal**: Reach a professional desktop-product look and feel.

Tasks:

1. Implement the native menu bar and shortcut mapping.
2. Improve Culling Workspace layout and large-screen fit.
3. Finish status bar, progress feedback, and settings page.
4. Theme system and window-state memory.
5. Optional: system tray and background-work notifications.
6. Desktop copy and interaction for empty, error, and loading states.

Deliverables:

- UI whose visuals and interaction meet desktop-product standard

Acceptance:

- Keyboard-first culling feels fluid
- No obvious “browser web page” feel

---

### Phase 4: Installers, signing, and release prep (about 1–1.5 weeks)

**Goal**: Produce distributable official installers.

Tasks:

1. Configure Windows NSIS (or MSI) and macOS DMG builds.
2. Integrate code signing (Windows Authenticode, macOS Developer ID + notarization).
3. GitHub Actions CI: auto-build installers for both platforms.
4. Optional: Tauri updater basics for auto-update.
5. Slim installer size and dependencies.

Deliverables:

- Distributable `.exe` / `.dmg` (plus signing notes)
- CI workflow files

Acceptance:

- A clean machine can install and run the full workflow

---

### Phase 5: Testing, docs, and stabilization (about 1 week)

**Goal**: A releasable v2.x Desktop.

Tasks:

1. Desktop-specific test matrix:
   - Start / quit / sidecar crash recovery
   - Large-project import and processing (100 / 500 / 2000)
   - Path permissions and cross-platform differences
   - Clean install / uninstall
2. Update README, user docs, and known-limitations docs.
3. Performance and memory validation.
4. Release notes (Changelog) and version: first desktop version is locked to `2.1.0-desktop`; `2.0.x` remains the local web line. Do not use `3.0.0` (no breaking data-format change).

Deliverables:

- Test report
- Updated documentation
- Official release-candidate packages

Acceptance:

- Meets every Definition of Done item in section 2.2

---

## 7. Suggested Repository Layout (incremental)

```text
frame-pilot/
├── apps/
│   ├── api/                 # existing FastAPI (keep)
│   ├── web/                 # existing Next.js (browser + Playwright, keep)
│   └── desktop/             # new Tauri shell (optional location)
│       ├── src-tauri/
│       │   ├── src/
│       │   ├── icons/
│       │   ├── tauri.conf.json
│       │   └── Cargo.toml
│       └── package.json
├── packaging/
│   ├── pyinstaller/         # backend packaging specs
│   │   ├── framepilot-api.spec
│   │   └── build.sh
│   └── scripts/
├── docs/
│   ├── desktop_development_plan.md   # this file
│   └── ...
└── ...
```

(Exact directories can be tuned in Phase 0/1 to match team convention.)

---

## 8. Main Risks and Mitigations

| Risk | Impact | Mitigation |
|------|------|----------|
| Python dependency size (Pillow, numpy, and similar) | Installer bloat | Slim PyInstaller, exclude test deps; evaluate Nuitka; build per platform |
| System WebView differences (Windows WebView2 vs macOS WebKit) | Frontend compatibility | Dual-platform testing early in Phase 0/1; CSS/JS fallbacks if needed |
| Code-signing and notarization cost and process | Poor distribution experience | Apply for certificates early; sign in CI; unsigned packages are OK for self-test during development |
| Sidecar process management (crashes, port conflicts, zombie processes) | Stability | Health checks + timed forced cleanup; port probe before start; platform-specific exit logic |
| Next.js static-export compatibility | Development cost | Record once in D0.06; lock the Vite desktop shell; do not migrate `apps/web` |
| Large-image decode memory pressure in WebView | Large-project experience | Keep current virtual list and bounded rendering; watch peak memory on desktop |

---

## 9. Testing Strategy (desktop increment)

On top of existing `npm run verify`, API pytest, frontend unit, and E2E, add:

1. **Sidecar lifecycle tests**: start failure, port in use, restart after crash.
2. **Native dialog and drag-and-drop tests**: manual plus as much automation as practical.
3. **Installer smoke**: clean Windows / macOS VM install → full workflow → uninstall.
4. **Performance regression**: reuse current `perf:api` and real-browser smoke ideas; record baselines under the desktop shell.
5. **Security regression**: confirm originals are still not uploaded and export paths cannot escape the project root.

---

## 10. Versioning and Release Recommendations

| Version | Meaning |
|------|------|
| 2.0.x | Continue stabilizing the current local Web rc |
| 2.1.0-desktop | First official desktop installer release (locked) |
| 2.2 | Deferred items: detached preview window, performance options, auto-update, tray, and similar |
| Later 3.x | HEIC/RAW, XMP sidecar, optional local models, following the original develop_plan |

Suggested release channels:

- GitHub Releases (primary)
- A website download page later, if needed

---

## 11. Rough Effort Estimate (reference)

| Phase | Estimate |
|------|------|
| Phase 0 feasibility | 3–5 days |
| Phase 1 desktop shell + sidecar | 1.5–2 weeks |
| Phase 2 native FS + workflow | 1.5–2 weeks |
| Phase 3 UI desktop polish | 2 weeks |
| Phase 4 installers and signing | 1–1.5 weeks |
| Phase 5 testing and docs | 1 week |
| **Total** | **about 6–10 weeks** |

Actual progress depends on staying with Tauri, whether the frontend needs the Vite move, and how ready code signing is.

---

## 12. Suggested Immediate Next Steps

Implementation-level task split and Goal Mode prompts (based on the 2026-08-18 repository state):

- [docs/plans/2026-08-18-desktop-packaging.md](plans/2026-08-18-desktop-packaging.md) — detailed development plan executed task-by-task as D0.00…D5.05 (includes the §5.1 task checklist; 2026-08-18 review findings were folded into this file)
- [docs/desktop_goal_mode.md](desktop_goal_mode.md) — pasteable Grok Build / Codex Goal Mode prompt

1. **Confirm the technology choice**: Tauri 2 + Python Sidecar (this plan’s default; fall back to Electron only after a written D0.09 veto).
2. **Create branch** `feature/desktop-packaging`.
3. **Paste the long prompt from `docs/desktop_goal_mode.md` into Goal Mode** and start at **D0.00**, committing one task at a time.
4. **Execution order**: D0.00 (CI verify) first, then D0.01…D0.09. After any task completes, tick the matching id in implementation-plan §5.1 in the same commit as the code.

---

## 13. In-Repo References

- [README.md](../README.md) — current features and how to run
- [develop_plan.md](../develop_plan.md) — v2 master plan (includes the desktop stretch goal)
- [docs/plans/2026-08-18-desktop-packaging.md](plans/2026-08-18-desktop-packaging.md) — per-task desktop implementation plan (Goal Mode backlog; this file wins technical conflicts; 2026-08-18 review findings were folded in, and the original review file was deleted)
- [docs/desktop_goal_mode.md](desktop_goal_mode.md) — desktop Goal Mode prompt
- [docs/v2_architecture.md](v2_architecture.md) — architecture (desktop packaging remains deferred in v2.0; the desktop track proceeds separately)
- [docs/v2_product_requirements.md](v2_product_requirements.md) — product boundaries
- [docs/v2_known_limitations.md](v2_known_limitations.md) — known limitations
- [docs/v2_milestones.md](v2_milestones.md) — milestones
- [docs/architecture.md](architecture.md) — implementation-level architecture notes

---

## 14. Changelog

| Date | Version | Notes |
|------|------|------|
| 2026-08-18 | 1.0 | First version: complete desktop (Win/macOS) development plan based on frame-pilot v2.0.0-rc2 |
| 2026-08-18 | 1.1 | Add implementation-plan and Goal Mode entry points: `docs/plans/2026-08-18-desktop-packaging.md`, `docs/desktop_goal_mode.md` |
| 2026-08-18 | 1.2 | Align after Opus 5 review: lock Vite dual-shell, `2.1.0-desktop`, WSL-aware Phase 0 acceptance, §5.6 deferred list |

---

*This document is an implementation blueprint. Technical details may be tuned from Phase 0 measurements, but the three core goals must stay: local-first, original-file safety, and installable apps on both platforms.*

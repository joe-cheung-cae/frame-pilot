# Phase 5 Documentation Design (2026-08-29)

> Language: **English** | [中文](2026-08-29-phase5-docs-design.zh.md)

**Umbrella:** [#78](https://github.com/joe-cheung-cae/frame-pilot/issues/78)  
**This gate:** [#81](https://github.com/joe-cheung-cae/frame-pilot/issues/81) — docs design only  
**Research input:** [2026-08-29-phase5-requirements.md](2026-08-29-phase5-requirements.md)  
**Task id truth:** [2026-08-18-desktop-packaging.md](2026-08-18-desktop-packaging.md) Phase 5 / §5.1

This is the **outline and file map** for D5.01–D5.05. It is not the final user-facing content. Gate 3 must accept this design before any Dev PR lands.

---

## 1. File map

| Path | Create / edit | Task | Notes |
| ---- | ------------- | ---- | ----- |
| `docs/desktop_testing.md` + `.zh.md` | **Create** | D5.01 | Phase 5 test matrix (command tables) |
| Root `package.json` | **Edit** (optional) | D5.01 | Add thin aliases only if they improve discoverability; prefer documenting existing scripts |
| `README.md` + `README.zh.md` | **Edit** | D5.02 | Short Desktop section + link to user guide; keep web setup primary for contributors |
| `docs/desktop_user_guide.md` + `.zh.md` | **Create** | D5.02 | End-user install / first launch / data / export reveal |
| `docs/v2_architecture.md` + `.zh.md` | **Edit** | D5.02 | Remove “desktop packaging” from Deferred; point to desktop plan / user guide |
| `apps/desktop/README.md` | **Edit** | D5.02 | Fix stale “installers wait until Phase 4”; link to user guide + signing |
| `docs/v2_performance_baseline.md` + `.zh.md` | **Edit** | D5.03 | New “Desktop sidecar / WebView” section with 100-photo row (or sidecar-only + UI pending) |
| `docs/desktop_feasibility_notes.md` + `.zh.md` | **Edit** | D5.03 | Dated note for measurement host / `[~]` UI if applicable |
| `apps/api/app/core/version.py` | **Edit** | D5.04 | `APP_VERSION = "2.1.0-desktop"` |
| `apps/api/pyproject.toml` | **Edit** | D5.04 | `version = "2.1.0-desktop"` |
| Root / `apps/web` / `apps/desktop` `package.json` | **Edit** | D5.04 | `"version": "2.1.0-desktop"` |
| `CHANGELOG.md` | **Create** | D5.04 | Keep English-only license-style legal text? Prefer English changelog with bilingual switcher link to `CHANGELOG.zh.md` if we add ZH — **Decision: bilingual pair** `CHANGELOG.md` + `CHANGELOG.zh.md` |
| `docs/v2_known_limitations.md` + `.zh.md` | **Edit** | D5.05 | New “Desktop 2.1” section with required bullets |
| `docs/plans/2026-08-18-desktop-packaging.md` + `.zh.md` | **Edit** | each Dev PR | Tick §5.1 for that task id in the **same** commit |
| Close-out only: Phase 5 DoD boxes | **Edit** | Gate 5 | Cite evidence; leave true `[~]` honest |

Do **not** recreate `docs/handoff/*`.

---

## 2. D5.01 — `docs/desktop_testing.md` outline

Language switcher; intro: local-first, never modify originals, rust-free `verify` vs GUI-host commands.

### 2.1 Prerequisites

- OS matrix: Windows / macOS (primary installers); Linux/WSL notes (dev / no installer DoD)
- Tooling: Node 22, Python 3.11 venv, optional rustc ≥1.88 for GUI
- Links: `apps/desktop/README.md`, signing runbook, Phase 2 [tests/desktop/workflow.md](../../tests/desktop/workflow.md)

### 2.2 Matrix — lifecycle

| Row | Command / action | Pass criteria |
| --- | ---------------- | ------------- |
| Start | `npm run dev:desktop` or installed app | Window `FramePilot`; sidecar loopback; `GET /health` 200 |
| HTTP smoke | `npm run test:desktop:smoke` | Exit 0 |
| Quit clean | Close with no active job | Sidecar exits; no orphan uvicorn |
| Quit + import | Close during import | Dialog paths per desktop README; originals untouched |
| Sidecar crash | Kill sidecar process while UI open | Visible failure; restart recovers or documents retry |
| Port in use | Bind conflict on intended port | Clear error; no bind to `0.0.0.0` |

### 2.3 Matrix — import / scale

| Row | Command / action | Pass criteria |
| --- | ---------------- | ------------- |
| 100 synthetic path import | `npm run generate:synthetic` → path import via desktop or API | Job complete; copies under `originals/`; sources unchanged |
| Optional 500 / 2000 | `npm run perf:api -- …` | Document counts; GUI optional / pending |
| Install / uninstall | CI NSIS + DMG (or local `tauri build`) | App launches once; uninstall removes app binary (data dir may remain — document) |

### 2.4 Matrix — security / network

| Row | Notes |
| --- | ----- |
| Loopback only | Sidecar binds `127.0.0.1` |
| Origin / Host | Desktop origin only with `FRAMEPILOT_DESKTOP=1`; LAN browse to machine IP **must fail** |
| Project roots | Custom roots only via D2.00 registration |

### 2.5 Scripts to document (prefer no new scripts)

Document existing: `dev:desktop`, `test:desktop:smoke`, `generate:synthetic`, `perf:api`, `packaging:sidecar`, `test:sidecar`, `verify`.

**Optional alias (only if design review wants it):** `"test:desktop:matrix": "npm run test:desktop:smoke"` — thin; otherwise skip.

**Commit:** `docs: add desktop test matrix`  
**§5.1:** D5.01 → `[x]`

---

## 3. D5.02 — User docs outline

### 3.1 `docs/desktop_user_guide.md`

1. What FramePilot desktop is (local-first; sidecar managed)
2. Install (Windows NSIS / macOS DMG; unsigned SmartScreen/Gatekeeper warning → signing doc)
3. First launch (window title; data directory locations by OS; Settings shows data dir via `/api/meta`)
4. Create project + native folder picker
5. Import (path import; copies not moves; chunked 100 files)
6. Process → Cull → Export; **Open export folder** / reveal
7. Quit with running jobs (summary; link desktop README for dialogs)
8. Keep using the **web app** for development (`npm run dev`) vs desktop shell
9. Links: testing matrix, known limitations, architecture, Phase 2 workflow checklist

### 3.2 README edits

- After “Run Locally”, add **Desktop app** subsection: one paragraph + link to `docs/desktop_user_guide.md`
- Keep contributor web path unchanged
- Retain unsigned CI installer warning; link signing + user guide

### 3.3 Architecture / desktop README

- Architecture: remove desktop packaging from Deferred; add short “Desktop shell” note (Tauri + sidecar)
- `apps/desktop/README.md`: installers exist via CI; point to user guide

**Commit:** `docs: add desktop install and data-dir instructions`  
**§5.1:** D5.02 → `[x]`

---

## 4. D5.03 — Performance notes outline

Add section **Desktop path-import performance** to `docs/v2_performance_baseline.md` (+ zh):

| Field | Content |
| ----- | ------- |
| Host / date | Fill at Dev time |
| Method | 100-photo path import + process; record sidecar RSS (and UI if GUI) |
| Table columns | Count, Import s, Process s, Sidecar peak RSS MB, UI RSS MB or `pending` |
| Caveats | WSL/no WebView → UI `pending`; synthetic JPEGs ≠ camera diversity |

Append matching dated bullet under feasibility notes if measurement is `[~]` for UI.

**Commit:** `docs: record desktop performance notes`  
**§5.1:** D5.03 → `[x]` (or `[~]` only if packaging plan allows partial — prefer `[x]` with UI pending called out in the doc body, matching locked decision 13)

---

## 5. D5.04 — Version bump checklist

1. Set `APP_VERSION = "2.1.0-desktop"` in `apps/api/app/core/version.py` only as source of truth for API payloads
2. Sync string in: `apps/api/pyproject.toml`, root `package.json`, `apps/web/package.json`, `apps/desktop/package.json`
3. Create `CHANGELOG.md` + `CHANGELOG.zh.md`: `2.1.0-desktop` RC section (desktop shell, path import, CI installers, unsigned note); prior `2.0.0-rc2` web line briefly
4. Do **not** `git tag` in this PR
5. Tests: `npm run test:api` asserts health version; `npm run verify`

**Commit:** `release: 2.1.0-desktop rc`  
**§5.1:** D5.04 → `[x]`

---

## 6. D5.05 — Known limitations outline

New section **Desktop 2.1** in `docs/v2_known_limitations.md` (+ zh), bullets required by packaging plan:

- Jobs not durable across sidecar kill / process exit
- HEIC / RAW skipped
- Auto-update deferred
- Unsigned installers until certs (link signing runbook)
- WSL may not run GUI
- Copy mode only (no reference-in-place)
- No detached preview window
- No concurrency knobs
- Optional tray deferred (D3.06); no `fs:`/`shell:` tray capabilities

Cross-link user guide + testing matrix.

**Commit:** `docs: document desktop 2.1 known limitations`  
**§5.1:** D5.05 → `[x]`

---

## 7. Design section → task → commit map

| Design § | Task | Commit |
| -------- | ---- | ------ |
| §2 | D5.01 | `docs: add desktop test matrix` |
| §3 | D5.02 | `docs: add desktop install and data-dir instructions` |
| §4 | D5.03 | `docs: record desktop performance notes` |
| §5 | D5.04 | `release: 2.1.0-desktop rc` |
| §6 | D5.05 | `docs: document desktop 2.1 known limitations` |

Dev order: D5.01 → D5.02 → D5.03 → D5.04 → D5.05 (one issue + PR each).

---

## 8. Gate 3 — “acceptable” checklist

Reviewers must confirm before merging this design and before any Dev PR:

- [ ] Scope matches packaging Phase 5 (no HEIC/RAW/XMP/tray/updater/Electron)
- [ ] Every D5.0x has a clear file list and commit message
- [ ] Bilingual pairs planned for all new living docs
- [ ] Version bump stays single-sourced; no premature tag
- [ ] D5.03 allows sidecar-only + UI pending on GUI-blocked hosts
- [ ] DoD tick-all deferred to Gate 5 close-out (not claimed in design)
- [ ] No §5.1 D5.0x ticks in the design PR itself

**Acceptance record:** GitHub approval on the design PR **or** explicit issue comment on #81 / review issue: `design accepted`.

---

## 9. Non-goals (repeat)

Same as research §5: no algorithm work, no tray implementation, no promoting D3.01–D3.03 `[~]` without GUI evidence, no scattering version literals outside D5.04 surfaces.

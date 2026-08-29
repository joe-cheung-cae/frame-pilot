# Phase 5 Requirements Inventory (2026-08-29)

> Language: **English** | [中文](2026-08-29-phase5-requirements.zh.md)

**Umbrella:** [#78](https://github.com/joe-cheung-cae/frame-pilot/issues/78)  
**This gate:** [#79](https://github.com/joe-cheung-cae/frame-pilot/issues/79) — requirement research only  
**Source of truth for task ids:** [2026-08-18-desktop-packaging.md](2026-08-18-desktop-packaging.md) Phase 5 / §5.1

This document inventories what Phase 5 must deliver. It does **not** write final user docs, bump the version, or tick D5.01–D5.05.

---

## 1. D5.01–D5.05 acceptance intent (from packaging plan)

| Id | Intent | Depends on | Planned primary files | Commit message |
| ---- | ------ | ---------- | --------------------- | -------------- |
| **D5.01** | Desktop test matrix document + commands: start/quit/sidecar crash/port in use; path import of 100 synthetic JPEGs; optional 500/2000 via `perf:api`; install/uninstall checklist; origin/CORS notes (LAN impossible — loopback-only) | Phase 4 | `docs/desktop_testing.md` (+ zh), root `package.json` scripts if useful | `docs: add desktop test matrix` |
| **D5.02** | README + user docs: install, first launch, data location, copies not moves, reveal export folders, keep using web app for development; architecture no longer lists desktop as deferred once shipped | D5.01 | `README.md` (+ zh), `docs/desktop_user_guide.md` (+ zh), pointers in known limitations / architecture | `docs: add desktop install and data-dir instructions` |
| **D5.03** | One 100-photo path-import + process RSS for sidecar and UI if GUI exists; otherwise sidecar-only and mark UI pending | D2.08 (done) | feasibility notes and/or `docs/v2_performance_baseline.md` (+ zh) | `docs: record desktop performance notes` |
| **D5.04** | Version bump to `2.1.0-desktop` RC; single source in `apps/api/app/core/version.py`; update `pyproject.toml` and both `package.json`; changelog; do not tag until verify + desktop CI artifacts exist | Phases 0–4 acceptance | `version.py`, `apps/api/pyproject.toml`, root + `apps/web`/`apps/desktop` `package.json`, changelog | `release: 2.1.0-desktop rc` |
| **D5.05** | Known limitations for desktop 2.1: jobs not durable across sidecar kill; HEIC/RAW skipped; auto-update deferred; unsigned until certs; WSL may not run GUI; copy mode only; no detached preview; no concurrency knobs; tray deferred (D3.06) | D5.02 | `docs/v2_known_limitations.md` (+ zh) | `docs: document desktop 2.1 known limitations` |

Phase 5 / product DoD boxes (still unchecked in §5.1) are listed in §3 below.

---

## 2. Existing asset inventory

### Scripts (root `package.json`)

| Script | Role for Phase 5 |
| ------ | ---------------- |
| `dev:desktop` | Start Tauri + sidecar (needs rustc ≥1.88 on host) |
| `test:desktop:smoke` | HTTP smoke: sidecar health + project list (`tests/desktop/smoke.sh`) |
| `perf:api` | API performance smoke; supports counts including 100/500/2000 |
| `generate:synthetic` | Synthetic JPEG dataset for path-import matrix rows |
| `packaging:sidecar` / `test:sidecar` | PyInstaller build + sidecar smoke |
| `verify` | Rust-free gate (lint, typecheck, typecheck:desktop, tests, artifacts) |
| `check:markdown-links` | Bilingual living-doc + relative link checker |
| `check:pretag` | verify + validation decision (web release line) |

No dedicated `docs/desktop_testing.md` or `docs/desktop_user_guide.md` exists yet.

### Docs already present

| Path | Gap relative to Phase 5 |
| ---- | ----------------------- |
| [tests/desktop/workflow.md](../../tests/desktop/workflow.md) | Phase 2 GUI checklist; still cites `APP_VERSION` `2.0.0-rc2`; not a full Phase 5 test matrix |
| [apps/desktop/README.md](../../apps/desktop/README.md) | Dev shell / data-dir / quit semantics; says installers wait until Phase 4 (stale vs completed Phase 4) |
| [docs/desktop_signing.md](../desktop_signing.md) | Unsigned CI OK for first RC; signing follow-up |
| [docs/desktop_feasibility_notes.md](../desktop_feasibility_notes.md) | Phase 0–4 measurements; GUI/`cargo` `[~]` on WSL hosts without rustc 1.88 |
| [docs/v2_performance_baseline.md](../v2_performance_baseline.md) | Web/API baseline + `perf:api` tables; **no desktop WebView / sidecar path-import RSS row yet** |
| [docs/v2_known_limitations.md](../v2_known_limitations.md) | v2.0 web-oriented; has desktop quit/sidecar notes but **not** the D5.05 desktop-2.1 bullet list |
| [docs/v2_architecture.md](../v2_architecture.md) | Still lists **desktop packaging** under Deferred Architecture |
| [README.md](../../README.md) | Web-first setup; brief unsigned-installer warning; **no install / first-launch / desktop data-dir user guide** |
| Changelog | **None** in repo; D5.04 must add one (or an agreed equivalent) per packaging plan |

### Version surfaces (today)

- Canonical: `apps/api/app/core/version.py` → `APP_VERSION = "2.0.0-rc2"`
- Also: root `package.json` `"version": "2.0.0-rc2"`; packaging plan requires updating `pyproject.toml` and both app `package.json` files only in D5.04
- Locked decision 15: do not scatter version literals; health/`/api/meta` already read `APP_VERSION`

### CI evidence already on main

- `.github/workflows/desktop.yml` builds Windows NSIS + macOS DMG (unsigned)
- Packaging plan Phase 4 acceptance cites [desktop.yml run 33170731977](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/33170731977)

---

## 3. Phase 5 DoD vs current `main`

| DoD box | Status on `main` | What Phase 5 still needs |
| ------- | ---------------- | ------------------------ |
| Windows and macOS installers exist (CI artifacts) | **True** (desktop CI) | Close-out: cite fresh or known Actions run in tracker |
| App start manages Python sidecar without uvicorn | **True** (Phase 1+ sidecar lifecycle) | Document in user guide / matrix |
| Native folder picker and drag-drop import | **Implemented**; live GUI may be `[~]` on some hosts | Document; keep `[~]` honest where unverified |
| Core workflow matches v2 | **True** at API / shared UI (D2.08) | Matrix + user guide cross-links |
| Originals never modified | **True** (immutability tests + workflow checklist) | Reaffirm in user docs |
| 500-photo API-level path import; 500 GUI if measured | API path covered by existing perf/API tests; **500 GUI often unmeasured** | Matrix: optional `perf:api`; GUI row may stay pending |
| User + developer docs exist | **Partial** (dev READMEs, signing, feasibility) | **D5.01–D5.02** are the gap |
| CI builds both platform installers; signing pending | **True** / signing deferred by design | D5.05 + signing runbook already |
| Loopback bind + Host/Origin checks | **True** (Phase 0) | Matrix CORS/LAN notes |
| Custom project roots only via D2.00 | **True** | User guide / limitations |

---

## 4. GUI / host limits for D5.03

Locked decision 13: `[~]` when WebView/GUI cannot run.

On hosts without `rustc` ≥1.88 / display (typical WSL agent):

- D5.03 may record **sidecar-only** RSS for 100-photo path-import + process
- Mark **UI / WebView RSS pending** with a dated note in feasibility or performance baseline
- Do **not** invent GUI numbers

D3.01–D3.03 remain `[~]` for live menu/status/settings GUI; Phase 5 must not pretend those are `[x]`.

---

## 5. Non-goals (Phase 5)

- HEIC / RAW decoding, XMP sidecar export, local neural models
- Cloud updater / auto-update shipping
- Electron switch
- Implementing optional tray (D3.06 stays deferred; D5.05 records it)
- Promoting D3.01–D3.03 `[~]` → `[x]` without a real GUI/`cargo` run
- Scattering `2.1.0-desktop` literals outside the D5.04 surfaces
- Reopening closed PR #27 / #67–#76 follow-ups

---

## 6. Suggested gate order (reminder)

1. This research (Gate 1) → merge  
2. Docs design (Gate 2) → review loop (Gate 3) until accepted  
3. Dev PRs: D5.01 → D5.02 → D5.03 → D5.04 → D5.05  
4. Close-out: tick DoD + umbrella #78  

**Hard gate:** no D5.0x implementation until the docs design is explicitly accepted.

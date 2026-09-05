# Phase 9 Implementation Plan — Remaining Stretch Close-Out (2026-09-04)

> Language: **English** | [中文](2026-09-04-remaining-stretch.zh.md)

**Umbrella:** [#160](https://github.com/joe-cheung-cae/frame-pilot/issues/160) (S9.00 schedule)  
**Related:** `develop_plan.md` §1.1; Phase 7 [2026-09-03-phase7-processing-cancel.md](2026-09-03-phase7-processing-cancel.md); Phase 8 [2026-09-04-heic-preview.md](2026-09-04-heic-preview.md); XMP historical [#117](https://github.com/joe-cheung-cae/frame-pilot/issues/117)

For Goal Mode and `/workflow remaining-stretch`: implement **one GitHub issue per run**. Pass `args.slice` (`s901`…`s913`). Do not start the next id until the current issue is implemented, tested, reviewed, committed, and pushed.

---

## 1. Why this slice

Numbered delivery through Phase 8 is on `main`. The leftover list in §1.1 was unscheduled stretch, not a license to freelance. This plan **schedules** that list as Phase 9 (S9.00–S9.13). Do not invent Phase 10.

S9.00 is this document, the §1.1 pointer, GitHub issues, and the workflow file. Product work starts at S9.01.

---

## 2. Locked decisions

1. **Local-first.** No photo upload, login, payment, or bundled neural models.
2. **Never modify or delete original photos.** Derivatives, export artifacts, XMP sidecars, and caches stay off the source files.
3. **One GitHub issue per workflow `phase()` / run.** Do not pack S9.01–S9.13 into one 开发 stage.
4. **J7.07:** cooperative `pause_requested` at existing processing checkpoints; worker exits without `cancelled` finalize and without reviewable partial groups. **Resume = clear-and-rerun** via `POST /process`. Do not keep half-built groups.
5. **Export cancel:** allow `job_type == "export"` on the existing cancel route. Cooperative checkpoints. Partial ZIP/folder uses fail-and-cleanup. Fix `"Only import jobs can be cancelled"`. Desktop quit can cancel an active export.
6. **AVIF:** add `.avif` to the existing still import/export pipeline. Decode with Pillow’s native `AvifImagePlugin` (live `pillow-heif` 1.6 dropped AVIF; do not make the HEIF opener claim `.avif`). Tiny in-process tests. Not RAW.
7. **RAW:** copy original bytes; extract **embedded preview only**. No thumb → skip with an explicit local message. No demosaic. No camera files in git. Document LibRaw license like libheif.
8. **XMP:** implement on [#165](https://github.com/joe-cheung-cae/frame-pilot/issues/165). Write `.xmp` only in the export directory. Never write into `originals/` or beside camera originals. Optional, default off.
9. **Concurrency knobs:** default remains one import/processing worker. Settings may raise import workers to 2–4 opt-in. One processing job per project. No Redis/Celery.
10. **Check for updates:** menu click only; GitHub Releases; no launch-time network; missing manifest is non-fatal.
11. **Signing:** CI gated on secrets; unsigned fallback must stay green. DoD is signing-ready, not a store release.
12. **macOS QA:** skip ≠ pass. Record skip with an ISO-8601 timestamp if no Mac host.
13. **No `APP_VERSION` bump.** CHANGELOG Unreleased only.
14. **Bilingual living docs**; English code, comments, tests, commits.
15. **Tests first.** `npm run verify` before each 上线.
16. **Out:** D4.03, full RAW develop, in-place grouping pause, cloud, Dramatiq/RQ, inventing Phase 10.

---

## 3. Status board

Phase 9 — remaining stretch (post Phase 8)

- [x] S9.00 Schedule slices, GitHub issues, §1.1 pointer, workflow — [#160](https://github.com/joe-cheung-cae/frame-pilot/issues/160)
- [x] S9.01 Export job cancel — [#164](https://github.com/joe-cheung-cae/frame-pilot/issues/164)
- [x] S9.02 J7.07 processing pause/resume — [#161](https://github.com/joe-cheung-cae/frame-pilot/issues/161)
- [x] S9.03 AVIF still preview — [#163](https://github.com/joe-cheung-cae/frame-pilot/issues/163)
- [x] S9.04 RAW embedded preview — [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162)
- [x] S9.05 XMP sidecar export — [#165](https://github.com/joe-cheung-cae/frame-pilot/issues/165) (historical [#117](https://github.com/joe-cheung-cae/frame-pilot/issues/117))
- [x] S9.06 Optional system tray (D3.06) — [#169](https://github.com/joe-cheung-cae/frame-pilot/issues/169)
- [x] S9.07 Detached preview window — [#166](https://github.com/joe-cheung-cae/frame-pilot/issues/166)
- [x] S9.08 Opt-in import concurrency knobs — [#168](https://github.com/joe-cheung-cae/frame-pilot/issues/168)
- [ ] S9.09 Change data directory — [#170](https://github.com/joe-cheung-cae/frame-pilot/issues/170)
- [ ] S9.10 Optional check for updates — [#167](https://github.com/joe-cheung-cae/frame-pilot/issues/167)
- [ ] S9.11 Signing-ready CI — [#171](https://github.com/joe-cheung-cae/frame-pilot/issues/171)
- [ ] S9.12 macOS DMG GUI lifecycle QA — [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172)
- [ ] S9.13 Docs leftover repair — [#173](https://github.com/joe-cheung-cae/frame-pilot/issues/173)

---

## 4. Issue map

| ID | GitHub | Commit subject |
| -- | ------ | -------------- |
| S9.00 | [#160](https://github.com/joe-cheung-cae/frame-pilot/issues/160) | `docs: schedule remaining stretch S9.00–S9.13` |
| S9.01 | [#164](https://github.com/joe-cheung-cae/frame-pilot/issues/164) | `v2: allow cooperative cancel on export jobs` |
| S9.02 | [#161](https://github.com/joe-cheung-cae/frame-pilot/issues/161) | `v2: cooperative pause for processing jobs` |
| S9.03 | [#163](https://github.com/joe-cheung-cae/frame-pilot/issues/163) | `v2: import AVIF still previews` |
| S9.04 | [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162) | `v2: extract RAW embedded previews` |
| S9.05 | [#165](https://github.com/joe-cheung-cae/frame-pilot/issues/165) | `v2: write XMP sidecars in export directory` |
| S9.06 | [#169](https://github.com/joe-cheung-cae/frame-pilot/issues/169) | `desktop: optional system tray` |
| S9.07 | [#166](https://github.com/joe-cheung-cae/frame-pilot/issues/166) | `desktop: detached preview window` |
| S9.08 | [#168](https://github.com/joe-cheung-cae/frame-pilot/issues/168) | `desktop: opt-in import worker concurrency` |
| S9.09 | [#170](https://github.com/joe-cheung-cae/frame-pilot/issues/170) | `desktop: change data directory with path rewrite` |
| S9.10 | [#167](https://github.com/joe-cheung-cae/frame-pilot/issues/167) | `desktop: optional check for updates` |
| S9.11 | [#171](https://github.com/joe-cheung-cae/frame-pilot/issues/171) | `ci: sign desktop installers when secrets exist` |
| S9.12 | [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172) | `docs: macOS DMG GUI lifecycle QA` |
| S9.13 | [#173](https://github.com/joe-cheung-cae/frame-pilot/issues/173) | `docs: close out remaining stretch S9` |

---

## 5. Per-issue contract

### S9.00 — Schedule (this commit)

Docs + GitHub issues + `.grok/workflows/remaining-stretch.rhai`. No product behavior change.

S9.01–S9.07 contracts are unchanged and already shipped. See git history on `feature/remaining-stretch` for the locked export-cancel, pause, AVIF, RAW, XMP, tray, and detached-preview text.

### S9.08 — Concurrency knobs

Locked contract: [2026-09-04-s908.md](2026-09-04-s908.md). Settings 1–4 import **derivative** workers, default 1. One processing job per project. No Redis/Celery.

**Hole (live tree):** `run_import_derivative_job` is a sequential per-photo loop (`apps/api/app/services/importing.py`). No `GET`/`PATCH /api/settings`. `SettingsPanel` has no worker control. Exclusive `python -m app.worker` lock. Known limitations deny knobs. #168: import derivative workers 1–4 opt-in, default 1.

**Identity:** Persist `import_workers` int 1–4 default 1 in `{data_dir}/app_settings.json` (atomic tmp + replace). API-owned. Not localStorage, not `/api/meta`, not a schema bump. Snapshot at `run_import_derivative_job` start. `n==1` keeps the sequential loop. `n=2–4` uses `ThreadPoolExecutor`; each task has its own Session; peak concurrent `process_registered_import_photo` ≤ n. Cancel cooperative; wait in-flight; no thread kill. Originals never modified. No ProcessPool, no extra OS workers.

**API:** GET `/api/settings` → `{import_workers}`. PATCH same; `0`/`5`/non-int → 422. Web and desktop.

**Processing:** unchanged one job per project. No processing-worker knob. Import still one job per project (409).

**UI:** SettingsPanel **Import workers** 1–4 default 1. `api.getSettings` / `api.patchSettings`. Applies to the next import job.

**This plan (implementation commit only):** tick §3 S9.08 `[x]` (en+zh). Do not tick S9.09–S9.13.

**Files:** `apps/api/app/core/app_settings.py` (new); `apps/api/app/schemas/api.py`; `apps/api/app/api/routes.py`; `apps/api/app/services/importing.py`; `apps/api/tests/test_app_settings.py`; `apps/web/src/lib/api.ts`; `apps/web/src/components/SettingsPanel.tsx` (+ test); `docs/api.md`, `docs/v2_known_limitations.md`, architecture, user guide, CHANGELOG Unreleased (+ zh).

**Tests first:** GET default 1; PATCH 2–4 persist; invalid 422; peak concurrency; originals unchanged; cancel with workers=4; `POST /process` reuse; SettingsPanel.

**Non-goals:** Redis/Celery; processing pool; cache knobs; S9.09–S9.13; `APP_VERSION`; signing.

### S9.09 — Data directory

Explicit authorize (D2.00 allowlist). Rewrite stored project paths. Never rewrite camera-card originals.

### S9.10 — Check for updates

Menu only. GitHub Releases. No launch network.

### S9.11 — Signing-ready CI

`desktop.yml` steps gated on secrets. Unsigned path remains green. Update `docs/desktop_signing.md` (+ zh) with secret names. No certs in git.

### S9.12 — macOS DMG QA

Follow `docs/desktop_testing.md`. No Mac → skip with timestamp, not pass.

### S9.13 — Docs leftover repair

Align `docs/desktop_development_plan.md` §2.2; known limitations; README; CHANGELOG; `implement_goals.md`. Do not claim 2.2 items done until their boxes are `[x]`. PR body may say `Fixes` only after this issue.

---

## 6. Definition of Done (program)

- [x] §1.1 names S9.00–S9.13 and forbids inventing Phase 10
- [ ] S9.01–S9.13 each `[x]` with the commit subject in §4
- [ ] Originals never modified in tests
- [ ] `npm run verify` green on the branch tip before S9.13 上线
- [ ] One draft PR for `feature/remaining-stretch`; `Refs #160` plus the child numbers; no `Fixes` until S9.13
- [ ] No `APP_VERSION` bump, no certs, no camera files, no model weights

---

## 7. Workflow execution

Workflows cannot launch other workflows. One parameterized file:

| Run | Command |
| --- | --- |
| Next product issue | `/workflow remaining-stretch` with `{"slice":"s901"}` (then `s902`…) |
| File | `.grok/workflows/remaining-stretch.rhai` |

Each run’s dashboard `phase()` title is that issue id. Inside the phase: 需求拆解 → 评审 (+ skeptic) → 归档 → 开发 → 测试 → 上线.

**Branch:** `feature/remaining-stretch` from `origin/main`. Push after every issue. Never a second PR. No merge to `main` from the workflow. No squash. No force-push.

**Idempotent:** if §3 is `[x]` and `git log origin/main..HEAD` already has that commit subject, return `ok=true` and do not redo.

**Fail closed:** `ok=false` or skeptic `real=false` → stop. Do not start the next slice.

Suggested `agent_budget`: 32.

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
- [ ] S9.06 Optional system tray (D3.06) — [#169](https://github.com/joe-cheung-cae/frame-pilot/issues/169)
- [ ] S9.07 Detached preview window — [#166](https://github.com/joe-cheung-cae/frame-pilot/issues/166)
- [ ] S9.08 Opt-in import concurrency knobs — [#168](https://github.com/joe-cheung-cae/frame-pilot/issues/168)
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

### S9.01 — Export cancel

**Hole (live tree):** `create_export_endpoint` writes `ExportRecord` + `run_export_job` only. `cancel_job_endpoint` loads `ProcessingJob` and 422s unless `job_type` is `import` or `processing`, with detail `"Only import jobs can be cancelled"` (`apps/api/app/api/routes.py`). `test_cancel_export_job_is_still_rejected` plants `ProcessingJob(job_type="export")`. Cancel with `ExportRecord.id` is 404. Desktop `find_active_job` lists `/jobs`, not `/exports`; `close_job_kind` maps unknown types to the processing quit copy (`apps/desktop/src-tauri/src/sidecar.rs`).

**Identity:** On export create, also persist `ProcessingJob` with `job_type="export"` and **the same `id` as the `ExportRecord`**, status `running`. Keep the two rows in sync on complete / fail / cancel / stale. Do not enqueue export on the durable worker. Startup still fail-and-cleanup leftover `ExportRecord` rows and fail non-import/processing `ProcessingJob` rows; **do not reclaim export**.

**Route:** `POST /api/projects/{project_id}/jobs/{job_id}/cancel` allows `{import, processing, export}`. Dispatch export to `request_export_job_cancellation` (do not overload import/processing helpers). Replace the 422 detail so it names the three allowed types. Other `job_type` values stay 422.

HTTP (mirror processing):

| Job state | Persist | HTTP |
| -- | -- | -- |
| queued or running | `cancellation_requested`; `current_step=cancellation_requested`; status unchanged | `202` |
| terminal (`complete`, `complete_with_errors`, `failed`, `cancelled`) | no-op | `200` |
| interrupted (no in-flight worker) | finalize immediately | `200` |

**Checkpoints:** cooperative, per photo at the existing `progress_callback` sites in `write_selection_csv` / `copy_selected_files` / `zip_selected_files`. Not a hard kill. On flag: abort, then `_remove_partial_export` (csv/zip/folder under the project export root only). Paths outside that root stay. **Originals are never modified or deleted.**

**Finalize:** `ProcessingJob` → `cancelled` + `cancelled_at`. Linked `ExportRecord` → existing fail-and-cleanup (`failed`, no new export status, no durable resume). Re-run is a new `POST /export`.

**Desktop:** add `CloseJobKind::Export`. `job_type=="export"` must not reuse the processing dialog. CancelAndQuit → CancelThenTerminate (POST the same cancel route, wait ≤10s, SIGTERM). Buttons: Quit and cancel export / Keep working / Quit anyway. Copy: partial export artifacts are cleaned; originals unchanged; next launch still fail-and-cleanup (not reclaim).

**Files:** `apps/api/app/api/routes.py` (`cancel_job_endpoint`, `create_export_endpoint`, `run_export_job`); `apps/api/app/services/exporting.py` checkpoints; `apps/api/app/services/jobs.py` (export stays non-reclaim); invert `apps/api/tests/test_import_process_export_api.py`; `apps/desktop/src-tauri/src/sidecar.rs`. Docs that currently assert export 422 (`docs/api.md`, `docs/v2_known_limitations.md`, desktop README / user guide, CHANGELOG Unreleased; + zh). Tick §3 S9.01 only in the implementation commit.

**Tests first:** invert `test_cancel_export_job_is_still_rejected`. queued/running → 202 + flag; terminal → 200 no-op; originals untouched. Live csv/zip/folder cancel removes the partial artifact under export root and does not touch originals. Import/processing cancel tests stay green. Desktop rust: export kind + cancel-and-quit.

**Non-goals:** S9.02–S9.13; export durable resume / worker reclaim; ExportPanel cancel button (desktop quit is the UI); `APP_VERSION`; signing.

### S9.02 — J7.07 pause

**Hole (live tree):** No `pause_requested` column. `ProcessingJob` / `_ensure_processing_job_columns` only have `cancellation_requested`. `cancel_job_endpoint` dispatches processing to `request_processing_job_cancellation` (`apps/api/app/api/routes.py`). `_save_job`, `run_processing_job` (after `claim_job_atomic`), and `process_project` (after `starting`, derivative heartbeat, pre/post `group_similar_photos`, post-ranking commit) observe only `_processing_job_cancellation_requested` and call `_finalize_cancelled_processing_job` (`apps/api/app/services/processing.py`). `prepare_interrupted_processing_jobs_for_reclaim` cancel-finalizes when `cancellation_requested`, else re-queues. `POST /process` returns the existing row while status is in `BLOCKING_JOB_STATUSES` (`queued`/`running`/`interrupted`). `ProcessingPanel` has Cancel only (`api.cancelJob`). Web `ProcessingJob.status` has no `paused`. Phase 7 J7.07 is `[-]`. `docs/v2_known_limitations.md` and CHANGELOG Unreleased still say pause/resume of in-flight grouping is not implemented.

**Identity:** Distinct `pause_requested` BOOLEAN NOT NULL DEFAULT 0. **Do not** reuse `cancellation_requested`, `cancelled_at`, or `request_processing_job_cancellation`. Add `POST /api/projects/{project_id}/jobs/{job_id}/pause`. Expose `pause_requested` on `JobRead` and web `ProcessingJob`.

**Status:** Finalize this row as `paused` (not `cancelled`, not `failed`, not `interrupted`). `paused` is **terminal-for-this-row**: add it to `TERMINAL_JOB_STATUSES` so stale sweeps and crash handlers no-op. Do **not** add it to `ACTIVE_JOB_STATUSES` or `BLOCKING_JOB_STATUSES`, so `POST /process` can create a **new** job. This supersedes the Phase 7 sketch of a non-terminal in-place `paused` status. In-place continue-hash-mid-batch is a non-goal.

**Route:** `POST /api/projects/{project_id}/jobs/{job_id}/pause` allows `job_type == "processing"` only. Import / export / other → 422. Missing job or wrong `project_id` → 404. Dispatch to new `request_processing_job_pause` in `processing.py`. Do not send pause through cancel helpers. Cancel still uses `POST .../cancel`.

HTTP (mirror processing cancel, distinct flag):

| Job state | Persist | HTTP |
| -- | -- | -- |
| queued or running | `pause_requested`; `current_step=pause_requested`; **status unchanged** | `202` |
| terminal (`complete`, `complete_with_errors`, `failed`, `cancelled`, `paused`) | no-op; do not set the flag on a completed success | `200` |
| interrupted (no in-flight worker) | immediately pause-finalize (reset groups, `status=paused`, not `cancelled`) | `200` |

**Cancel wins:** if `cancellation_requested` is already true, do not overwrite `current_step` with pause; leave cancel in charge. Worker checkpoints check cancel first, then pause.

**Checkpoints:** cooperative, same sites as J7.02. Not a hard kill. At each site: cancel flag → existing cancel finalize; else pause flag → pause finalize; else continue. Prefer bool return from `_save_job` (False after pause or cancel finalize); callers `return job`. Do **not** raise through `process_project` / `run_processing_job` `except Exception` (that marks `failed`). **Do not** add a progress callback inside `group_similar_photos`.

Live sites that must observe pause (today cancel-only):

| Site | Live code |
| -- | -- |
| After atomic claim | `run_processing_job` after `claim_job_atomic` + refresh |
| After `starting` commit | `process_project` after the starting commit, **before** `_complete_unchanged_job` |
| Each `_save_job` | start of `_save_job` (`session.refresh` first) |
| Derivative heartbeat | every `DERIVATIVE_VALIDATION_HEARTBEAT_INTERVAL` photos and the post-loop heartbeat |
| Immediately before and after `group_similar_photos` | existing pre/post heartbeats |
| After each ranking group commit | after the per-group `session.commit()` that writes ranked photos |

**Pause finalize:** call `reset_project_after_processing_failure` **then** set `status="paused"`, `current_step="paused"`, `pause_requested=True`, `completed_at`, clear `worker_id` / `heartbeat_at` / `interrupted_at`, commit. Reason may be `"Processing job was paused by user request"`. Do **not** set `status="cancelled"`. Do **not** set `cancellation_requested` or `cancelled_at`. Groups empty, `processed_images == 0`, in-flight `processing` / `processed` photos return to `imported`. `user_status` / `star_rating` stay. Import derivatives stay. **Originals are never modified or deleted.** Not reviewable.

**Reclaim:** in `prepare_interrupted_processing_jobs_for_reclaim`, after atomic claim + refresh, inspect flags directly (do not use `_processing_job_cancellation_requested`; it is false when `interrupted`). If `cancellation_requested` → existing cancel finalize (cancel wins). Elif `pause_requested` → pause finalize; do **not** re-queue; do **not** increment `reclaim_count`. No-flag path stays Phase 6.1 queued reclaim. `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0` fail-and-retry unchanged for jobs without pause/cancel flags.

**Resume:** after the paused row is terminal, `POST /process` creates a **new** processing job and rebuilds groups (`create_processing_job` + `run_processing_job`). Do not resume the paused row in place. Do not extend `POST .../retry` beyond import.

**UI:** `ProcessingPanel` Pause control, distinct from Cancel. Add `api.pauseJob` → POST `/pause`. Do not send pause through `cancelJob`.

| Displayed job | Control | Copy |
| -- | -- | -- |
| processing, queued/running, both flags false | show **Pause Grouping and Ranking** and existing Cancel | existing `current_step` / progress |
| queued/running, `pause_requested` or pause mutation pending | hide Pause | `Pause requested. FramePilot will stop after a safe checkpoint.` |
| queued/running, `cancellation_requested` | hide Pause; existing Cancel pending copy | unchanged cancel pending |
| `paused` | hide Pause/Cancel; enable **Run Grouping and Ranking** (`POST /process`, not `/retry`) | paused recovery: stopped at a safe checkpoint; partial groups were cleared; run again when ready; originals unchanged |
| import / export / other, or terminal complete/failed/cancelled | no pause control | unchanged |

`canPauseProcessing(job, isPausePending)` is true iff the job exists, `job_type === "processing"`, status is `queued` or `running`, `pause_requested` is false, `cancellation_requested` is false, and `isPausePending` is false. `canCancelProcessing` is false when `pause_requested`. `processingJobHasReviewableResults("paused")` is false. Poll 1000ms while queued/running, including pause-pending. Once `paused`, `isProcessing` is false so Run is enabled (label stays “Run Grouping and Ranking”, not Retry).

**Docs:** replace “pause/resume of in-flight grouping is not implemented” in `docs/v2_known_limitations.md` (+ zh) and the S9.01 CHANGELOG Unreleased bullet. Document the pause route in `docs/api.md` (+ zh): cooperative, distinct flag, `paused` finalize, groups cleared, resume via `POST /process`. Short architecture note if that page still implies pause is absent. CHANGELOG Unreleased: new S9.02 subsection. No `APP_VERSION` bump.

**Phase 7 plan (implementation commit only):** tick J7.07 `[x]` with note: `2026-09-05: S9.02 / #161; cooperative pause_requested; worker exits without cancelled finalize; resume is POST /process clear-and-rerun; not in-place.` Same on zh. Do not untick J7.01–J7.06.

**This plan (implementation commit only):** tick §3 S9.02 `[x]` (en+zh). Do not tick S9.03–S9.13.

**Files:** `apps/api/app/models/entities.py` (`pause_requested`); `apps/api/app/db/session.py` (`_ensure_processing_job_columns`); `apps/api/app/schemas/api.py` (`JobRead`); `apps/api/app/api/routes.py` (pause endpoint, `_job_read`); `apps/api/app/services/processing.py` (request helper, checkpoints, pause finalize, reclaim); `apps/api/app/services/jobs.py` (`paused` in `TERMINAL_JOB_STATUSES` only); `apps/api/tests/test_import_process_export_api.py`; `apps/api/tests/test_job_reliability.py`; `apps/api/tests/test_job_processing_reclaim.py`; `apps/api/tests/test_job_checkpoint.py`; `apps/web/src/lib/api.ts` (`pauseJob`, status union, `pause_requested`); `apps/web/src/lib/processingProgress.ts` (+ tests); `apps/web/src/components/ProcessingPanel.tsx`; `tests/e2e/local-workflow.spec.ts` mocked pause; `docs/api.md`, `docs/v2_known_limitations.md`, architecture if it still denies pause, CHANGELOG Unreleased (+ zh); Phase 7 plan (+ zh) J7.07 tick; this plan (+ zh) §3 S9.02 tick.

**Tests first:** queued/running processing pause → 202, `pause_requested` true, `cancellation_requested` false, `status` unchanged, originals untouched. Worker observes pause at a ranking or post-grouping checkpoint → job `paused` not `cancelled`/`failed`; groups empty; `processed_images == 0`; originals unchanged; `user_status` / `star_rating` preserved. Terminal pause → 200 no-op. Interrupted pause → 200, `paused`, groups empty. Import/export pause → 422. After `paused`, `POST /process` creates a new job (not 409 / not reuse paused id). Reclaim interrupted + `pause_requested` → `paused`, not queued, not cancelled. Cancel tests stay green (cancel wins if both flags). `canPauseProcessing` / pending copy / `processingJobHasReviewableResults("paused")` false. Mocked E2E: Pause visible; POST pause; status Paused; Run enabled. Existing import/processing/export cancel tests stay green.

**Non-goals:** in-place continue-hash-mid-batch; keeping half-built groups; export or import pause; desktop quit-and-pause (quit stays cancel); expanding `/retry`; S9.01 or S9.03–S9.13; `APP_VERSION`; signing.

### S9.03 — AVIF

**Hole (live tree):** `.avif` is not in `SUPPORTED_EXTENSIONS` (`apps/api/app/services/importing.py`) or `STORED_IMAGE_EXTENSIONS` (`apps/api/app/services/exporting.py`). `ensure_heif_opener()` calls only `pillow_heif.register_heif_opener()` and its docstring says it does not register AVIF (`apps/api/app/image/heif_support.py`). Live `pillow-heif` 1.6.0 dropped AVIF: `register_heif_opener` registers `.heic`/`.heif`/… as format `"HEIF"` and `_is_supported_heif` rejects `avif`/`avis` brands. `register_avif_opener` does not exist. The HEIF wheel ships libheif/libde265/libx265, not an AV1 codec. `test_supported_extensions_include_heic_not_avif` and `test_heif_opener_does_not_claim_avif` encode that skip. ImportPanel `IMPORT_IMAGE_ACCEPT` / `IMPORT_FORMAT_COPY` and desktop `IMAGE_EXTENSIONS` omit avif. PyInstaller lists `PIL.JpegImagePlugin` / `PngImagePlugin` / `WebPImagePlugin` plus `pillow_heif`, not `PIL.AvifImagePlugin`. Docs say “AVIF is not accepted”. Pillow 12 already ships `PIL.AvifImagePlugin` + `_avif` and auto-registers `.avif` as format `"AVIF"` when `_avif` is present.

**Identity:** Mirror HEIC still preview, not RAW. Add **only** `.avif` (not `.avifs` sequences) to `SUPPORTED_EXTENSIONS` and `STORED_IMAGE_EXTENSIONS`. Copy original AVIF bytes into `{root_path}/originals/` unchanged. Decode with **Pillow’s native `AvifImagePlugin`** via the existing `Image.open` / `ImageOps.exif_transpose` / `.convert("RGB")` path. Thumbnails and previews stay **WebP**. Score/group on that RGB. Export ZIP/folder ships the **original AVIF bytes** (`ZIP_STORED`). Primary still only. HDR/gain-map: decode whatever primary RGB Pillow gives; do not implement tone mapping. **Do not** make the HEIF opener claim `.avif`. **Do not** add `pillow-avif-plugin`. **Do not** call a missing `register_avif_opener`. **Do not** bump `pillow-heif` for AVIF. Keep `ensure_heif_opener()` for HEIC/HEIF. Missing `_avif` in a wheel is a fail, not a skip.

**UI:** `ImportPanel` `accept` adds `image/avif,.avif`. Format copy names AVIF next to JPEG/PNG/WebP/HEIC/HEIF; RAW stays skipped. Update empty-state / processing strings that currently say “JPEG, PNG, WebP, or HEIC/HEIF” (`shellCopy.ts`, `processingProgress.ts`). Desktop `apps/desktop/src/lib/nativeFs.ts` `IMAGE_EXTENSIONS` adds `"avif"`. Path-import still uses the API list.

**Packaging:** `framepilot-api.spec` hiddenimports add `PIL.AvifImagePlugin` and `_avif` (same family as WebP). Keep pillow-heif collect for HEIC. Frozen sidecar smoke: generate a tiny AVIF in-process and path-import it through the frozen binary (keep the existing HEIC smoke). Stay under the 400 MB unpacked D4.06 threshold. Do not sign.

**Docs (implementation commit):** living pages that currently deny AVIF must name still AVIF: `docs/api.md`, `docs/architecture.md`, `docs/v2_known_limitations.md` (Supported File Formats; remove AVIF from Deferred), `README.md`, `docs/desktop_user_guide.md` (+ zh). CHANGELOG Unreleased: new S9.03 subsection. No `APP_VERSION` bump. Do not claim RAW, XMP, gain-map HDR, `.avifs`, or signed builds.

**This plan (implementation commit only):** tick §3 S9.03 `[x]` (en+zh). Do not tick S9.04–S9.13.

**Files:** `apps/api/app/services/importing.py`; `apps/api/app/services/exporting.py`; `apps/api/tests/heic_helpers.py` or a tiny `tiny_avif_bytes()` helper; `apps/api/tests/test_heif_support.py`; `apps/api/tests/test_import_process_export_api.py`; `apps/api/tests/test_import_from_paths.py`; `apps/api/tests/test_import_path_expansion.py`; `apps/api/tests/test_path_import_process_export_workflow.py`; `apps/api/tests/test_export_hardening.py`; `apps/web/src/components/ImportPanel.tsx` (+ test); `apps/web/src/lib/shellCopy.ts` (+ test); `apps/web/src/lib/processingProgress.ts` (+ test); `apps/desktop/src/lib/nativeFs.ts` (+ test); `packaging/pyinstaller/framepilot-api.spec`; `scripts/sidecar-smoke.sh`; docs listed above + CHANGELOG Unreleased (+ zh); this plan (+ zh) §3 S9.03 tick.

**Tests first:** invert `test_supported_extensions_include_heic_not_avif` so `.avif` is in `SUPPORTED_EXTENSIONS`. Keep `test_heif_opener_does_not_claim_avif` (`.avif` is `"AVIF"`, not `"HEIF"`). Generate tiny AVIF in-process with Pillow `Image.save(..., format="AVIF")` — no camera files in git. Multipart and from-paths: valid tiny AVIF copies into `originals/`, WebP derivatives, source size/mtime/bytes unchanged; RAW still skipped. Garbage `.avif` (`b"not-a-real-avif"`) is a failed import item after copy, not an unsupported-extension skip. Path-import + process + CSV/ZIP/folder: ZIP member is original AVIF bytes with `ZIP_STORED`. ImportPanel accept + copy; desktop picker extensions include `avif`. Existing JPEG/HEIC/RAW-skip tests stay green.

**Non-goals:** RAW; XMP; gain-map HDR; `.avifs` sequences; Live Photo `.mov`; new decoder packages; `APP_VERSION`; signing; S9.04–S9.13.

### S9.04 — RAW embedded preview

**Hole (live tree):** `.arw` / `.cr3` / `.dng` / `.nef` live only in `PLANNED_RAW_EXTENSIONS`, not in `SUPPORTED_EXTENSIONS` (`apps/api/app/services/importing.py`) or `STORED_IMAGE_EXTENSIONS` (`apps/api/app/services/exporting.py`). `unsupported_image_reason` returns `"RAW files are not supported yet; import JPEG, PNG, or WebP files for this release"`. `expand_import_paths` and `register_import_file` skip by extension **before copy**. Derivative paths (`process_registered_import_photo`, `import_image_file`, `ensure_photo_derivatives`) call `Image.open` on the copied original — Pillow cannot decode RAW. No `rawpy` / LibRaw in `apps/api/pyproject.toml`. PyInstaller lists JPEG/PNG/WebP/AVIF plugins plus `pillow_heif`, not `rawpy`. Sidecar smoke covers HEIC and AVIF only. ImportPanel `IMPORT_IMAGE_ACCEPT` / `IMPORT_FORMAT_COPY` and desktop `IMAGE_EXTENSIONS` omit RAW; copy says RAW is skipped. Tests encode the skip: `test_import_accepts_heic_and_still_skips_raw`, `test_import_accepts_avif_and_still_skips_raw`, `test_import_from_paths_accepts_avif_and_still_skips_raw`, `test_expand_includes_avif_and_still_skips_raw`, `test_expand_nested_jpegs_and_skips` (`frame.dng` / `b"not-raw"` never copied). Docs (`docs/api.md`, `docs/architecture.md`, `docs/v2_known_limitations.md` Deferred Formats, README, desktop user guide, `docs/v2_algorithm_strategy.md`) still say RAW is skipped. Known limitations document LGPL libheif, not LibRaw.

**Identity:** Mirror HEIC still preview’s copy-and-WebP path, **not** a RAW developer. Add **only** `.arw`, `.cr3`, `.dng`, `.nef` to `SUPPORTED_EXTENSIONS` and `STORED_IMAGE_EXTENSIONS`. Rename `PLANNED_RAW_EXTENSIONS` → `RAW_EXTENSIONS` (same four). Copy original RAW bytes into `{root_path}/originals/` unchanged. Decode with **`rawpy.extract_thumb()`** (LibRaw embedded preview) into a Pillow `Image`, then the existing `ImageOps.exif_transpose` / `.convert("RGB")` path. JPEG thumbs: `Image.open(BytesIO(thumb.data))`. BITMAP thumbs: `Image.fromarray(thumb.data)`. Thumbnails and previews stay **WebP**. Score/group on that **preview RGB** (not a demosaiced CFA). Export ZIP/folder ships the **original RAW bytes** (`ZIP_STORED`). Metadata comes from the preview image EXIF when present; do not parse RAW maker notes; do not write XMP.

**Decoder:** add `rawpy` to `apps/api/pyproject.toml` (MIT wrapper; wheels ship LibRaw). Choose a version with CPython 3.11 wheels for manylinux, macOS, and win_amd64. New `apps/api/app/image/raw_preview.py` with `extract_raw_preview_image(path) -> Image.Image`. Call **`extract_thumb` only**. **Do not** call `raw.postprocess`, `raw.raw_image`, or any demosaic. Map `rawpy.LibRawNoThumbnailError`, `rawpy.LibRawUnsupportedThumbnailError`, and LibRaw open failures to “no preview”. **Do not** `Image.open` the RAW file. **Do not** send RAW through `ensure_heif_opener()` / `AvifImagePlugin`. Missing `rawpy` / bundled LibRaw is a **fail**, not a skip (same family as missing Pillow `_avif`).

**Skip vs fail:** No embedded preview → **skip** with an explicit local reason, **not** a failed Photo after copy (that path is garbage HEIC/AVIF). No Photo row. No leftover copy under `originals/`. User source bytes/mtime/size unchanged. Locked reason (helper; replace the old “not supported yet” string):

`RAW file has no embedded preview; FramePilot does not demosaic`

`expand_import_paths` probes RAW sources **read-only** and puts no-preview files in `skipped` before copy. `register_import_file` / `import_image_file` defense-in-depth: if a RAW copy has no extractable thumb, `_cleanup_paths` that copy and raise the same reason (multipart lands in `skipped[]`). `process_registered_import_photo` and `ensure_photo_derivatives` must use the extract helper for `RAW_EXTENSIONS` so retry/reclaim can rebuild WebP from the copied original.

**UI:** `ImportPanel` `accept` adds `.dng,.arw,.cr3,.nef` (and matching `image/x-adobe-dng` / `image/x-sony-arw` / `image/x-canon-cr3` / `image/x-nikon-nef` if the existing accept style includes MIME). Format copy names RAW with an embedded preview next to JPEG/PNG/WebP/HEIC/HEIF/AVIF; RAW without a preview is skipped. Update empty-state / processing strings (`shellCopy.ts`, `processingProgress.ts`). Desktop `apps/desktop/src/lib/nativeFs.ts` `IMAGE_EXTENSIONS` adds `"dng"`, `"arw"`, `"cr3"`, `"nef"`. Path-import still uses the API list.

**Packaging:** `framepilot-api.spec` hiddenimports add `rawpy`; add `packaging/pyinstaller/hooks/hook-rawpy.py` mirroring `hook-pillow_heif.py` (`collect_all` + `collect_dynamic_libs`). Keep pillow-heif / AVIF collects. Frozen sidecar smoke: generate a tiny DNG **in-process** with an embedded JPEG preview and path-import it through the frozen binary (keep HEIC and AVIF smokes). Stay under the 400 MB unpacked D4.06 threshold. Do not sign.

**License (implementation commit):** document like libheif in `docs/v2_known_limitations.md` (+ zh): `rawpy` is MIT; its wheels ship **LGPL-2.1 / CDDL** LibRaw inside the API/sidecar runtime. FramePilot does not vendor LibRaw source into this MIT tree. CHANGELOG Unreleased: new S9.04 subsection. No `APP_VERSION` bump.

**Docs (implementation commit):** living pages that currently deny RAW must name embedded-preview import: `docs/api.md`, `docs/architecture.md`, `docs/v2_known_limitations.md` (Supported File Formats; full RAW develop stays Deferred), `README.md`, `docs/desktop_user_guide.md`, `docs/v2_algorithm_strategy.md` (+ zh). Do not claim demosaic, XMP, extra RAW extensions, or signed builds. Scoring/grouping use the embedded preview RGB.

**This plan (implementation commit only):** tick §3 S9.04 `[x]` (en+zh). Do not tick S9.05–S9.13.

**Files:** `apps/api/pyproject.toml`; `apps/api/app/image/raw_preview.py` (new); `apps/api/app/services/importing.py`; `apps/api/app/services/exporting.py`; `apps/api/tests/raw_helpers.py` (new, `tiny_dng_bytes`); `apps/api/tests/test_raw_preview.py` (new) or extend `test_heif_support.py`; `apps/api/tests/test_import_process_export_api.py`; `apps/api/tests/test_import_from_paths.py`; `apps/api/tests/test_import_path_expansion.py`; `apps/api/tests/test_path_import_process_export_workflow.py`; `apps/api/tests/test_export_hardening.py`; `apps/web/src/components/ImportPanel.tsx` (+ test); `apps/web/src/lib/shellCopy.ts` (+ test); `apps/web/src/lib/processingProgress.ts` (+ test); `apps/desktop/src/lib/nativeFs.ts` (+ test); `packaging/pyinstaller/framepilot-api.spec`; `packaging/pyinstaller/hooks/hook-rawpy.py`; `scripts/sidecar-smoke.sh`; docs listed above + CHANGELOG Unreleased (+ zh); this plan (+ zh) §3 S9.04 tick.

**Tests first:** invert the RAW skip tests so `.arw/.cr3/.dng/.nef` are in `SUPPORTED_EXTENSIONS`. Generate tiny DNG **in-process** with an embedded JPEG preview (`tiny_dng_bytes` via stdlib + Pillow; enrich with a tiny CFA + `DNGVersion` until `rawpy.extract_thumb` succeeds). **No camera files in git.** Unit: `extract_raw_preview_image` returns RGB of the expected size; `raw.postprocess` is not called. Multipart and from-paths: valid tiny DNG copies into `originals/`, WebP derivatives, source size/mtime/bytes unchanged. Same payload saved as `.arw`/`.cr3`/`.nef` either imports (if LibRaw identifies by content) or, if LibRaw rejects that extension on the synthetic DNG, still belongs to `SUPPORTED_EXTENSIONS` while garbage bytes skip. Garbage `.dng` (`b"not-a-real-raw"`) and a DNG with no preview IFD are **skipped** with the no-preview reason, **not** `processing_state=failed` after copy; `originals/frame.dng` must not exist. Path-import + process + CSV/ZIP/folder: ZIP member is original DNG bytes with `ZIP_STORED`; camera-card source unchanged. ImportPanel accept + copy; desktop picker extensions include `dng`/`arw`/`cr3`/`nef`. Existing JPEG/HEIC/AVIF tests stay green.

**Non-goals:** full demosaic / `postprocess`; XMP; extra RAW extensions (`.cr2`, `.raf`, `.orf`, `.rw2`, …); camera fixtures in git; vendoring LibRaw source; `APP_VERSION`; signing; S9.05–S9.13.

### S9.05 — XMP

**Hole (live tree):** `ExportCreate` only has `mode` (`csv`/`folder`/`zip`) and `statuses` (`apps/api/app/schemas/api.py`). `create_export_endpoint` / `run_export_job` never accept or persist an XMP flag (`apps/api/app/api/routes.py`). `copy_selected_files` / `zip_selected_files` copy original bytes only; no `.xmp` members (`apps/api/app/services/exporting.py`). `ExportRecord` / `ExportRead` have no `include_xmp`. `ExportPanel` POSTs `{ mode, statuses }` with no checkbox (`apps/web/src/components/ExportPanel.tsx`, `api.exportSelection`). Path-import ZIP tests assert `namelist() == ["hero.jpg"]`. Docs say XMP is planned but not implemented (`docs/api.md`, `docs/export_interoperability.md`, `docs/v2_known_limitations.md` Export Limitations, README). No `xmp` tests. `_ensure_export_record_columns` runs only from already-applied migrations 1 and 3 (`CURRENT_SCHEMA_VERSION` is 5); a new export column will not appear on existing v5 DBs unless a new migration runs.

**Identity:** Optional **`include_xmp: bool = False`** on `ExportCreate` (omitted JSON key = false). **Not** a fourth export mode. Modes stay `{csv, folder, zip}`. Persist `include_xmp` BOOLEAN NOT NULL DEFAULT 0 on `ExportRecord`. Expose it on `ExportRead` and web `ExportRecord`. `create_export_endpoint` stores `payload.include_xmp` on the record. `run_export_job` reads `record.include_xmp`. `copy_selected_files` / `zip_selected_files` take `include_xmp: bool = False` so unit tests can pass it. Sidecars are derived export artifacts only.

**Schema:** `_ensure_export_record_columns` adds `include_xmp INTEGER NOT NULL DEFAULT 0`. Bump `CURRENT_SCHEMA_VERSION` to **6** with `_migrate_to_6` that calls that ensure (same pattern as S9.02 `_migrate_to_5`). Also call `_ensure_export_record_columns` from `init_db` next to `_ensure_processing_job_columns` so leftover DBs still get the ALTER. `test_init_db_adds_missing_export_record_columns_to_existing_sqlite_table` must assert `include_xmp`.

**Where:** Write `.xmp` **only** under the project export root (`{root_path}/exports/...`). Folder: `{exported_filename}.xmp` next to each copied file inside `exports/folders/selected-{id}/`. ZIP: include the same `{exported_filename}.xmp` members inside `exports/zip/selected-{id}.zip` (XML uses `ZIP_DEFLATED`; images stay `ZIP_STORED`). CSV: `include_xmp` is accepted and stored; **write no `.xmp` files** (CSV already has `status` / `star_rating`; extra files beside the CSV would leak on cancel because `remove_partial_export` only deletes `output_path`). **Never** write into `{root_path}/originals/`, beside `original_path` (camera card), or into image bytes (no embedded XMP packets).

**Filename:** `{exported_file.name}.xmp` (append `.xmp` to the unique exported basename, e.g. `hero.jpg.xmp` / `hero-1.jpg.xmp`). Do **not** replace the image extension with `.xmp` (`hero.xmp`): JPEG+RAW pairs share a stem and would collide. Add the sidecar name to ZIP `used_names`. Document that Lightroom Classic auto-sidecar discovery often looks for `{stem}.xmp`; this slice guarantees unambiguous pairing and a Lightroom-readable **field**, not auto-discovery. Do not claim a tested Lightroom/Capture One GUI round-trip.

**Packet (stdlib only):** New `apps/api/app/services/xmp_sidecar.py`. UTF-8 RDF/XML (`xml.etree.ElementTree` or equivalent stdlib; escape XML). Wrapper: `x:xmpmeta` / `rdf:RDF` / `rdf:Description`. **Do not** add `python-xmp-toolkit` / libxmp / ExifTool. Locked mapping (do **not** use `xmp:Rating = -1` for Reject — that would drop stars):

| `user_status` | `xmp:Rating` | `xmp:Label` | `dc:subject` (`rdf:Bag` / `rdf:li`) |
| -- | -- | -- | -- |
| Pick | `star_rating` clamped 0–5 | Green | Pick |
| Maybe | `star_rating` clamped 0–5 | Yellow | Maybe |
| Reject | `star_rating` clamped 0–5 | Red | Reject |
| Unreviewed | `star_rating` clamped 0–5 | omit `xmp:Label` | Unreviewed |

Also write `dc:title` = exported filename and `dc:identifier` = project photo id. Namespaces: `x` `adobe:ns:meta/`, `xmp` `http://ns.adobe.com/xap/1.0/`, `dc` `http://purl.org/dc/elements/1.1/`, `rdf` `http://www.w3.org/1999/02/22-rdf-syntax-ns#`. `xmp:Rating` is the documented Lightroom-compatible rating field (#165). `xmp:Label` uses Adobe color-label strings so Pick/Maybe/Reject stay inspectable without clobbering stars. Do not copy camera EXIF, GPS, or scores into the sidecar.

**Checkpoints:** write the sidecar in the **same per-photo loop** as the copy/zip member, then the existing `progress_callback`. Cancel/fail still `remove_partial_export` on `output_path` (folder rmtree and zip unlink already drop sidecars). Originals never modified or deleted.

**UI:** `ExportPanel` checkbox **Write XMP sidecars**, default **unchecked**, React state only (**do not** persist in `localStorage`; export status preference stays separate). Disabled with other export controls while running. Helper: sidecars go next to folder copies and inside ZIP; never beside originals; CSV already includes status and stars. `api.exportSelection(projectId, mode, statuses, includeXmp = false)`. Unchecked POST omits the flag or sends `false` (both must default off). History may show `XMP` when `include_xmp` is true. `ExportRecord` type and ExportPanel test mocks gain `include_xmp?: boolean`. Mocked E2E export POST may send `include_xmp`.

**Docs (implementation commit):** living pages that currently say XMP is not implemented must describe this optional export-directory sidecar: `docs/export_interoperability.md`, `docs/api.md`, `docs/v2_known_limitations.md` (Export Limitations; XMP writes stay out of import/`originals/`), `docs/architecture.md`, `README.md`, `docs/desktop_user_guide.md` (+ zh). CHANGELOG Unreleased: new S9.05 subsection. No `APP_VERSION` bump. Do not claim Lightroom/Capture One GUI certification, embedded XMP, or write-back next to camera files.

**This plan (implementation commit only):** tick §3 S9.05 `[x]` (en+zh). Do not tick S9.06–S9.13.

**Files:** `apps/api/app/services/xmp_sidecar.py` (new); `apps/api/app/services/exporting.py`; `apps/api/app/schemas/api.py` (`ExportCreate`/`ExportRead`); `apps/api/app/models/entities.py` (`ExportRecord.include_xmp`); `apps/api/app/db/session.py` (`_ensure_export_record_columns`, `init_db`); `apps/api/app/db/migrations.py` (`CURRENT_SCHEMA_VERSION` 6, `_migrate_to_6`); `apps/api/app/api/routes.py` (`create_export_endpoint`, `run_export_job`); `apps/api/tests/test_xmp_sidecar.py` (new) or extend `test_ranking_export.py`; `apps/api/tests/test_db_session.py`; `apps/api/tests/test_import_process_export_api.py`; `apps/api/tests/test_path_import_process_export_workflow.py`; `apps/api/tests/test_export_hardening.py`; `apps/web/src/lib/api.ts`; `apps/web/src/components/ExportPanel.tsx` (+ test); `tests/e2e/local-workflow.spec.ts` mocked `include_xmp`; docs listed above + CHANGELOG Unreleased (+ zh); this plan (+ zh) §3 S9.05 tick.

**Tests first:** omit `include_xmp` and `include_xmp: false` → no `.xmp` under the project root; ZIP namelist stays images only; originals (project copy **and** camera-card `original_path`) size/mtime/bytes unchanged. Folder + `include_xmp: true` writes `{name}.xmp` next to each copy; packet maps Pick/Maybe/Reject/Unreviewed and stars 0 and 5 as the table; no `.xmp` under `originals/` or the camera-card directory. ZIP + `include_xmp: true` includes matching `.xmp` members; image member bytes equal the original; originals unchanged. CSV + `include_xmp: true` writes no `.xmp` files; CSV still has status/stars; originals unchanged. Duplicate filenames get matching `{unique-name}.xmp`. Schema v5 → v6 adds `include_xmp`. Cancel of a live folder/zip with `include_xmp: true` removes the partial artifact under export root and does not touch originals. ExportPanel checkbox default off; checked POST sends `include_xmp: true`. Existing csv/zip/folder/cancel tests stay green.

**Non-goals:** writing next to `originals/` or the camera card; embedding XMP in image bytes; a fourth `mode="xmp"`; `python-xmp-toolkit` / ExifTool / libxmp; Lightroom/Capture One GUI round-trip CI; `xmp:Rating = -1` for Reject; write-back on import/review; S9.06–S9.13; `APP_VERSION`; signing.

### S9.06 — Tray

Optional tray + job progress. No new `fs:`/`shell:` capabilities. Tick D3.06.

### S9.07 — Detached preview

Second WebView + shared selection. Degrade to in-shell preview if WebView fails.

### S9.08 — Concurrency knobs

Settings 1–4 import workers, default 1. Processing stays one job per project.

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

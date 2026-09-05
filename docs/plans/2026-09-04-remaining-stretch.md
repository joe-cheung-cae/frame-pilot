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
- [x] S9.09 Change data directory — [#170](https://github.com/joe-cheung-cae/frame-pilot/issues/170)
- [x] S9.10 Optional check for updates — [#167](https://github.com/joe-cheung-cae/frame-pilot/issues/167)
- [x] S9.11 Signing-ready CI — [#171](https://github.com/joe-cheung-cae/frame-pilot/issues/171)
- [x] S9.12 macOS DMG GUI lifecycle QA — [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172)
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

**Hole (live tree):** SettingsPanel shows a read-only data directory from `GET /api/meta` and says changing the location is not available (`apps/web/src/components/SettingsPanel.tsx`). D3.03 deferred change to 2.2. Rust `resolve_runtime_data_dir` uses absolute `FRAMEPILOT_DATA_DIR` else OS app-support / `.framepilot-desktop-dev` (`apps/desktop/src-tauri/src/data_dir.rs`); no pointer file. Sidecar `--data-dir` is required. SQLite `framepilot.db` plus absolute `Project.root_path`, `Photo.original_path` / `project_copy_path` / `thumbnail_path` / `preview_path`, and `ExportRecord.output_path`. `Project.source_root_path` is the import folder (camera card / source). Import copies into `{root_path}/originals` and never modifies the source. D2.00 `POST /api/desktop/project-roots` + `register_root` is the authorize path; rejects `$HOME` / `/` / drive roots / current data_dir and its parents. `test_create_project_rejects_root_outside_allowlist` must stay green unchanged. #170: explicit user authorize; copy/move FramePilot data dir; rewrite stored project paths; never rewrite camera-card originals.

**Identity:** Desktop-only change of the FramePilot **app data directory** (db, logs, `app_settings.json`, `desktop_project_roots.json`, `{data_dir}/projects/...`). Not a project-root picker and not reference-in-place. Copy the current data-dir tree into an explicitly authorized destination; rewrite stored paths whose resolved prefix is the **old** data_dir; leave the old tree on disk (do not delete in this slice). **Never** open, copy, move, chmod, or rewrite files on a camera card or any path outside the old data_dir. No schema bump.

**Authorize:** Same D2.00 flow as project folders: native `pickDirectory` → `POST /api/desktop/project-roots` (existing 422s). Migrate only if the destination is already in `registered_roots()`. Reuse `register_root` / `is_blocked_allowlist_root`. Also reject the current data_dir, its parents, **children** of the current data_dir (nested copy), and the same path. Destination must exist, be a directory, and be empty. Do **not** set `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST`. Do **not** change `test_create_project_rejects_root_outside_allowlist`. After copy, drop the new data_dir from the copied `desktop_project_roots.json` (it is now the data dir; D2.00 would reject it).

**API:** Desktop-only `POST /api/desktop/data-dir` `{"path": "<abs>"}` (404 unless `FRAMEPILOT_DESKTOP=1`). 409 if any job is in `BLOCKING_JOB_STATUSES`. 422 if unregistered / blocked / nested / missing / nonempty. Copy the tree including SQLite `-wal`/`-shm`. Rewrite in the **destination** db only (old db and files stay byte-identical). Prefix-replace old_data_dir on `Project.root_path`, `Photo.original_path` / `project_copy_path` / `thumbnail_path` / `preview_path`, and `ExportRecord.output_path` **only when** the stored path is under the old data_dir. **Never** rewrite `Project.source_root_path`. Custom D2.00 project folders outside the old data_dir stay put (files not copied; `root_path` unchanged). 200 `{ "data_dir": "<new>" }`.

**Persist / restart:** Rust reads `{anchor}/data_dir.json` (`{"data_dir": "<abs>"}`) after env override and before default app-support / `.framepilot-desktop-dev`. Absolute `FRAMEPILOT_DATA_DIR` still wins. After API 200, Tauri writes the pointer at the **default anchor** (not inside the movable tree), updates `DesktopPaths`, and respawns the sidecar with the new `--data-dir`. Settings refetches `GET /api/meta`. No extra `fs:` / `shell:` capabilities.

**UI:** SettingsPanel, desktop shell + native FS only: **Change data directory** (pick → register → confirm → POST). Confirm copy: rewrite paths inside the current data directory; camera cards and other source folders are not moved or modified. Browser stays read-only. Keep **Open data folder**.

**This plan (implementation commit only):** tick §3 S9.09 `[x]` (en+zh). Do not tick S9.10–S9.13.

**Files:** `apps/api/app/services/data_dir.py` (new); `apps/api/app/api/routes.py`; `apps/api/app/schemas/api.py`; `apps/api/tests/test_data_dir_relocate.py` (new); `apps/desktop/src-tauri/src/data_dir.rs`; `apps/desktop/src-tauri/src/lib.rs`; `apps/web/src/lib/api.ts`; `apps/web/src/components/SettingsPanel.tsx` (+ test); `docs/api.md`, `docs/v2_known_limitations.md`, architecture, user guide, CHANGELOG Unreleased (+ zh). Do not rewrite `docs/desktop_development_plan.md` §2.2 as shipped (S9.13).

**Tests first:** register then POST copies db + managed project; rewritten `root_path` / photo copy / derivative paths live under the new data_dir; old data_dir files byte-identical; camera-card source size/mtime/bytes unchanged; `source_root_path` unchanged; custom D2.00 `root_path` outside the old data_dir unchanged; blocked / unregistered / nested / nonempty 422; no desktop env 404; blocking job 409; `test_create_project_rejects_root_outside_allowlist` unchanged; SettingsPanel shows Change on desktop only; pointer file makes next `resolve_data_dir` return the override; env override still wins.

**Non-goals:** deleting the old data dir; rewriting §2.2 as done; check for updates (S9.10); signing; `APP_VERSION`; extra `fs:`/`shell:` capabilities; Redis/Celery; S9.10–S9.13.

### S9.10 — Check for updates

Menu only. GitHub Releases. No launch network.

**Hole (live tree):** Help is Shortcuts + About only (`apps/desktop/src-tauri/src/menu.rs`). `Cargo.toml` has window-state, single-instance, dialog, opener — no updater plugin. `tauri.conf.json` has no `plugins.updater`. CSP `connect-src` is loopback only. Capabilities are `opener:allow-reveal-item-in-dir` only. `lib.rs` setup never networks except sidecar `/health`. Known limitations: **Auto-update is deferred**; users install new builds manually. `.github/workflows/desktop.yml` uploads unsigned NSIS/DMG artifacts and does not publish GitHub Release assets or Tauri `latest.json`. #167: menu click only; GitHub Releases query; no launch-time network; no telemetry; missing manifest = non-fatal no-op; unsigned builds must still launch.

**Identity:** Desktop-only **check**, not auto-install. Help → **Check for updates** (id `check-for-updates`, no accelerator). Native-owned like About; JS `menuRoutes` ignores it. Query GitHub Releases on that click only. Do **not** add `tauri-plugin-updater`, download-and-install, or `bundle.createUpdaterArtifacts` (signing / updater artifacts stay S9.11). Missing certs / pubkey / `TAURI_SIGNING_PRIVATE_KEY` must not prevent `Builder`/`run`. Originals are never read or uploaded. No telemetry, login, payment, or GitHub token.

**Network:** Rust helper thread, not WebView. Unauthenticated `GET https://api.github.com/repos/joe-cheung-cae/frame-pilot/releases/latest`. User-Agent `FramePilot/{CARGO_PKG_VERSION}`. Timeout ~10s. Small sync client (`ureq`). No launch / Ready / timer / Settings poll. A second click while in-flight is ignored. CSP unchanged. No extra `fs:` / `shell:` capabilities; do not add `opener:default`.

**Manifest:** The Releases JSON is the manifest (`tag_name` required; `html_url` optional). 404 / empty body / missing `tag_name` / unparseable version → missing manifest → **non-fatal no-op** (no panic, no blocking error; optional stderr). 403 / 429 / timeout / 5xx → non-fatal local dialog, not a crash. Do not require a Tauri `latest.json` asset in this slice.

**Compare:** Normalize `tag_name` and `CARGO_PKG_VERSION` (`2.1.0-desktop`): strip leading `v`, take MAJOR.MINOR.PATCH before `-`/`+`. Remote core > local → update available. Else up to date. Live latest tag `v2.0.0` is older than `2.1.0-desktop` → up to date. Do not bump `APP_VERSION`.

**UI:** Existing `tauri-plugin-dialog` message. Update available: current vs latest (releases URL as text). Up to date: current version. Browser/web has no item. Not SettingsPanel. This slice does not open a URL.

**This plan (implementation commit only):** tick §3 S9.10 `[x]` (en+zh). Do not tick S9.11–S9.13.

**Files:** `apps/desktop/src-tauri/src/updater.rs` (new); `apps/desktop/src-tauri/src/menu.rs`; `apps/desktop/src-tauri/src/lib.rs`; `apps/desktop/src-tauri/Cargo.toml` (+ lock for `ureq`); `apps/web/src/lib/menuRoutes.test.ts`; `docs/v2_known_limitations.md`, user guide, architecture, CHANGELOG Unreleased (+ zh). Do not rewrite `docs/desktop_development_plan.md` §2.2 / §5.4 / §5.6 as shipped (S9.13). Do not edit `desktop.yml` (S9.11).

**Tests first:** menu id present, no accelerator, not a reserved culling key; `check-for-updates` is native-owned in `menuRoutes.test.ts`; `lib.rs` setup does not call the check; 404/empty JSON → no-op enum, no panic; `v2.2.0` vs `2.1.0-desktop` → available; `v2.0.0` / `v2.1.0` vs `2.1.0-desktop` → current; timeout/403 do not panic; tests inject status/body (no live GitHub). `npm run verify` stays rust-free.

**Non-goals:** launch-time / periodic check; auto-download/install; `tauri-plugin-updater`; publishing `latest.json` or signing (S9.11); extra `fs:`/`shell:`/`opener:default`; telemetry; GitHub token; Settings toggle; `APP_VERSION`; rewriting §2.2 as done; S9.11–S9.13.

### S9.11 — Signing-ready CI

`desktop.yml` steps gated on secrets. Unsigned path remains green. Update `docs/desktop_signing.md` (+ zh) with secret names. No certs in git.

**Hole (live tree):** `.github/workflows/desktop.yml` header says **Unsigned builds only (signing is D4.05)**; `npx tauri build --bundles nsis|dmg` has no signing env; uploads `FramePilot-windows-nsis` / `FramePilot-macos-dmg` with `if-no-files-found: error`. `apps/desktop/src-tauri/tauri.conf.json` has identifier `com.framepilot.app`, NSIS `currentUser`, no `certificateThumbprint` / `signingIdentity` / notarization fields. `docs/desktop_signing.md` lists typical material as **examples only**, not exact GitHub secret names. `scripts/check-release-artifacts.sh` blocks zip/sqlite/photos but not `.pfx` / `.p12` / `.p8`. D4.05 shipped the runbook only. #171: wire Authenticode / notarization gated on secrets; missing secrets keep today’s unsigned upload; DoD is signing-ready, not a SmartScreen-clean public release; no certs in git; document exact secret names.

**Identity:** CI **signing-ready**, not a store release. Keep the existing `npx tauri build` path (do **not** switch to `tauri-apps/tauri-action`; do not raise `contents: write`; do not publish GitHub Releases or Tauri `latest.json`). When a platform’s **full** secret set is non-empty, sign that platform’s installer during the existing build step (Windows Authenticode on the NSIS `.exe`; macOS Developer ID + notary + staple on the `.app` / DMG). When any required secret for that platform is missing or empty, skip signing for that platform and upload the same unsigned artifact as today; the job stays **green**. If the full set is present and sign / notarize fails, the job is **red** (do not silently fall back to unsigned). Windows and macOS gate independently (`fail-fast: false` stays). Originals are never read or uploaded. No telemetry, login, payment, or bundled models.

**Secrets (locked GitHub Actions names):** Windows signs only when **both** `WINDOWS_CERTIFICATE` (base64 Authenticode `.pfx`) and `WINDOWS_CERTIFICATE_PASSWORD` are non-empty. macOS signs + notarizes only when **all** of `APPLE_CERTIFICATE` (base64 Developer ID Application `.p12`), `APPLE_CERTIFICATE_PASSWORD`, `APPLE_SIGNING_IDENTITY`, `APPLE_TEAM_ID`, `APPLE_API_ISSUER`, `APPLE_API_KEY` (App Store Connect Key ID), and `APPLE_API_KEY_CONTENT` (`.p8` file contents) are non-empty. `APPLE_API_KEY_PATH` is a runner temp path derived from `APPLE_API_KEY_CONTENT`, not a GitHub secret. Copy secrets into `env:` then test non-empty; never echo values. Do **not** export empty `APPLE_CERTIFICATE` (Tauri would try to import and fail). Do **not** add `APPLE_ID` / `APPLE_PASSWORD` / `KEYCHAIN_PASSWORD` / Azure Trusted Signing / `TAURI_SIGNING_PRIVATE_KEY` in this slice.

**Windows:** Full set present → decode PFX on the runner, import into `Cert:\CurrentUser\My`, derive thumbprint, `npx tauri build --bundles nsis` with a **local** `--config` overlay for `digestAlgorithm=sha256`, public DigiCert timestamp URL, and that thumbprint. Delete the decoded PFX before upload. Do **not** commit thumbprint or PFX. Either secret missing → current unsigned `npx tauri build --bundles nsis`.

**macOS:** Full set present → write `AuthKey_${APPLE_API_KEY}.p8` under `$RUNNER_TEMP`, export the APPLE_* env vars, `npx tauri build --bundles dmg` (Tauri imports the p12, signs, notarizes, staples). Delete p12 / p8 from the runner before upload. Any required secret missing → current unsigned `npx tauri build --bundles dmg` with those env vars unset.

**CI shape:** Keep `on:` (`workflow_dispatch` + push `main` path filters), matrix `windows-latest` / `macos-latest`, sidecar build + `npm run test:sidecar`, stage sidecar, existing artifact names. Do not launch the packaged GUI. Do not attach photos. `permissions.contents: read` stays. Header comment: signing-ready, gated on secrets, unsigned fallback must stay green.

**Docs:** Replace the “examples only” table in `docs/desktop_signing.md` (+ zh) with the exact names above (names and purpose only; never sample values). State: missing secrets → unsigned green; complete secrets → sign; sign failure with secrets present → red. Keep internal-tester unsigned guidance.

**Git hygiene:** Never commit `.pfx` / `.p12` / `.p8` / private keys / base64 cert blobs. Extend `scripts/check-release-artifacts.sh` to reject tracked `\.(pfx|p12|p8)$`. Add those globs to `.gitignore`.

**This plan (implementation commit only):** tick §3 S9.11 `[x]` (en+zh). Do not tick S9.12–S9.13.

**Files:** `.github/workflows/desktop.yml`; `docs/desktop_signing.md` (+ zh); `scripts/check-release-artifacts.sh`; `scripts/test-release-checks.sh`; `.gitignore`; `docs/v2_known_limitations.md`, README, CHANGELOG Unreleased (+ zh). Do not edit `verify.yml`. Do not bump `APP_VERSION`. Do not rewrite `docs/desktop_development_plan.md` §2.2 / §5.4 / §5.6 as shipped (S9.13). Do not commit certs.

**Tests first:** `scripts/test-release-checks.sh` asserts `desktop.yml` references the locked secret names; Windows import/sign and macOS notarize are gated on non-empty env (not unconditional); missing-secret path has no `exit 1`; empty `APPLE_CERTIFICATE` is not exported; `verify.yml` still has no codesign/notarize; `check:artifacts` rejects a tracked `.pfx` / `.p12` / `.p8`. `npm run verify` stays rust-free and does not run `desktop.yml`.

**Non-goals:** SmartScreen reputation / public store listing; Mac App Store; Azure / DigiCert cloud signing; `tauri-action` Release publish; `tauri-plugin-updater` / `createUpdaterArtifacts` / `TAURI_SIGNING_PRIVATE_KEY` / `latest.json`; Apple ID + app-specific password auth; launching packaged GUI; S9.12 macOS DMG GUI QA; S9.13 leftover docs; `APP_VERSION`; certs in git.

### S9.12 — macOS DMG QA

Follow `docs/desktop_testing.md`. No Mac → skip with timestamp, not pass.

**Hole (live tree):** Packaged macOS GUI lifecycle has no dated `[x]` evidence. [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144) closed Windows-only 2026-09-04; `develop_plan.md` §1.1 records macOS DMG as skip (no Mac host) and says skip is not a macOS pass. `docs/desktop_testing.md` has the lifecycle + install/uninstall matrix and a record template, but no S9.12 results section. `.github/workflows/desktop.yml` uploads `FramePilot-macos-dmg` and **does not** launch the packaged GUI (`verify.yml` is rust-free and also does not). This 需求拆解 host is Linux; a DMG cannot be mounted or launched here. #172: run packaged DMG GUI lifecycle on a Mac; if no Mac, record skip with an ISO-8601 timestamp and close as skip, not as a pass.

**Identity:** Docs-only QA record. Prefer a real macOS GUI pass of the packaged DMG. Skip is an allowed close-out when no Mac host exists, **if and only if** it is dated ISO-8601 and never labeled pass. Do not change production Rust / Python / TypeScript. Do not treat unsigned as signed. Gatekeeper warnings on unsigned DMGs are expected, not a fail. Originals never modified. No `APP_VERSION` bump.

**Mac pass path:** `uname -s` is Darwin (or an equivalent macOS GUI host with a display). Install CI artifact `FramePilot-macos-dmg` (Actions → `desktop` workflow; `workflow_dispatch` if this branch has no artifact) or local `npx tauri build --bundles dmg`. Then run `docs/desktop_testing.md` **manual GUI** rows only:

- Start (installed): window title `FramePilot`; sidecar loopback; `GET /health` → 200 with `version` + `service` (do not run uvicorn yourself)
- Quit clean (no active job): sidecar exits; no orphan uvicorn on that port
- Quit + import / Quit + processing / Quit + export: dialogs per `apps/desktop/README.md`; source originals size/mtime/bytes unchanged; cancelled processing clears partial groups; cancelled export fail-and-cleanup
- Sidecar crash: UI shows failure / unreachable API; restart recovers or documents retry; originals untouched
- Port in use: clear error; process must **not** listen on `0.0.0.0`
- Install / uninstall: app binary removed; **data directory may remain** (`~/Library/Application Support/FramePilot`)

Record per the matrix template: date / OS / `APP_VERSION` from `GET /health`, which rows `[x]` vs dated `[~]`, CI artifact run URL, originals unchanged. Import-quit may use `npm run generate:synthetic` into a throwaway folder **outside** the app data directory. Never camera files. Never commit photos, databases, or export trees.

**No-Mac skip path:** If the 开发 host is not Darwin (Linux, WSL, headless CI), do **not** mark any GUI row `[x]`. `await_user` **once** asking for a Mac host. If none is provided, record **skip** (not pass) with an ISO-8601 UTC timestamp. Skip may tick §3 S9.12 `[x]` because #172 allows skip-as-close-out; the living docs must still say skip ≠ pass. CI HTTP smoke / frozen sidecar / Playwright staying green does **not** convert a skip into a macOS GUI pass.

**Skip record (implementation commit):** Add a dated **S9.12 macOS DMG GUI results** subsection to `docs/desktop_testing.md` (+ zh) using the existing template; CHANGELOG Unreleased; one `docs/v2_known_limitations.md` (+ zh) bullet; comment on #172 with HEAD, `uname`, timestamp, and skip reason. Do **not** rewrite `docs/desktop_development_plan.md` §2.2 as shipped (S9.13). A skip must **not** tick “Windows and macOS both install and run from standard installer packages”.

**This plan (implementation commit only):** tick §3 S9.12 `[x]` (en+zh). Do not tick S9.13. Commit subject `docs: macOS DMG GUI lifecycle QA`.

**Files:** `docs/desktop_testing.md` (+ zh); `docs/v2_known_limitations.md` (+ zh); CHANGELOG Unreleased (+ zh). Optional pointer note in `develop_plan.md` §1.1 that S9.12 recorded skip or pass — do not claim a Mac pass on skip. Do not edit `.github/workflows/desktop.yml` or `verify.yml`. Do not change production app code.

**Tests first:** No new automated GUI test. `npm run verify` stays rust-free and does not launch a DMG. On skip, do not invent Mac-only pytest/Playwright. Existing desktop HTTP smoke / sidecar tests stay green.

**Non-goals:** inventing `[x]` without a real window; launching packaged GUI from CI; signing/notarize as this slice; Mac App Store / Gatekeeper-clean claim; Windows NSIS re-run (#144 already closed); S9.13 leftover docs; `APP_VERSION`; camera files; bundled models; extra `fs:`/`shell:` capabilities.

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

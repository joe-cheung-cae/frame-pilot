# Desktop Review-Fix Requirements Breakdown

Handoff stage: `需求拆解`  
Date: 2026-08-20T09:30:00+08:00  
Branch for this pipeline: `feature/desktop-packaging` (HEAD `7e545f80ad9205cc3a7ab67bf1683ab583743f24`)  
Parent issue: [joe-cheung-cae/frame-pilot#30](https://github.com/joe-cheung-cae/frame-pilot/issues/30)  
Scope fence: **sidecar lifecycle + quit handshake review-fix only** — confirmed findings F001–F006 from the 2026-08-20T08:37:35+08:00 full code review. Do not start desktop Phases 2–5. Do not redo D1.01–D1.09 product work. Do not retick §5.1 Phase 1 boxes (already `[x]`).

This document is the implementation contract for later stages (`评审` → `归档` → `开发` → `测试` → `上线`). It does not implement production Rust / TypeScript / Python.

**Not this document:**

- Desktop Phase 0 (D0.00–D0.09) — closed `上线` 2026-08-19 with GO
- Desktop Phase 1 product work (D1.01–D1.09) — closed `上线` 2026-08-19 with GO on `feature/desktop-packaging`; boxes stay `[x]`
- Desktop Phases 2–5 (D2.00–D5.05): registered project roots, native pickers, menus, installers, `APP_VERSION` bump to `2.1.0-desktop`
- A second patch for F006 (same implementation as F001)

**Sources of truth (read in this order when implementing):**

1. `AGENTS.md` + `develop_plan.md` (local-first, original-file safety, English, tests)
2. `docs/plans/2026-08-18-desktop-packaging.md` (locked decisions; §5.1 Phase 1 already `[x]`; D1.09 quit semantics; wins on technical conflict)
3. GitHub issue bodies: [joe-cheung-cae/frame-pilot#30](https://github.com/joe-cheung-cae/frame-pilot/issues/30) and sub-issues `#33` `#35` `#36` `#34` `#31` `#32` (acceptance copied below)
4. This file (pipeline-bounded contract for the review-fix on `feature/desktop-packaging`)
5. Live `apps/desktop/src-tauri/src/lib.rs`, `apps/desktop/src-tauri/src/sidecar.rs`, `apps/desktop/src-tauri/Cargo.toml` (crate `framepilot-desktop`, lib `framepilot_desktop_lib`)
6. `docs/v2_known_limitations.md` (cooperative import cancel; quit-anyway / SIGTERM is `failed` + retryable)
7. `docs/desktop_feasibility_notes.md` (Phase 1 GO; `npm run verify` rust-free)
8. `docs/desktop_goal_mode.md` (loop rules; tracker still lives in the implementation plan §5.1)

Conflict rule from the implementation plan: on any technical conflict that plan wins, and the product plan must be edited in the same commit that resolves the conflict. The product plan never introduces a new task id. Review-fix work does not add D-ids and does not retick Phase 1.

---

## 1. Goal

Close the six confirmed sidecar-lifecycle and quit-handshake defects from [joe-cheung-cae/frame-pilot#30](https://github.com/joe-cheung-cae/frame-pilot/issues/30) on `feature/desktop-packaging` at `7e545f80`, without merging, without opening a PR, without closing GitHub issues, and without starting Phase 2.

The Phase 1 shell is supposed to keep original photos untouched, hold SQLite under the OS app-support data dir, POST `/cancel` for an in-flight **import** only on explicit user choice, then SIGTERM the sidecar. The confirmed defects break that contract:

1. A failed sidecar start can leave a hidden API bound to the allocated loopback port and data dir — [joe-cheung-cae/frame-pilot#33](https://github.com/joe-cheung-cae/frame-pilot/issues/33) F001 / [joe-cheung-cae/frame-pilot#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32) F006 (**one implementation**).
2. Shutdown can race a supervisor restart so a new sidecar outlives window destroy — [joe-cheung-cae/frame-pilot#35](https://github.com/joe-cheung-cae/frame-pilot/issues/35) F002.
3. Closing during an import never mounts Keep working / Quit and cancel import / Quit anyway (invalid JS) — [joe-cheung-cae/frame-pilot#36](https://github.com/joe-cheung-cae/frame-pilot/issues/36) F003, which makes [joe-cheung-cae/frame-pilot#34](https://github.com/joe-cheung-cae/frame-pilot/issues/34) F004 the live fallback (unconfirmed cancel). **F003 + F004 must land together.**
4. Cmd+Q / `ExitRequested` SIGTERMs the sidecar without the close dialog — [joe-cheung-cae/frame-pilot#31](https://github.com/joe-cheung-cae/frame-pilot/issues/31) F005. **`ExitRequested` needs `prevent_exit`.**

**Explicit coupling (do not split these):**

- **F001 == F006 one change.** [joe-cheung-cae/frame-pilot#33](https://github.com/joe-cheung-cae/frame-pilot/issues/33) and [joe-cheung-cae/frame-pilot#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32) are the same leak at `lib.rs` ready-line / missing-stdout drop. Close both with terminate-on-error plus shutdown-aware `store_child`. Do **not** write a second patch for F006.
- **F003 is import-only.** Processing `extra_button` is empty and that generated script still parses. Do not treat a green processing-dialog substring test as coverage for import.
- **F003 + F004 must land together.** Today F003 makes F004 the live import-close path (2s timeout then `unwrap_or(CloseChoice::CancelAndQuit)`).
- **`ExitRequested` needs `prevent_exit`.** `app.run` matches `Exit | ExitRequested` and always `request_shutdown()`; `matches!` discards `ExitRequestApi`.
- **`npm run verify` stays rust-free.** Do not install or require `rustc`, `cargo`, or Tauri. Root `package.json` `verify` is `lint && typecheck && typecheck:desktop && test && check:artifacts` (TypeScript desktop typecheck only).

Review time on the parent issue: `2026-08-20T08:37:35+08:00`. Verdict on `#30`: **block** — do not merge until the high findings are fixed and the sidecar lifecycle plus quit handshake are retested. This pipeline fixes the findings on the feature branch; it still does **not** open a PR or merge to `main`.

Live crate (do not rename): `apps/desktop/src-tauri/Cargo.toml` package `framepilot-desktop`, lib `framepilot_desktop_lib`.

---

## 2. Locked decisions

These are binding for this review-fix. Do not re-litigate Phase 0/1 architecture. Do not retick §5.1 Phase 1 boxes.

1. **F001 == F006 one change.** One terminate-on-error + wait path after `spawn_sidecar` (ready-line timeout/parse failure and missing stdout). Health-fail already terminates; keep that. Retry reuses the same allocated loopback port and absolute `--data-dir`. After a restart spawn, if `shutdown` is already set, terminate the new child instead of `store_child`. Never leave an orphan sidecar after start failure, retry, or quit.
2. **F003 is import-only.** Import `extra_button` is a regular Rust string with real ASCII quotes interpolated into a double-quoted JS `innerHTML` assignment inside a raw string — SyntaxError. Processing `extra_button` is `""`, so that script still parses. `quit_dialog_script_hides_cancel_for_processing_jobs` is substring-only and cannot catch the import bug.
3. **F003 + F004 must land together.** Fix script generation **and** change the unconfirmed handshake fallback from `CancelAndQuit` to `Stay` (reset `close_in_progress`). `CancelAndQuit` only for an explicit button payload.
4. **`ExitRequested` needs `prevent_exit`.** On app quit (Cmd+Q and other accelerators), `prevent_exit` and run the same `close_decision` flow as window `CloseRequested`. `request_shutdown` only after Stay is declined, and after `CancelThenTerminate` has waited up to `CANCEL_WAIT`. `RunEvent::Exit` may still drain.
5. **`npm run verify` stays rust-free.** Do not add `cargo test`, `rustc`, or Tauri to `verify`. Desktop unit tests run via `cargo test` in `apps/desktop/src-tauri` during `开发` / `测试`, not via `verify`.
6. **Shell stays Tauri 2 + Python sidecar.** Electron stays off the table. Crate name stays `framepilot-desktop`; lib stays `framepilot_desktop_lib`.
7. **Bind / port / data-dir:** Sidecar listens on `127.0.0.1` only. Never `0.0.0.0`. Shipped spawn never `--port 0`. `--data-dir` is required and absolute. `--port 0` remains valid for tests and standalone smoke only.
8. **Import cancel stays cooperative.** POST the existing cancel route. In-flight photo may remain `processing` until retry. Do **not** weaken `test_cancelled_import_job_stops_safely_and_retry_preserves_review_state`.
9. **Quit-anyway / SIGTERM is `failed` + retryable** via `fail_active_jobs_on_startup`, **not** `cancelled`. Processing jobs have no cancel route. Import-only extra button. Processing extra_button stays empty and must still parse.
10. **Safety:** Never modify or delete original photos. Copy-mode unchanged. Do not weaken export/asset path-escape or allowlist tests.
11. **Web app must keep working.** `apps/web` stays Next.js. Do not add `output: 'export'`. `npm run dev` on `:3000` / `:8000` stays valid. Playwright file inputs in `ImportPanel.tsx` stay.
12. **Project roots:** Never set `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME`, `/`, a drive root, or any broad parent. Custom roots are D2.00 (out of scope).
13. **Version:** `APP_VERSION` stays `2.0.0-rc2`. Do not bump `pyproject.toml` or either `package.json`. D5.04 is out of scope.
14. **This pipeline’s branch:** stay on `feature/desktop-packaging`. Do not checkout other branches. Do not open a PR. Do not merge to `main`. Do not close GitHub issues. Push after each finished stage (`git push -u origin HEAD`).
15. **No cloud, login, payment, bundled models, HEIC/RAW/XMP.**
16. **Tracker:** `docs/plans/2026-08-18-desktop-packaging.md` §5.1 Phase 1 ids D1.01–D1.09 stay `[x]`. D0.07 stays dated `[~]`. Do not start D2–D5. Do not retick Phase 1 as part of this fix.
17. **English** for code, comments, tests, docs, and commit messages. No `Co-authored-by Cursor` or similar trailers.

---

## 3. In-scope issue ids

Parent tracking issue:

| Role | Issue | Title |
|------|-------|-------|
| Parent | [joe-cheung-cae/frame-pilot#30](https://github.com/joe-cheung-cae/frame-pilot/issues/30) | Full code review (2026-08-20) — `feature/desktop-packaging` @ `7e545f8` (verdict **block**) |

Confirmed sub-issues (all in scope; always write `owner/repo#N`):

| ID | Issue | Severity | Category | Title | Implementation grouping |
|----|-------|----------|----------|-------|-------------------------|
| F001 | [joe-cheung-cae/frame-pilot#33](https://github.com/joe-cheung-cae/frame-pilot/issues/33) | high | bug | Ready-line failure drops the sidecar without terminating it | **One change with F006** |
| F002 | [joe-cheung-cae/frame-pilot#35](https://github.com/joe-cheung-cae/frame-pilot/issues/35) | high | reliability | Supervisor can respawn the sidecar after shutdown | Own slice after F001+F006 |
| F003 | [joe-cheung-cae/frame-pilot#36](https://github.com/joe-cheung-cae/frame-pilot/issues/36) | high | bug | Import quit dialog script is invalid JavaScript | **Must land with F004** |
| F004 | [joe-cheung-cae/frame-pilot#34](https://github.com/joe-cheung-cae/frame-pilot/issues/34) | medium | ux | Failed quit-dialog handshake defaults to cancel-and-quit | **Must land with F003** |
| F005 | [joe-cheung-cae/frame-pilot#31](https://github.com/joe-cheung-cae/frame-pilot/issues/31) | medium | ux | App quit SIGTERMs the sidecar without the close dialog | Own slice; `prevent_exit` |
| F006 | [joe-cheung-cae/frame-pilot#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32) | medium | reliability | Sidecar process leaked when ready-line wait fails | **Same as F001 — not a second patch** |

**Totals:** 3 high · 3 medium · 0 low (6 confirmed; F001 and F006 are one implementation item).

Suggested serial order (from `#30` triage; 归档 will name A–D slices):

1. F001 + F006 — terminate (and wait) on every post-spawn error before retry; shutdown-aware `store_child`
2. F002 — re-check `shutdown` after `probe_health` and before `start_sidecar_process` / `store_child`
3. F003 + F004 — generate a parseable import overlay; handshake timeout → `CloseChoice::Stay`
4. F005 — `ExitRequested`: `prevent_exit`, same `close_decision` as window close

Do not tick GitHub issues or §5.1 boxes in this documentation stage.

---

## 4. Out of scope

Explicitly **not** this review-fix:

- **Desktop Phases 2–5.** Do not start D2.00–D5.05 (registered project roots, native pickers, menus, installers, desktop CI matrix, signing, `2.1.0-desktop` bump).
- **`APP_VERSION` bump.** Stay `2.0.0-rc2`. D5.04 is out.
- **Opening a PR, merging to `main`, or closing GitHub issues** (`#30` `#33` `#35` `#36` `#34` `#31` `#32` stay open).
- **D1.01–D1.09 redo.** Phase 1 product work is already `[x]`. Do not retick those boxes. Do not reimplement navigation adapters, Vite SPA, data-dir policy, or the D1.09 confirm dialog from scratch — only fix the confirmed defects in the existing handlers.
- **Cloud / login / payment / telemetry / remote processing.**
- **HEIC / RAW / XMP / bundled neural models.**
- **`output: 'export'`** on `apps/web`. Keep Next.js.
- **Setting `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST=$HOME`** (or `/`, a drive root, or any broad parent).
- **A second F006 patch.** F001 == F006 one change.
- Making `npm run verify` require `rustc`, `cargo`, or Tauri.
- Weakening `test_cancelled_import_job_stops_safely_and_retry_preserves_review_state`.
- Adding a processing-job cancel route. Processing extra_button stays empty.
- Labelling quit-anyway / SIGTERM as `cancelled`. That path is `failed` + retryable via `fail_active_jobs_on_startup`.
- Shipping `--port 0` on the Tauri spawn path. Relative `--data-dir`. Bind on `0.0.0.0`.
- Publishing installers. Checking out other branches. Creating a second worktree.
- Adding `desktop-packaging-review.rhai` in this commit (that file already exists from the review pipeline; do not add it here). This commit **may** include already-authored `.grok/workflows/desktop-review-fix.rhai`.
- Starting `评审` implementation notes as if they were code, or starting `开发` in this stage.

---

## 5. Files to create / modify

This `需求拆解` stage only writes handoff docs (and may git-add the already-authored workflow). Production files below are for later `开发` slices.

### This documentation stage

- **Create:** `docs/handoff/review-fix-requirements.md` (this file)
- **Replace:** `docs/handoff/STATUS.md`
- **May include if already authored:** `.grok/workflows/desktop-review-fix.rhai`
- **Do not add:** `.grok/workflows/desktop-packaging-review.rhai`

### F001 + F006 — terminate on ready-line / missing-stdout error ([joe-cheung-cae/frame-pilot#33](https://github.com/joe-cheung-cae/frame-pilot/issues/33), [joe-cheung-cae/frame-pilot#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32))

- **Modify:** `apps/desktop/src-tauri/src/lib.rs` — `start_sidecar_process` (~66–76), `start_sidecar_with_retry`, `store_child`
- **Modify if extracting a testable Drop/guard:** `apps/desktop/src-tauri/src/sidecar.rs` (`spawn_sidecar`, `wait_for_ready_line`, `terminate_sidecar`)
- Prefer a Drop/guard so every post-spawn `Err` path terminates (including `wait_for_ready_line` timeout/parse failure and missing stdout). Health-fail already calls `terminate_sidecar`; keep that.
- If `shutdown` is already set after a restart spawn, terminate the new child instead of `store_child` (F006 shutdown-aware store note; implement with F001, not later).

### F002 — shutdown-aware supervisor ([joe-cheung-cae/frame-pilot#35](https://github.com/joe-cheung-cae/frame-pilot/issues/35))

- **Modify:** `apps/desktop/src-tauri/src/lib.rs` — `supervise_sidecar`, `SidecarState`, `request_shutdown`, `store_child`, `start_sidecar_process`
- Re-check `shutdown` after `probe_health` and immediately before `start_sidecar_process` and `store_child`. If shutdown is set, do not spawn; terminate any local `Child`. Prefer `SidecarState` Drop that always terminates.

### F003 + F004 — parseable import overlay + Stay fallback ([joe-cheung-cae/frame-pilot#36](https://github.com/joe-cheung-cae/frame-pilot/issues/36), [joe-cheung-cae/frame-pilot#34](https://github.com/joe-cheung-cae/frame-pilot/issues/34))

- **Modify:** `apps/desktop/src-tauri/src/sidecar.rs` — `quit_dialog_script` (import `extra_button` at ~150; `innerHTML` interpolation at ~168)
- **Modify:** `apps/desktop/src-tauri/src/lib.rs` — `handle_close_requested` (~126–157)
- Fix generation (DOM APIs, HTML entities, or the same backslash-quote escaping as the hardcoded buttons). Processing `extra_button` stays empty and must still parse.
- Unconfirmed handshake → `CloseChoice::Stay` and reset `close_in_progress`. Extract a small testable helper (unresolved handshake → Stay).

### F005 — `ExitRequested` `prevent_exit` ([joe-cheung-cae/frame-pilot#31](https://github.com/joe-cheung-cae/frame-pilot/issues/31))

- **Modify:** `apps/desktop/src-tauri/src/lib.rs` — `app.run` (~337–340), reuse `handle_close_requested` or a shared helper
- On `ExitRequested`, `prevent_exit` and the same `close_decision` as `CloseRequested`. Stay keeps the sidecar alive. Quit and cancel import POSTs cancel. Quit anyway SIGTERMs without labelling the job `cancelled`.

### Shared constraints (do not change unless a later slice truly requires it)

- Do not change `apps/web` except if a shared string is truly required (it should not be).
- Do not change `apps/api` cancel routes, cooperative-cancel tests, or `fail_active_jobs_on_startup` semantics in this track unless a documented hole is in-scope (it is not).
- `Cargo.toml` crate name stays `framepilot-desktop`; lib stays `framepilot_desktop_lib`. Add test-only deps only if a later slice cannot test without them.
- `docs/v2_known_limitations.md` already states cooperative cancel and quit-anyway = failed + retryable. Update only if the remaining gap note would be wrong after the fix.

---

## 6. Tests-first list

Write the failing test **before** the implementation. Drive shipped functions. Do not mock the unit under test. Do not re-implement the oracle in the test. A substring-only test is **not** enough for the import overlay.

| Group | Write first | Must assert | Run |
|-------|-------------|-------------|-----|
| F001+F006 [joe-cheung-cae/frame-pilot#33](https://github.com/joe-cheung-cae/frame-pilot/issues/33) / [#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32) | Rust unit/harness in `apps/desktop/src-tauri` (same `#[cfg(test)]` style as `sidecar.rs`; extract a small guard into `sidecar.rs` if `lib.rs` is awkward without Tauri) | After a ready-line timeout or parse failure, `terminate_sidecar` (and wait) ran; no process remains listening on the allocated loopback port; retry can bind the same port and start a new sidecar; missing stdout also terminates the child before return; after a restart spawn, if `shutdown` is already set, the new child is terminated instead of stored. Spawn a real child (short listener or sleep), do not mock `Child`. | `cargo test` in `apps/desktop/src-tauri` (crate `framepilot-desktop`) |
| F002 [joe-cheung-cae/frame-pilot#35](https://github.com/joe-cheung-cae/frame-pilot/issues/35) | Rust unit tests on shipped helpers | If `shutdown` is set, `start_sidecar_process` / `store_child` do not keep a live child; re-check after `probe_health`; any child spawned after shutdown is terminated before return; close/quit during the 400ms health probe leaves no sidecar after exit (helper-level). | `cargo test` in `apps/desktop/src-tauri` |
| F003 [joe-cheung-cae/frame-pilot#36](https://github.com/joe-cheung-cae/frame-pilot/issues/36) | Rust unit test that **parses** the emitted script | `quit_dialog_script(CloseJobKind::Import)` is syntactically valid JavaScript **and** still contains `data-choice=cancel_and_quit`. Parse for real (`node --check` on the emitted script, or an equivalent parser). Substring-only is a fail. Processing script still has no Quit and cancel; empty `extra_button` still parses. | `cargo test` in `apps/desktop/src-tauri` (and node parse if used) |
| F004 [joe-cheung-cae/frame-pilot#34](https://github.com/joe-cheung-cae/frame-pilot/issues/34) | Testable handshake helper (unresolved → Stay) | Handshake timeout or invalid first payload maps to `CloseChoice::Stay` and is specified to reset `close_in_progress`. Explicit `cancel_and_quit` and `quit_anyway` unchanged. Cancel is POSTed only on the cancel button. | `cargo test` in `apps/desktop/src-tauri` |
| F005 [joe-cheung-cae/frame-pilot#31](https://github.com/joe-cheung-cae/frame-pilot/issues/31) | Testable ExitRequested helper | `ExitRequested` is `prevent_exit`'d and routed through `close_decision`; Stay does not `request_shutdown`; window close path still maps through the same decision. | `cargo test` in `apps/desktop/src-tauri` |
| Regression | Existing tests | Do **not** weaken `test_cancelled_import_job_stops_safely_and_retry_preserves_review_state`. Do not add a processing cancel route. `npm run verify` does not invoke `rustc` / `cargo` / Tauri. | `npm run test:web`; `npm run verify` with fail-if-invoked wrappers; do not run job pytest unless API is touched (it should not be) |

**`测试` stage verification plan:**

1. `cargo test` in `apps/desktop/src-tauri` **twice**. Must include the new tests from A–D. Record count.
2. `npm run test:web` exit 0.
3. `npm run verify` exit 0 and rust-free (fail-if-invoked wrappers on PATH for `rustc`/`cargo`/`tauri`).
4. Do not run job pytest unless API changed (it should not).
5. If `tests/desktop/smoke.sh` or `npm run test:desktop:smoke` exists, run it.
6. GUI WebView of the overlay is not required if unit tests prove the import script parses and Stay is the unconfirmed fallback.
7. If `rustc`/`cargo` missing (exit 127), capture exact command+error; do not claim those tests passed; still run the non-Rust checks.

Keep existing path-import immutability and allowlist tests green. Never set `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME`.

---

## 7. Acceptance boxes

Copied from the GitHub issue bodies. Ticked at `上线` 2026-08-20T11:13:12+08:00 after measured `测试` evidence (`cargo test` 35 passed twice on rustc/cargo 1.97.1; `npm run test:web`; `npm run verify` rust-free; `npm run test:desktop:smoke`). Do not close the issues. Do not open a PR. Do not merge to `main`.

### F001 — [joe-cheung-cae/frame-pilot#33](https://github.com/joe-cheung-cae/frame-pilot/issues/33) `[high]` Ready-line failure drops the sidecar without terminating it

Copied from `#33` Acceptance criteria:

- [x] After a ready-line timeout or parse failure, no process remains listening on the allocated loopback port
- [x] Retry can bind the same port and start a new sidecar
- [x] Missing stdout also terminates the child before return
- [x] A unit or harness test covers ready-line failure then retry (no leftover listener)

Evidence: slice A `7a8bdba74bfe656a64fd4ae172cbbfd494707fb7`. Tests `ready_line_timeout_terminates_listener_and_retry_can_bind_same_port`, `ready_line_parse_failure_terminates_listener_and_frees_port`, `missing_stdout_terminates_child_before_return` (real loopback listener, not `sleep`).

### F002 — [joe-cheung-cae/frame-pilot#35](https://github.com/joe-cheung-cae/frame-pilot/issues/35) `[high]` Supervisor can respawn the sidecar after shutdown

Copied from `#35` Acceptance criteria:

- [x] Close or quit during the 400ms health probe leaves no sidecar process after the app exits
- [x] `start_sidecar_process` / `store_child` are no-ops when `shutdown` is already set
- [x] Any child spawned after shutdown is terminated before return

Evidence: slice B `c7cda3c20c93725aa5efe74e914e3d6e06e4cca6` plus slice A shutdown-aware `store_child`. Tests `close_during_health_probe_leaves_no_sidecar`, `start_sidecar_process_does_not_spawn_when_shutdown_is_set`, `start_sidecar_process_and_store_child_do_not_keep_live_child_when_shutdown_is_set`, `start_sidecar_process_terminates_child_spawned_after_shutdown`, `supervisor_rechecks_shutdown_after_health_probe`. Note (I2): the issue’s “no-ops” wording is implemented as **terminate, do not drop** — a silent return that drops `Child` would leak.

### F003 — [joe-cheung-cae/frame-pilot#36](https://github.com/joe-cheung-cae/frame-pilot/issues/36) `[high]` Import quit dialog script is invalid JavaScript

Copied from `#36` Acceptance criteria:

- [x] `quit_dialog_script(CloseJobKind::Import)` is syntactically valid JavaScript
- [x] The import script still contains `data-choice=cancel_and_quit`
- [x] Closing during an import mounts Keep working / Quit and cancel import / Quit anyway
- [x] A unit test fails if the import script does not parse as JS (substring checks alone are not enough)

F003 is **import-only**. Processing `extra_button` is empty and still parses. Do not treat a green processing-dialog substring test as coverage for import.

Evidence: slice C `2ae116392b169aac2c8b70551624dcfb64582654` (landed with F004). Tests `quit_dialog_script_import_is_valid_javascript_with_cancel_button` (`node --check` / parser, not substring-only) and `quit_dialog_script_processing_is_valid_javascript_without_cancel`. The emitted import script includes Keep working, Quit and cancel import, and Quit anyway. Live GUI WebView click was not required by the `测试` plan.

### F004 — [joe-cheung-cae/frame-pilot#34](https://github.com/joe-cheung-cae/frame-pilot/issues/34) `[medium]` Failed quit-dialog handshake defaults to cancel-and-quit

Copied from `#34` Acceptance criteria:

- [x] Handshake timeout or invalid first payload leaves the window open (Stay) and resets `close_in_progress`
- [x] Cancel is POSTed only when the user clicks Quit and cancel import
- [x] Quit anyway still terminates without POST cancel

F003 + F004 **must land together**. Today F003 makes F004 the live import-close path (2s timeout then `CancelAndQuit`).

Evidence: same slice C commit as F003. Test `close_choice_from_handshake_unresolved_stays`. `eval` `Err` is `None` → Stay. Stay resets `close_in_progress`. `CancelThenTerminate` only from an explicit `cancel_and_quit` payload on an import job.

### F005 — [joe-cheung-cae/frame-pilot#31](https://github.com/joe-cheung-cae/frame-pilot/issues/31) `[medium]` App quit SIGTERMs the sidecar without the close dialog

Copied from `#31` Acceptance criteria:

- [x] Cmd+Q / app quit during an active import or processing job shows the same close dialog as the window close button
- [x] Stay keeps the app running and the sidecar alive
- [x] Quit and cancel import POSTs cancel and waits up to `CANCEL_WAIT` before SIGTERM
- [x] Quit anyway still SIGTERMs without pretending the job is `cancelled`

`ExitRequested` needs `prevent_exit`.

Evidence: slice D `2bd21f6922c47ab379929b0ff6f9dc3f830eac87`. Test `app_quit_action_prevents_exit_requested_and_shares_close_decision_with_window_close`. `prevent_exit` runs first; Stay does not `request_shutdown`; `RunEvent::Exit` may still drain. Quit-anyway / SIGTERM remains `failed` + retryable via `fail_active_jobs_on_startup`, not `cancelled`. Live Cmd+Q in a GUI session was not required by the `测试` plan.

### F006 — [joe-cheung-cae/frame-pilot#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32) `[medium]` Sidecar process leaked when ready-line wait fails

Copied from `#32` Acceptance criteria:

- [x] Same as F001: no leftover listener after ready-line failure
- [x] After a restart spawn, if `shutdown` is already set, the new child is terminated instead of stored
- [x] Closed together with F001

F001 == F006 **one change**. Do not write a second patch for F006.

Evidence: same slice A commit as F001. Test `store_child_terminates_when_shutdown_is_set`. Slice B is supervisor re-check + `SidecarState` Drop, not a second F006 patch.

### Parent `#30` retest (not extra product scope; evidence for `测试` / `上线`)

From [joe-cheung-cae/frame-pilot#30](https://github.com/joe-cheung-cae/frame-pilot/issues/30):

- [x] Ready-line timeout then retry (no leftover listener on the allocated port)
- [x] Close/quit during the 400ms probe (no child after exit)
- [x] Close during a running import (Keep working stays, cancel POSTs only on the cancel button)
- [x] Cmd+Q during import (same dialog, not an immediate SIGTERM)

`npm run verify` must not compile this crate. `测试` ran `npm run verify` with fail-if-invoked wrappers first on `PATH`; `rustc` / `cargo` / `tauri` were never called. Parent retest is helper/harness-level as specified (GUI WebView of the overlay was not required). Issues stay open.

---

## 8. Environment notes

- **OBJECTIVE branch is `feature/desktop-packaging`.** Confirm with `git rev-parse --abbrev-ref HEAD` before committing. Repo is `/Users/chao/workspace/repo/frame-pilot`. Do not checkout other branches. Do not open a PR. Do not merge to `main`. `isolation_worktree` is false; edit the shared workspace. Do not create a second worktree.
- **Parent review HEAD** is `7e545f80ad9205cc3a7ab67bf1683ab583743f24` (`feature/desktop-packaging` vs `origin/main` `1d6ffa70858e6663f2539fb25d1358fecf519cd4`).
- **This host is macOS.** User-space rustup was used in Phase 1 (`rustc 1.97.1` / `cargo 1.97.1` into `$HOME/.cargo`). If `cargo`/`rustc` are missing in a later stage (exit 127), capture the exact command+error; do not claim `cargo test` passed.
- **This `需求拆解` stage is documentation only.** Do not implement production Rust/TS/Python. Do not install rustup. Tests run: none (docs).
- **`npm run verify` must stay Rust-free.** Live script: `npm run lint && npm run typecheck && npm run typecheck:desktop && npm run test && npm run check:artifacts`. Do not add `cargo test` or `tauri build` to `verify`.
- Sidecar binds `127.0.0.1` only. Absolute `--data-dir`. Shipped spawn never `--port 0`.
- Import cancel stays cooperative. Quit-anyway / SIGTERM is `failed` + retryable, not `cancelled`. Processing jobs have no cancel route. Import-only extra button.
- Never set `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME`. Keep `apps/web` on Next.js. Do not add `output: 'export'`.
- English only. No `Co-authored-by Cursor` trailers.
- Scratch: `/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-501/desktop-review-fix` (chmod 700). Evidence copy: `/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-goal-7cc6541d0495/implementer`. Never use `/tmp` for handoff captures. If `git push` fails, write the exact git error to scratch `git-push.txt` and still finish the docs.
- Push after every finished stage: `git push -u origin HEAD`.

---

## 9. Risks

| Risk | Why it bites | Mitigation |
|------|--------------|------------|
| Second F006 patch | `#32` is labelled duplicate of F001 but has a shutdown-aware `store_child` note; a later slice might “fix F006 again” | F001 == F006 **one change**. Implement terminate-on-error **and** shutdown-aware `store_child` in the F001 slice. Do not write a second F006 patch. |
| Treating processing-dialog substring tests as F003 coverage | Processing `extra_button` is empty, so that script still parses; import quotes break JS | F003 is **import-only**. Test must parse `quit_dialog_script(CloseJobKind::Import)` as JS. Substring-only is a fail. |
| Shipping F003 without F004 | Today F003 makes F004 the live import-close path (2s then `CancelAndQuit`). A parseable overlay with the old fallback still unconfirmed-cancels if handshake fails | F003 + F004 **must land together**. Unconfirmed handshake → Stay. |
| `matches!` on `ExitRequested` | Discards `ExitRequestApi`; `prevent_exit` cannot run; Cmd+Q SIGTERMs immediately | F005: `ExitRequested` needs `prevent_exit` and the same `close_decision` as window close. |
| `verify` grows a Rust dependency | CI / non-desktop hosts fail; parent `#30` out-of-scope includes this | `npm run verify` stays rust-free. `cargo test` is `开发`/`测试` only. |
| Orphan sidecar after start failure / retry / quit | `Child` drop does not kill; retry reuses port and `--data-dir`; SQLite stays locked | Terminate-and-wait on every post-spawn error; shutdown re-check before spawn/store; Drop that always terminates. Never leave an orphan sidecar. |
| Weakening cooperative cancel | Changing cancel so no photo remains `processing` at the checkpoint breaks `test_cancelled_import_job_stops_safely_and_retry_preserves_review_state` | Import cancel stays cooperative. In-flight photo may remain `processing` until retry. Do not weaken that test. |
| Labelling SIGTERM as `cancelled` | Startup sweep marks killed jobs `failed`; processing has no cancel route | Quit-anyway / SIGTERM is `failed` + retryable via `fail_active_jobs_on_startup`, not `cancelled`. Import-only extra button. |
| Redoing D1.01–D1.09 or reticking §5.1 | Phase 1 is already GO `[x]`; tracker noise hides the review-fix | Do not redo product work. Do not retick Phase 1 boxes. Only fix F001–F006 in the existing handlers. |
| Starting Phase 2–5 / allowlist `$HOME` / Next export | Locked out of this track | Out of scope list is binding. |
| Closing GitHub issues or opening a PR | Objective forbids it; `#30` stays the parent tracker | Comment later in `上线`; do not close; do not PR; do not merge. |
| Mocking `Child` instead of a real leftover listener | Would not prove the port is free for retry | Spawn a real short listener/sleep; assert no leftover listener on the allocated port. |

---

## 10. Definition of done for this breakdown

- This file decomposes **only** [joe-cheung-cae/frame-pilot#30](https://github.com/joe-cheung-cae/frame-pilot/issues/30) sub-issues `#33` `#35` `#36` `#34` `#31` `#32` (F001–F006).
- It states explicitly: **F001 == F006 one change**; **F003 is import-only** (processing `extra_button` is empty and still parses); **F003 + F004 must land together**; **`ExitRequested` needs `prevent_exit`**; **`npm run verify` stays rust-free**.
- Locked decisions, in-scope / out-of-scope ids, files, tests-first list, acceptance boxes **copied** from `#33` `#35` `#36` `#34` `#31` `#32`, and risks are explicit enough for an adversarial `评审`.
- No production Rust / TypeScript / Python was changed in the `需求拆解` commit except documentation (and `.grok/workflows/desktop-review-fix.rhai` if included).
- §5.1 Phase 1 boxes stay `[x]`. D0.07 stays `[~]`. Phase 2 boxes stay `[ ]`.
- Next stage: `评审` writes `docs/handoff/review-fix-review.md` against live `lib.rs` and `sidecar.rs`.

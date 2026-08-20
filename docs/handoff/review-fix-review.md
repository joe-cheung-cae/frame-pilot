# Desktop Review-Fix Requirements Review

Handoff stage: `评审`  
Date: 2026-08-20T10:25:00+08:00  
Branch: `feature/desktop-packaging`  
Reviewed: `docs/handoff/review-fix-requirements.md` (需求拆解) against live `apps/desktop/src-tauri/src/lib.rs` and `sidecar.rs` on HEAD `7e545f80ad9205cc3a7ab67bf1683ab583743f24`  
Sources: GitHub [joe-cheung-cae/frame-pilot#30](https://github.com/joe-cheung-cae/frame-pilot/issues/30) and sub-issues `#33` `#35` `#36` `#34` `#31` `#32`, `docs/plans/2026-08-18-desktop-packaging.md` (D1.09, §5.1 already `[x]`), `AGENTS.md`, root `package.json` `verify`, `apps/desktop/src-tauri/Cargo.toml`

**Verdict: accept-with-notes**

The breakdown is a safe sidecar-lifecycle + quit-handshake contract. It matches the live defects, keeps F001 == F006 as one change, treats F003 as import-only, lands F003 with F004, requires `ExitRequested` `prevent_exit`, and leaves `npm run verify` rust-free. It does not contradict locked Phase 0/1 decisions or the confirmed GitHub findings. It is not rejected.

归档 must fold the notes below into `docs/handoff/review-fix-backlog.md` before 开发. The notes are missing-but-fixable implementation details (testable helpers, terminate-not-drop, eval-failure Stay, listener-not-sleep). They are not product-policy holes.

No production Rust / TypeScript / Python was changed in this stage. §5.1 Phase 1 boxes stay `[x]`. D0.07 stays dated `[~]`. Phase 2 boxes stay `[ ]`. Do not open a PR, merge to `main`, or close GitHub issues.

---

## 1. Live-tree facts (verified 2026-08-20T10:25:00+08:00)

Checked against `lib.rs` / `sidecar.rs` / `package.json`, not the docs alone.

| Claim in the breakdown | Live tree |
|------------------------|-----------|
| F001 == F006: `wait_for_ready_line` `?` drops `Child` without `terminate_sidecar` | Confirmed `lib.rs:66–72`. `spawn_sidecar` then `stdout.take()?` then `wait_for_ready_line(...).map_err(...)?`. `std::process::Child` drop does not kill or wait. |
| Missing stdout same leak | Confirmed `lib.rs:68–71`. `take()` `None` → `"sidecar stdout missing"` via `?`; `child` dropped still running. |
| Health-fail already terminates | Confirmed `lib.rs:73–75`. Keep this path. A Drop/guard may terminate again after wait; `terminate_sidecar` is idempotent via `try_wait`. |
| Retry reuses allocated port and `--data-dir` | Confirmed `lib.rs:80–94` (`start_sidecar_with_retry` passes the same `port` / `data_dir`). |
| `store_child` keeps a child even if `shutdown` is set | Confirmed `lib.rs:37–41`. Overwrites `Option<Child>` with no `shutdown` load. Dropping the argument without `terminate_sidecar` would leak. |
| F002: supervisor shutdown checks only at loop head | Confirmed `lib.rs:178–184` then `probe_health` 400ms at `:193`. Restart at `:202–213` calls `start_sidecar_process` then `store_child` with no re-check. `recovery_action(false, 1)` is `Restart` (`sidecar.rs:411–417`). |
| `request_shutdown` holds the child mutex for the whole SIGTERM/kill wait | Confirmed `lib.rs:43–50` + `terminate_sidecar` (`sidecar.rs:419–441`, grace 5s). |
| F003 import `extra_button` is a regular Rust string with real ASCII quotes | Confirmed `sidecar.rs:150` `"<button type=\"button\" data-choice=\"cancel_and_quit\">..."`. Interpolated into a double-quoted JS `innerHTML` assignment inside `r#"..."#` at `:168`. Hardcoded buttons keep literal `\"`; import quotes terminate the JS string. |
| Processing `extra_button` is empty and still parses | Confirmed `sidecar.rs:155` `""`. That generated script is valid JS. |
| `quit_dialog_script_hides_cancel_for_processing_jobs` is substring-only | Confirmed `sidecar.rs:808–817`. It would stay green on today's invalid import script. |
| F003 makes F004 the live import-close path | Confirmed `lib.rs:126–146`. `eval` error → `finish_quit`; missing `dialog_shown` / unparsed payload → `.unwrap_or(CloseChoice::CancelAndQuit)` which POSTs cancel for import (`close_decision` → `CancelThenTerminate`). Tauri `eval` typically does not wait for JS parse, so the 2s timeout is the likely live import path. |
| `ExitRequested` needs `prevent_exit` | Confirmed `lib.rs:337–340`. `matches!(event, RunEvent::Exit \| RunEvent::ExitRequested { .. })` always `request_shutdown()`. `matches!` discards `ExitRequestApi`. Window close is intercepted (`lib.rs:318–324`). |
| `npm run verify` rust-free | Confirmed root `package.json:19`: `lint && typecheck && typecheck:desktop && test && check:artifacts`. No `rustc` / `cargo` / `tauri`. |
| Crate `framepilot-desktop`, lib `framepilot_desktop_lib` | Confirmed `apps/desktop/src-tauri/Cargo.toml`. |
| Sidecar bind / port / data-dir | `LOOPBACK_HOST = "127.0.0.1"`; `sidecar_spawn_spec` rejects `--port 0` and relative `--data-dir`. |
| Import cancel cooperative; processing has no cancel route | `request_cancel_then_wait` POSTs existing cancel. API `routes.py:760` 422 `"Only import jobs can be cancelled"`. `test_cancelled_import_job_stops_safely_and_retry_preserves_review_state` still present. |
| Quit-anyway / SIGTERM is `failed` + retryable | `fail_active_jobs_on_startup` in `apps/api/app/services/jobs.py:94+`. Not `cancelled`. |
| `APP_VERSION` `2.0.0-rc2` | `apps/api/app/core/version.py`, root `package.json`, crate version. |
| `apps/web` stays Next.js; no `output: 'export'` | `apps/web/next.config.ts`. |
| §5.1 Phase 1 D1.01–D1.09 `[x]`; D0.07 `[~]`; Phase 2 `[ ]` | Confirmed `docs/plans/2026-08-18-desktop-packaging.md`. |
| `lib.rs` has no `#[cfg(test)]` | Tests live in `sidecar.rs` and `data_dir.rs` only. Helpers must be extracted to test without Tauri. |

---

## 2. Confirmation of locked couplings

All five adversarial checks hold. The breakdown does not invent a second F006 patch, does not treat the processing substring test as F003 coverage, does not ship F003 without F004, does not leave `ExitRequested` as a drain-only match, and does not grow `verify` into a Rust gate.

1. **F001 == F006 one change** ([joe-cheung-cae/frame-pilot#33](https://github.com/joe-cheung-cae/frame-pilot/issues/33) / [joe-cheung-cae/frame-pilot#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32)). Same leak at `lib.rs:72` plus missing-stdout. `#32` adds shutdown-aware `store_child`. Implement terminate-on-error **and** terminate-instead-of-store in slice A. Do not write a second F006 patch in slice B.
2. **F003 is import-only** ([joe-cheung-cae/frame-pilot#36](https://github.com/joe-cheung-cae/frame-pilot/issues/36)). Processing empty `extra_button` still parses. Import quotes break JS. Substring tests cannot catch it.
3. **F003 + F004 must land together** ([joe-cheung-cae/frame-pilot#34](https://github.com/joe-cheung-cae/frame-pilot/issues/34)). A parseable overlay with `unwrap_or(CancelAndQuit)` still unconfirmed-cancels on handshake miss. Stay only for explicit `stay` or unresolved handshake. `CancelAndQuit` only for the cancel button payload.
4. **`ExitRequested` needs `prevent_exit`** ([joe-cheung-cae/frame-pilot#31](https://github.com/joe-cheung-cae/frame-pilot/issues/31)). `RunEvent::Exit` may still drain. Cmd+Q must share `close_decision` with window close.
5. **`npm run verify` stays rust-free.** `cargo test` is `开发` / `测试` only, crate `framepilot-desktop` in `apps/desktop/src-tauri`.

Serial order A–D in the workflow is correct: F001+F006 → F002 → F003+F004 → F005.

---

## 3. Findings

None of these are reject reasons. 归档 must fold them into slice implement / tests-first text.

### I1 — Extract a terminate-on-error Drop/guard into `sidecar.rs` (important)

**Why.** `lib.rs` is awkward to unit-test without Tauri. `start_sidecar_process` has three post-spawn `Err` paths (missing stdout, ready-line timeout/parse, later health fail). A future `?` will leak again unless every path is covered by one guard.

**Required change for 归档/开发 (slice A).** Extract something like `SpawnedSidecar { child: Child, armed: bool }` into `sidecar.rs` with `Drop` calling `terminate_sidecar` while armed, and `into_child(self) -> Child` that disarms. `start_sidecar_process` wraps `spawn_sidecar` in that guard. Health-fail may keep its explicit `terminate_sidecar`; double-terminate after wait is OK. Drive the guard from tests with a **real** child, not a mock `Child`.

### I2 — `store_child` must terminate, not silently no-op (important)

**Why.** [joe-cheung-cae/frame-pilot#35](https://github.com/joe-cheung-cae/frame-pilot/issues/35) acceptance says `store_child` is a “no-op” when `shutdown` is set. A true no-op that returns without storing still **drops** the argument `Child` and leaks the process — the F001 bug again. [joe-cheung-cae/frame-pilot#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32) and the breakdown implement text already say terminate instead of store.

**Required change for 归档/开发.** Slice A: if `shutdown` is set, `store_child` takes the child and `terminate_sidecar`s it. Slice B: re-check `shutdown` after `probe_health` and immediately before `start_sidecar_process`; do not spawn; terminate any local `Child`. Prefer `SidecarState` `Drop` that always terminates (defense in depth; `Arc` drop is not the primary race fix). Do **not** treat slice B as a second F006 patch.

### I3 — Unresolved handshake helper must include `eval` failure → Stay (important)

**Why.** Today `webview.eval(...).is_err()` at `lib.rs:126–128` calls `finish_quit` immediately (SIGTERM, no Stay, no POST cancel). The 2s `unwrap_or(CancelAndQuit)` at `:143–146` is the other unconfirmed path. After F003, a still-failing `eval` must not skip the Stay fallback.

**Required change for 归档/开发 (slice C).** Extract a small shipped helper, for example `fn close_choice_from_handshake(payload: Option<&str>) -> CloseChoice` mapping parseable `stay` / `cancel_and_quit` / `quit_anyway` to those choices and **everything else** (timeout `None`, `dialog_shown`, junk) to `CloseChoice::Stay`. `handle_close_requested` uses it for recv timeout **and** for `eval` `Err` (treat as unresolved). Stay resets `close_in_progress`. `CancelAndQuit` only from an explicit button payload. Processing empty `extra_button` must still parse.

### I4 — `prevent_exit` before the `close_in_progress` early-return (important)

**Why.** `handle_close_requested` returns immediately if `close_in_progress` is already true. If `ExitRequested` is routed through that function **before** `api.prevent_exit()`, Cmd+Q during an in-flight window-close dialog still exits and SIGTERMs.

**Required change for 归档/开发 (slice D).** `match` `RunEvent::ExitRequested { api, .. }`, call `api.prevent_exit()` first, then the same `close_decision` flow as `CloseRequested`. Extract a testable routing helper so tests can assert: `ExitRequested` → prevent + dialog path; `Stay` does not `request_shutdown`; `RunEvent::Exit` may still drain; window close still maps through the same decision.

### N1 — F001 leftover-port assertion needs a listener, not only `sleep` (note)

A `sleep` child does not occupy the allocated loopback port, so “retry can bind the same port” would not prove the leak is gone. Spawn a short `127.0.0.1` listener (or a process that binds the allocated port and omits a valid ready line). Do not mock `Child`. After terminate-and-wait, the test must bind that port again.

### N2 — Ready-line timeout leaves a stdout reader thread (note)

`wait_for_ready_line` (`sidecar.rs:354–377`) parks a thread on `stdout` until a line or process death. That is acceptable once `terminate_sidecar` runs (pipe EOF). Do not “fix” it by leaking the process or by skipping wait.

### N3 — Do not reopen locked fences (note)

Do not retick D1.01–D1.09. Do not start D2–D5. Do not bump `APP_VERSION`. Do not add `output: 'export'`. Do not set `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME`. Do not weaken `test_cancelled_import_job_stops_safely_and_retry_preserves_review_state`. Do not add a processing cancel route. Do not label quit-anyway / SIGTERM as `cancelled`. Do not ship `--port 0`. Do not close GitHub issues or open a PR. English only; no `Co-authored-by Cursor` trailers.

---

## 4. Testable helpers (required)

归档 must name these in the A–D slices so 开发 writes failing tests against **shipped** functions.

| Helper | Put in | Slice | Must prove |
|--------|--------|-------|------------|
| Terminate-on-error Drop/guard (`SpawnedSidecar` or equivalent) | `sidecar.rs` | A — [joe-cheung-cae/frame-pilot#33](https://github.com/joe-cheung-cae/frame-pilot/issues/33) + [joe-cheung-cae/frame-pilot#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32) | Ready-line timeout/parse failure and missing stdout terminate-and-wait; no leftover listener on the allocated port; retry can bind that port; shutdown-set `store_child` terminates instead of keeping the child. |
| Shutdown re-check + `SidecarState` Drop | `lib.rs` (tiny predicate may live in `sidecar.rs` if that is easier to test) | B — [joe-cheung-cae/frame-pilot#35](https://github.com/joe-cheung-cae/frame-pilot/issues/35) | After `probe_health`, if `shutdown` is set, do not spawn; any child spawned after shutdown is terminated before return. Not a second F006 patch. |
| Handshake Stay fallback | `sidecar.rs` | C — [joe-cheung-cae/frame-pilot#36](https://github.com/joe-cheung-cae/frame-pilot/issues/36) + [joe-cheung-cae/frame-pilot#34](https://github.com/joe-cheung-cae/frame-pilot/issues/34) | `None` / invalid / `dialog_shown` → `CloseChoice::Stay`; explicit `cancel_and_quit` and `quit_anyway` unchanged. Import `quit_dialog_script` **parses as JS** (`node --check` or equivalent parser) and still contains `data-choice=cancel_and_quit`. Substring-only is a fail. Processing script still has no Quit and cancel and still parses. |
| `ExitRequested` routing | `sidecar.rs` or a tiny enum next to `close_decision` | D — [joe-cheung-cae/frame-pilot#31](https://github.com/joe-cheung-cae/frame-pilot/issues/31) | `ExitRequested` → prevent_exit + same `close_decision` as window close; Stay does not `request_shutdown`; `Exit` may drain. |

Do not mock the unit under test. Do not re-implement the oracle in the test.

---

## 5. Required tests-first list

Copy into the backlog. Write the failing test before the implementation. Run via `cargo test` in `apps/desktop/src-tauri` (crate `framepilot-desktop`) during `开发` / `测试`, **not** via `npm run verify`.

| Group | Write first | Must assert | Run |
|-------|-------------|-------------|-----|
| A. F001+F006 [joe-cheung-cae/frame-pilot#33](https://github.com/joe-cheung-cae/frame-pilot/issues/33) / [#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32) | Guard/harness in `sidecar.rs` `#[cfg(test)]` | After ready-line timeout or parse failure, `terminate_sidecar` (and wait) ran; no leftover listener on the allocated loopback port; retry can bind that port; missing stdout also terminates before return; if `shutdown` is set, `store_child` terminates instead of storing. Real child that **listens** (not only `sleep`). | `cargo test` in `apps/desktop/src-tauri` |
| B. F002 [joe-cheung-cae/frame-pilot#35](https://github.com/joe-cheung-cae/frame-pilot/issues/35) | Unit tests on shipped helpers | If `shutdown` is set, `start_sidecar_process` / `store_child` do not keep a live child; re-check after `probe_health`; child spawned after shutdown is terminated before return. | `cargo test` in `apps/desktop/src-tauri` |
| C. F003 [joe-cheung-cae/frame-pilot#36](https://github.com/joe-cheung-cae/frame-pilot/issues/36) | Parser test of emitted script | `quit_dialog_script(CloseJobKind::Import)` is syntactically valid JavaScript **and** contains `data-choice=cancel_and_quit`. Parse for real. Processing script has no Quit and cancel; empty `extra_button` still parses. | `cargo test` (and `node --check` if used) |
| C. F004 [joe-cheung-cae/frame-pilot#34](https://github.com/joe-cheung-cae/frame-pilot/issues/34) | Handshake helper | Timeout / invalid first payload / `eval` failure → `CloseChoice::Stay` and reset `close_in_progress`. Explicit cancel POSTs only on the cancel button. Quit anyway terminates without POST cancel. | `cargo test` in `apps/desktop/src-tauri` |
| D. F005 [joe-cheung-cae/frame-pilot#31](https://github.com/joe-cheung-cae/frame-pilot/issues/31) | ExitRequested routing helper | `ExitRequested` is `prevent_exit`'d and routed through `close_decision`; Stay does not `request_shutdown`; window close uses the same decision. | `cargo test` in `apps/desktop/src-tauri` |
| Regression | Existing tests | Do not weaken `test_cancelled_import_job_stops_safely_and_retry_preserves_review_state`. Do not add a processing cancel route. `npm run verify` does not invoke `rustc` / `cargo` / `tauri`. | `npm run test:web`; `npm run verify` with fail-if-invoked wrappers |

**`测试` stage verification plan** (unchanged, still binding):

1. `cargo test` in `apps/desktop/src-tauri` **twice**. Must include the new tests from A–D. Record count.
2. `npm run test:web` exit 0.
3. `npm run verify` exit 0 and rust-free (fail-if-invoked wrappers on PATH for `rustc`/`cargo`/`tauri`).
4. Do not run job pytest unless API changed (it should not).
5. If `tests/desktop/smoke.sh` or `npm run test:desktop:smoke` exists, run it.
6. GUI WebView of the overlay is not required if unit tests prove the import script parses and Stay is the unconfirmed fallback.
7. If `rustc`/`cargo` missing (exit 127), capture exact command+error; do not claim those tests passed; still run the non-Rust checks.

---

## 6. Acceptance boxes (still unticked)

Copied from the issues. `上线` ticks them only after measured evidence. Do not close [joe-cheung-cae/frame-pilot#30](https://github.com/joe-cheung-cae/frame-pilot/issues/30) or the sub-issues.

- F001 `#33`: no leftover listener after ready-line failure; retry binds the same port; missing stdout terminates; harness covers failure then retry.
- F002 `#35`: close/quit during the 400ms probe leaves no sidecar; `start_sidecar_process` / `store_child` do not keep a live child when `shutdown` is set (terminate, do not drop); post-shutdown spawn is terminated before return.
- F003 `#36`: import script parses as JS; still contains `data-choice=cancel_and_quit`; overlay mounts three buttons; parser test (not substring-only).
- F004 `#34`: unresolved handshake → Stay + reset `close_in_progress`; cancel POSTed only on the cancel button; quit anyway SIGTERMs without POST cancel. Lands with F003.
- F005 `#31`: Cmd+Q shows the same dialog; Stay keeps sidecar alive; cancel waits up to `CANCEL_WAIT` then SIGTERM; quit anyway is `failed` + retryable, not `cancelled`. `prevent_exit` first.
- F006 `#32`: same as F001 plus shutdown-aware store; closed with F001, not a second patch.

Parent `#30` retest: ready-line timeout then retry; close during 400ms probe; close during import (Keep working stays); Cmd+Q during import (dialog, not immediate SIGTERM). `npm run verify` must not compile this crate.

---

## 7. Definition of done for this review

- Verdict is **accept-with-notes** (not reject): the breakdown matches live `lib.rs` / `sidecar.rs` and does not contradict locked decisions.
- Notes I1–I4 and N1–N3 plus the helper table are explicit enough for 归档 slices A–D.
- No production code changed. Phase 1 boxes stay `[x]`. Next stage: 归档 writes `docs/handoff/review-fix-backlog.md`.

# Desktop Review-Fix Accepted Backlog

Handoff stage: `归档`  
Date: 2026-08-20T10:40:00+08:00  
Branch: `feature/desktop-packaging`  
Parent: [joe-cheung-cae/frame-pilot#30](https://github.com/joe-cheung-cae/frame-pilot#30) (verdict **block** at `7e545f80`; this pipeline does not merge)  
Sources: `docs/handoff/review-fix-requirements.md`, `docs/handoff/review-fix-review.md` (verdict **accept-with-notes**), live `apps/desktop/src-tauri/src/lib.rs` / `sidecar.rs`, GitHub `#33` `#35` `#36` `#34` `#31` `#32`

**Verdict folded:** accept-with-notes. This file is the accepted implementation contract for **F001–F006 only**. F001 ([joe-cheung-cae/frame-pilot#33](https://github.com/joe-cheung-cae/frame-pilot/issues/33)) and F006 ([joe-cheung-cae/frame-pilot#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32)) are **one implementation**. F006 is **not** a second feature and must not get a second patch.

This document does not implement production Rust / TypeScript / Python. §5.1 Phase 1 boxes stay `[x]`. D0.07 stays dated `[~]`. Phase 2 boxes stay `[ ]`. Do not start Phases 2–5. Do not bump `APP_VERSION`. Do not redo D1.01–D1.09 product work. Do not start `开发` from this archive commit.

---

## Process

- Implement **one slice at a time**, tests first, then the smallest change that makes those tests pass.
- Slice **开发** as **exactly** A then B then C then D. Do not start B before A is committed. Do not start C before B is committed. Do not start D before C is committed.
- Extra per-slice commits are allowed (tests, follow-ups). `开发` **must finish with these four required subjects** (STATUS may be updated in D):
  1. `desktop: terminate sidecar on ready-line failure`
  2. `desktop: avoid sidecar respawn after shutdown`
  3. `desktop: fix import quit dialog script and stay fallback`
  4. `desktop: route app quit through the close dialog`
- Push after every finished stage **and** after every `开发` slice commit: `git push -u origin HEAD`.
- `测试` drives the verification plan below. `cargo test` is `开发` / `测试` only, crate `framepilot-desktop` in `apps/desktop/src-tauri`.
- `上线` may comment on GitHub; do **not** close issues, open a PR, or merge to `main`.
- Stay on `feature/desktop-packaging`. Do not checkout other branches.
- Local-first. Never modify or delete original photos. English for code, comments, tests, docs, and commits. No `Co-authored-by Cursor` trailers.
- `npm run verify` stays rust-free. Do not install or require `rustc`, `cargo`, or Tauri.
- Drive **shipped** helpers. Do not mock the unit under test. Do not re-implement the oracle in the test.
- Never leave an orphan sidecar after start failure, retry, or quit.

| Slice | ID | Title | Depends on | Required commit subject |
|-------|----|-------|------------|-------------------------|
| A | F001+F006 | Terminate sidecar on ready-line / missing-stdout failure; shutdown-aware `store_child` | none — do this first | `desktop: terminate sidecar on ready-line failure` |
| B | F002 | Shutdown-aware supervisor / `store_child` / Drop | A committed | `desktop: avoid sidecar respawn after shutdown` |
| C | F003+F004 | Parseable import overlay + Stay fallback | B committed | `desktop: fix import quit dialog script and stay fallback` |
| D | F005 | `ExitRequested` `prevent_exit` + same `close_decision` | C committed | `desktop: route app quit through the close dialog` |

F006 is closed with slice A. Slice B is **not** a second F006 patch.

---

## Folded review notes

| Id | Finding | Folded into |
|----|---------|-------------|
| I1 | Extract a terminate-on-error Drop/guard into `sidecar.rs` (`SpawnedSidecar { child, armed }` + `into_child`) | A — wrap `spawn_sidecar`; Drop terminates while armed |
| I2 | `store_child` must terminate, not silently no-op (a no-op that drops `Child` leaks) | A — terminate instead of store when `shutdown` is set. B — supervisor re-check + `SidecarState` Drop (not a second F006 patch) |
| I3 | Unresolved handshake helper must include `eval` failure → Stay | C — `close_choice_from_handshake`; `eval` `Err` is unresolved |
| I4 | `prevent_exit` before the `close_in_progress` early-return | D — `api.prevent_exit()` first, then the same `close_decision` flow |
| N1 | F001 leftover-port assertion needs a listener, not only `sleep` | A tests-first — real `127.0.0.1` listener on the allocated port |
| N2 | Ready-line timeout leaves a stdout reader thread; OK once `terminate_sidecar` runs | A — do not skip wait; do not leak the process |
| N3 | Do not reopen locked fences | Locked decisions below |

---

## Locked decisions (do not re-litigate)

1. **F001 == F006 one change.** [joe-cheung-cae/frame-pilot#33](https://github.com/joe-cheung-cae/frame-pilot/issues/33) and [joe-cheung-cae/frame-pilot#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32) are the same leak. One terminate-on-error + wait path after `spawn_sidecar` (ready-line timeout/parse failure **and** missing stdout). Health-fail already terminates; keep that. Retry reuses the same allocated loopback port and absolute `--data-dir`. After a restart spawn, if `shutdown` is already set, terminate the new child instead of storing it. Do **not** write a second patch for F006.
2. **F003 is import-only.** [joe-cheung-cae/frame-pilot#36](https://github.com/joe-cheung-cae/frame-pilot/issues/36). Import `extra_button` quotes break JS. Processing `extra_button` is `""` and that generated script still parses. Do not treat a green processing-dialog substring test as coverage for import.
3. **F003 + F004 must land together.** [joe-cheung-cae/frame-pilot#34](https://github.com/joe-cheung-cae/frame-pilot/issues/34). Fix script generation **and** change the unconfirmed handshake fallback from `CancelAndQuit` to `Stay`. `CancelAndQuit` only for an explicit button payload. `eval` `Err` is also Stay.
4. **`ExitRequested` needs `prevent_exit`.** [joe-cheung-cae/frame-pilot#31](https://github.com/joe-cheung-cae/frame-pilot/issues/31). Call `api.prevent_exit()` first, then the same `close_decision` as window close. `RunEvent::Exit` may still drain.
5. **`npm run verify` stays rust-free.** Root `package.json` `verify` is `lint && typecheck && typecheck:desktop && test && check:artifacts`. Do not add `cargo test`, `rustc`, or Tauri.
6. **Shell stays Tauri 2 + Python sidecar.** Crate name stays `framepilot-desktop`; lib stays `framepilot_desktop_lib`.
7. **Bind / port / data-dir:** Sidecar listens on `127.0.0.1` only. Never `0.0.0.0`. Shipped spawn never `--port 0`. `--data-dir` is required and absolute.
8. **Import cancel stays cooperative.** POST the existing cancel route. In-flight photo may remain `processing` until retry. Do **not** weaken `test_cancelled_import_job_stops_safely_and_retry_preserves_review_state`.
9. **Quit-anyway / SIGTERM is `failed` + retryable** via `fail_active_jobs_on_startup`, **not** `cancelled`. Processing jobs have no cancel route. Import-only extra button. Processing `extra_button` stays empty and must still parse.
10. **Safety:** Never modify or delete original photos. Copy-mode unchanged.
11. **Web app must keep working.** `apps/web` stays Next.js. Do not add `output: 'export'`.
12. **Project roots:** Never set `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME`, `/`, a drive root, or any broad parent.
13. **Version:** `APP_VERSION` stays `2.0.0-rc2`. Do not bump `pyproject.toml` or either `package.json`.
14. **This pipeline’s branch:** stay on `feature/desktop-packaging`. Do not open a PR. Do not merge to `main`. Do not close GitHub issues.
15. **No cloud, login, payment, bundled models, HEIC/RAW/XMP.**
16. **Tracker:** `docs/plans/2026-08-18-desktop-packaging.md` §5.1 Phase 1 ids D1.01–D1.09 stay `[x]`. D0.07 stays dated `[~]`. Do not start D2–D5. Do not retick Phase 1 as part of this fix.
17. **English** for code, comments, tests, docs, and commit messages. No `Co-authored-by Cursor` or similar trailers.

---

## Testable helpers (required)

`开发` writes failing tests against **shipped** functions. `lib.rs` has no `#[cfg(test)]`; extract helpers so tests do not need Tauri.

| Helper | Put in | Slice | Must prove |
|--------|--------|-------|------------|
| Terminate-on-error Drop/guard (`SpawnedSidecar` or equivalent) | `sidecar.rs` | A — [joe-cheung-cae/frame-pilot#33](https://github.com/joe-cheung-cae/frame-pilot/issues/33) + [joe-cheung-cae/frame-pilot#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32) | Ready-line timeout/parse failure and missing stdout terminate-and-wait; no leftover listener on the allocated port; retry can bind that port; shutdown-set `store_child` terminates instead of keeping the child. |
| Shutdown re-check + `SidecarState` Drop | `lib.rs` (tiny predicate may live in `sidecar.rs` if that is easier to test) | B — [joe-cheung-cae/frame-pilot#35](https://github.com/joe-cheung-cae/frame-pilot/issues/35) | After `probe_health`, if `shutdown` is set, do not spawn; any child spawned after shutdown is terminated before return. Not a second F006 patch. |
| Handshake Stay fallback | `sidecar.rs` | C — [joe-cheung-cae/frame-pilot#36](https://github.com/joe-cheung-cae/frame-pilot/issues/36) + [joe-cheung-cae/frame-pilot#34](https://github.com/joe-cheung-cae/frame-pilot/issues/34) | `None` / invalid / `dialog_shown` / `eval` failure → `CloseChoice::Stay`; explicit `cancel_and_quit` and `quit_anyway` unchanged. Import `quit_dialog_script` **parses as JS** (`node --check` or equivalent parser) and still contains `data-choice=cancel_and_quit`. Substring-only is a fail. Processing script still has no Quit and cancel and still parses. |
| `ExitRequested` routing | `sidecar.rs` or a tiny enum next to `close_decision` | D — [joe-cheung-cae/frame-pilot#31](https://github.com/joe-cheung-cae/frame-pilot/issues/31) | `ExitRequested` → prevent_exit + same `close_decision` as window close; Stay does not `request_shutdown`; `Exit` may drain. |

---

## A — F001+F006 terminate-on-error (and missing stdout)

**id:** F001+F006  
**issues:** [joe-cheung-cae/frame-pilot#33](https://github.com/joe-cheung-cae/frame-pilot/issues/33) (F001 high), [joe-cheung-cae/frame-pilot#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32) (F006 medium; **same implementation**)  
**depends-on:** none — do this first. Do not start B until this slice is committed.

**files:**
- modify: `apps/desktop/src-tauri/src/lib.rs` — `start_sidecar_process` (~66–76), `start_sidecar_with_retry`, `store_child` (~37–41)
- modify: `apps/desktop/src-tauri/src/sidecar.rs` — extract `SpawnedSidecar` (or equivalent) Drop/guard; keep `spawn_sidecar`, `wait_for_ready_line`, `terminate_sidecar`
- test: `apps/desktop/src-tauri/src/sidecar.rs` `#[cfg(test)]` (same crate `framepilot-desktop`; `lib.rs` has no `#[cfg(test)]`)

**implement:**
- After `spawn_sidecar`, wrap the child in a Drop/guard (`SpawnedSidecar { child: Child, armed: bool }` or equivalent) in `sidecar.rs`. `Drop` calls `terminate_sidecar` while armed. `into_child(self) -> Child` disarms. `start_sidecar_process` wraps spawn in that guard (**I1**).
- One terminate-on-error + wait path for every post-spawn `Err`: ready-line timeout, ready-line parse failure, **and missing stdout** (`stdout.take()` `None` → `"sidecar stdout missing"`). `std::process::Child` drop does not kill or wait.
- Health-fail already calls `terminate_sidecar`; keep that. Double-terminate after wait is OK (`terminate_sidecar` is idempotent via `try_wait`).
- Retry (`start_sidecar_with_retry`) reuses the same allocated loopback port and absolute `--data-dir`.
- **I2 / F006 shutdown-aware store (implement here, not in B):** if `shutdown` is already set, `store_child` takes the child and `terminate_sidecar`s it. A true no-op that returns without storing still **drops** the argument `Child` and leaks. Do not write a second F006 patch later.
- **N2:** Ready-line timeout may leave a stdout reader thread; that is acceptable once `terminate_sidecar` runs (pipe EOF). Do not “fix” it by leaking the process or skipping wait.
- Never leave an orphan sidecar after start failure or retry.

**tests-first:** write the failing guard/harness in `sidecar.rs` `#[cfg(test)]` **before** the implementation. Drive the shipped Drop/guard and `store_child` behavior. Do not mock `Child`. Do not re-implement the oracle in the test.
- After ready-line timeout or parse failure, `terminate_sidecar` (and wait) ran.
- **N1:** spawn a real child that **listens** on the allocated `127.0.0.1` port (or a process that binds that port and omits a valid ready line). A `sleep` child does not occupy the port, so it cannot prove “retry can bind the same port”.
- No leftover listener on the allocated loopback port; after terminate-and-wait the test must bind that port again; retry can bind the same port.
- Missing stdout also terminates the child before return.
- If `shutdown` is set, `store_child` terminates instead of storing.

Run: `cargo test` in `apps/desktop/src-tauri` (crate `framepilot-desktop`), **not** `npm run verify`. Capture `cargo-test-A.txt`. If `rustc`/`cargo` missing (exit 127), capture exact command+error; do not claim tests passed.

**commit-hint:** `desktop: terminate sidecar on ready-line failure`

**done-when:**
- Ready-line timeout/parse failure and missing stdout terminate-and-wait; no leftover listener; retry binds the same port.
- Shutdown-set `store_child` terminates instead of keeping the child (F006 closed here).
- Required subject is on the slice commit. F006 is not a second feature.

---

## B — F002 shutdown-aware supervisor / `store_child` / Drop

**id:** F002  
**issues:** [joe-cheung-cae/frame-pilot#35](https://github.com/joe-cheung-cae/frame-pilot/issues/35) (high)  
**depends-on:** A committed (`desktop: terminate sidecar on ready-line failure`). Do not start B before A is committed. Do not start C until this slice is committed.

**files:**
- modify: `apps/desktop/src-tauri/src/lib.rs` — `supervise_sidecar` (~178–213), `SidecarState`, `request_shutdown` (~43–50), `store_child`, `start_sidecar_process`
- modify if a tiny predicate is easier to test there: `apps/desktop/src-tauri/src/sidecar.rs`
- test: shipped helpers under `#[cfg(test)]` (prefer `sidecar.rs` or a tiny extracted predicate; do not require Tauri)

**implement:**
- Supervisor today checks `shutdown` only at the loop head, then `probe_health` 400ms, then Restart → `start_sidecar_process` → `store_child` with no re-check. `recovery_action(false, 1)` is `Restart`.
- Re-check `shutdown` after `probe_health` and immediately before `start_sidecar_process`. If shutdown is set, do **not** spawn; terminate any local `Child`.
- Prefer `SidecarState` `Drop` that always terminates (defense in depth; `Arc` drop is not the primary race fix).
- `store_child` may already terminate-on-shutdown from slice A; **keep that**. Add supervisor re-checks + Drop. This slice is **not** a second F006 patch (**I2**).
- `request_shutdown` today holds the child mutex for the whole SIGTERM/kill wait; do not widen that hold if a re-check can terminate a local child instead.

**tests-first:** write failing unit tests on shipped helpers **before** the implementation.
- If `shutdown` is set, `start_sidecar_process` / `store_child` do not keep a live child (terminate, do not drop).
- Re-check after `probe_health`; if `shutdown` is set, do not spawn.
- Any child spawned after shutdown is terminated before return.
- Helper-level: close/quit during the 400ms health probe leaves no sidecar.

Run: `cargo test` in `apps/desktop/src-tauri`. Capture `cargo-test-B.txt`.

**commit-hint:** `desktop: avoid sidecar respawn after shutdown`

**done-when:**
- Supervisor does not respawn after shutdown; post-shutdown spawn is terminated before return.
- `SidecarState` Drop always terminates (defense in depth).
- Required subject is on the slice commit. No second F006 patch.

---

## C — F003+F004 parseable import overlay + Stay fallback

**id:** F003+F004  
**issues:** [joe-cheung-cae/frame-pilot#36](https://github.com/joe-cheung-cae/frame-pilot/issues/36) (F003 high, **import-only**), [joe-cheung-cae/frame-pilot#34](https://github.com/joe-cheung-cae/frame-pilot/issues/34) (F004 medium). **Must land together.**  
**depends-on:** B committed (`desktop: avoid sidecar respawn after shutdown`). Do not start C before B is committed. Do not start D until this slice is committed.

**files:**
- modify: `apps/desktop/src-tauri/src/sidecar.rs` — `quit_dialog_script` (import `extra_button` ~150; `innerHTML` interpolation ~168); extract `close_choice_from_handshake` (or equivalent)
- modify: `apps/desktop/src-tauri/src/lib.rs` — `handle_close_requested` (~126–157)
- test: `sidecar.rs` `#[cfg(test)]` — real JS parse of the import script; handshake helper

**implement:**
- **F003 (import-only):** Import `extra_button` is a regular Rust string with real ASCII quotes interpolated into a double-quoted JS `innerHTML` assignment inside `r#"..."#` — SyntaxError. Overlay never mounts. Fix generation (DOM APIs, HTML entities, or the same backslash-quote escaping as the hardcoded buttons).
- Processing `extra_button` stays `""` and **must still parse**. Do not treat `quit_dialog_script_hides_cancel_for_processing_jobs` substring-only as F003 coverage.
- **F004:** Today F003 makes F004 the live import-close path (`eval` error → `finish_quit`; missing `dialog_shown` / unparsed payload → `.unwrap_or(CloseChoice::CancelAndQuit)` which POSTs cancel for import). After F003, a still-failing handshake must not unconfirmed-cancel.
- Extract `fn close_choice_from_handshake(payload: Option<&str>) -> CloseChoice` (**I3**): parseable `stay` / `cancel_and_quit` / `quit_anyway` map to those choices; **everything else** (timeout `None`, `dialog_shown`, junk, **`eval` `Err` treated as unresolved**) maps to `CloseChoice::Stay`. Stay resets `close_in_progress`. `CancelAndQuit` only from an explicit cancel-button payload. Quit anyway terminates without POST cancel.

**tests-first:** write the failing parser + handshake tests **before** the implementation. Substring-only is a **fail**.
- `quit_dialog_script(CloseJobKind::Import)` is syntactically valid JavaScript **and** contains `data-choice=cancel_and_quit`. Parse for real (`node --check` on the emitted script, or an equivalent parser).
- Processing script has no Quit and cancel; empty `extra_button` still parses.
- Handshake helper: `None` / invalid / `dialog_shown` / `eval` failure → `CloseChoice::Stay` and reset `close_in_progress`. Explicit `cancel_and_quit` and `quit_anyway` unchanged. Cancel POSTed only on the cancel button.

Run: `cargo test` in `apps/desktop/src-tauri` (and `node --check` if used). Capture `cargo-test-C.txt`.

**commit-hint:** `desktop: fix import quit dialog script and stay fallback`

**done-when:**
- Import overlay script parses as JS and still contains `data-choice=cancel_and_quit`.
- Unresolved handshake (timeout, junk, `eval` failure) is Stay; cancel POST only on the cancel button.
- F003 and F004 landed together. Required subject is on the slice commit.

---

## D — F005 `ExitRequested` `prevent_exit` + same `close_decision`

**id:** F005  
**issues:** [joe-cheung-cae/frame-pilot#31](https://github.com/joe-cheung-cae/frame-pilot/issues/31) (medium)  
**depends-on:** C committed (`desktop: fix import quit dialog script and stay fallback`). Do not start D before C is committed.

**files:**
- modify: `apps/desktop/src-tauri/src/lib.rs` — `app.run` (~337–340); reuse `handle_close_requested` or a shared helper; `prevent_exit` **before** the `close_in_progress` early-return (**I4**)
- modify: `apps/desktop/src-tauri/src/sidecar.rs` or a tiny enum next to `close_decision` — testable `ExitRequested` routing helper
- test: shipped routing helper under `#[cfg(test)]`
- may modify: `docs/handoff/STATUS.md` — `current_stage=开发`, `next_stage=测试`, A–D SHAs (STATUS may be updated in D)

**implement:**
- Today `matches!(event, RunEvent::Exit | RunEvent::ExitRequested { .. })` always `request_shutdown()`. `matches!` discards `ExitRequestApi`. Window close is already intercepted.
- `match` `RunEvent::ExitRequested { api, .. }`, call `api.prevent_exit()` **first**, then the same `close_decision` flow as `CloseRequested`.
- `request_shutdown` only after Stay is declined, and after `CancelThenTerminate` has waited up to `CANCEL_WAIT`. Stay keeps the sidecar alive. Quit and cancel import POSTs cancel. Quit anyway SIGTERMs without labelling the job `cancelled`.
- `RunEvent::Exit` may still drain (`request_shutdown`).
- Extract a testable routing helper: `ExitRequested` → prevent + dialog path; Stay does not `request_shutdown`; window close still maps through the same decision.

**tests-first:** write the failing routing-helper test **before** the implementation.
- `ExitRequested` is `prevent_exit`'d and routed through `close_decision`.
- Stay does not `request_shutdown`.
- Window close uses the same decision.
- `RunEvent::Exit` may still drain.

Run: `cargo test` in `apps/desktop/src-tauri`. Capture `cargo-test-D.txt`.

**commit-hint:** `desktop: route app quit through the close dialog`

**done-when:**
- Cmd+Q / `ExitRequested` shows the same close dialog as window close; `prevent_exit` runs first.
- Stay keeps the sidecar alive; cancel waits up to `CANCEL_WAIT` then SIGTERM; quit anyway is `failed` + retryable, not `cancelled`.
- Required subject is on the product-fix commit. STATUS may be updated in D (`current_stage=开发`, `next_stage=测试`); a docs-only extra commit is allowed if it still leaves the required product subject on the F005 commit.
- `开发` has finished with the four required subjects listed in Process.

---

## Required tests-first list (`开发` / `测试`)

Write the failing test before the implementation. Drive shipped functions. Do not mock the unit under test. Do not re-implement the oracle in the test. A substring-only test is **not** enough for the import overlay.

| Group | Write first | Must assert | Run |
|-------|-------------|-------------|-----|
| A. F001+F006 [joe-cheung-cae/frame-pilot#33](https://github.com/joe-cheung-cae/frame-pilot/issues/33) / [#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32) | Guard/harness in `sidecar.rs` `#[cfg(test)]` | After ready-line timeout or parse failure, `terminate_sidecar` (and wait) ran; no leftover listener on the allocated loopback port; retry can bind that port; missing stdout also terminates before return; if `shutdown` is set, `store_child` terminates instead of storing. Real child that **listens** (not only `sleep`). | `cargo test` in `apps/desktop/src-tauri` |
| B. F002 [joe-cheung-cae/frame-pilot#35](https://github.com/joe-cheung-cae/frame-pilot/issues/35) | Unit tests on shipped helpers | If `shutdown` is set, `start_sidecar_process` / `store_child` do not keep a live child; re-check after `probe_health`; child spawned after shutdown is terminated before return. | `cargo test` in `apps/desktop/src-tauri` |
| C. F003 [joe-cheung-cae/frame-pilot#36](https://github.com/joe-cheung-cae/frame-pilot/issues/36) | Parser test of emitted script | `quit_dialog_script(CloseJobKind::Import)` is syntactically valid JavaScript **and** contains `data-choice=cancel_and_quit`. Parse for real. Processing script has no Quit and cancel; empty `extra_button` still parses. | `cargo test` (and `node --check` if used) |
| C. F004 [joe-cheung-cae/frame-pilot#34](https://github.com/joe-cheung-cae/frame-pilot/issues/34) | Handshake helper | Timeout / invalid first payload / `eval` failure → `CloseChoice::Stay` and reset `close_in_progress`. Explicit cancel POSTs only on the cancel button. Quit anyway terminates without POST cancel. | `cargo test` in `apps/desktop/src-tauri` |
| D. F005 [joe-cheung-cae/frame-pilot#31](https://github.com/joe-cheung-cae/frame-pilot/issues/31) | ExitRequested routing helper | `ExitRequested` is `prevent_exit`'d and routed through `close_decision`; Stay does not `request_shutdown`; window close uses the same decision. | `cargo test` in `apps/desktop/src-tauri` |
| Regression | Existing tests | Do not weaken `test_cancelled_import_job_stops_safely_and_retry_preserves_review_state`. Do not add a processing cancel route. `npm run verify` does not invoke `rustc` / `cargo` / `tauri`. | `npm run test:web`; `npm run verify` with fail-if-invoked wrappers |

**`测试` stage verification plan** (binding):

1. `cargo test` in `apps/desktop/src-tauri` **twice**. Must include the new tests from A–D. Record count.
2. `npm run test:web` exit 0.
3. `npm run verify` exit 0 and rust-free (fail-if-invoked wrappers on PATH for `rustc`/`cargo`/`tauri`).
4. Do not run job pytest unless API changed (it should not).
5. If `tests/desktop/smoke.sh` or `npm run test:desktop:smoke` exists, run it.
6. GUI WebView of the overlay is not required if unit tests prove the import script parses and Stay is the unconfirmed fallback.
7. If `rustc`/`cargo` missing (exit 127), capture exact command+error; do not claim those tests passed; still run the non-Rust checks.

Keep existing path-import immutability and allowlist tests green. Never set `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME`.

---

## Acceptance boxes (ticked at `上线`)

Copied from the issues. Ticked 2026-08-20T11:13:12+08:00 after measured `测试` evidence (`cargo test` 35 passed twice, rustc/cargo 1.97.1; `npm run test:web`; `npm run verify` rust-free; `npm run test:desktop:smoke`). Do not close [joe-cheung-cae/frame-pilot#30](https://github.com/joe-cheung-cae/frame-pilot/issues/30) or the sub-issues. Do not open a PR. Do not merge to `main`.

- [x] F001 `#33`: no leftover listener after ready-line failure; retry binds the same port; missing stdout terminates; harness covers failure then retry. SHA `7a8bdba74bfe656a64fd4ae172cbbfd494707fb7`.
- [x] F002 `#35`: close/quit during the 400ms probe leaves no sidecar; `start_sidecar_process` / `store_child` do not keep a live child when `shutdown` is set (terminate, do not drop); post-shutdown spawn is terminated before return. SHA `c7cda3c20c93725aa5efe74e914e3d6e06e4cca6`.
- [x] F003 `#36`: import script parses as JS; still contains `data-choice=cancel_and_quit`; overlay mounts three buttons; parser test (not substring-only). SHA `2ae116392b169aac2c8b70551624dcfb64582654` (with F004).
- [x] F004 `#34`: unresolved handshake → Stay + reset `close_in_progress`; cancel POSTed only on the cancel button; quit anyway SIGTERMs without POST cancel. Lands with F003. Same SHA as F003.
- [x] F005 `#31`: Cmd+Q shows the same dialog; Stay keeps sidecar alive; cancel waits up to `CANCEL_WAIT` then SIGTERM; quit anyway is `failed` + retryable, not `cancelled`. `prevent_exit` first. SHA `2bd21f6922c47ab379929b0ff6f9dc3f830eac87`.
- [x] F006 `#32`: same as F001 plus shutdown-aware store; closed with F001, not a second patch. Same SHA as F001.

Parent `#30` retest (helper/harness-level; GUI WebView overlay click not required): ready-line timeout then retry; close during 400ms probe; close during import (Keep working stays); Cmd+Q during import (dialog, not immediate SIGTERM). `npm run verify` must not compile this crate (verified with fail-if-invoked wrappers).

---

## Out of scope

- Desktop Phases 2–5 (D2.00–D5.05). Do not start them.
- `APP_VERSION` bump. Stay `2.0.0-rc2`.
- Opening a PR, merging to `main`, or closing GitHub issues.
- D1.01–D1.09 redo. Phase 1 boxes stay `[x]`. Do not retick.
- A second F006 patch. F001 == F006 one change (slice A). Slice B is supervisor re-check + Drop only.
- Making `npm run verify` require `rustc`, `cargo`, or Tauri.
- Weakening `test_cancelled_import_job_stops_safely_and_retry_preserves_review_state`.
- Adding a processing-job cancel route. Labelling quit-anyway / SIGTERM as `cancelled`.
- Shipping `--port 0` on the Tauri spawn path. Relative `--data-dir`. Bind on `0.0.0.0`.
- `output: 'export'` on `apps/web`. `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST=$HOME`.
- Cloud / login / payment / telemetry / HEIC / RAW / XMP / bundled models.
- Adding `.grok/workflows/desktop-packaging-review.rhai` in this archive commit.

---

## Definition of done for this archive

- This file is the accepted contract for slices A–D with `depends-on`, `files`, `implement`, `tests-first`, `commit-hint`, and `done-when` on each id (F001+F006, F002, F003+F004, F005).
- Extra per-slice commits are allowed; `开发` must finish with the four required subjects; F006 is not a second feature.
- Review notes I1–I4 and N1–N3 are folded into slice implement / tests-first text.
- No production Rust / TypeScript / Python was changed in this `归档` commit.
- §5.1 Phase 1 boxes stay `[x]`. Next stage: `开发` slice A.

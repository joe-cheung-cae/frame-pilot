# Desktop Review-Fix Handoff Status

- current_stage: 测试
- status: complete
- files changed this stage: none (verification only; this STATUS handoff)
- tests_run: see below
- next_stage: 上线
- verdict: pass
- blockers: none
- branch: feature/desktop-packaging
- parent_issue: joe-cheung-cae/frame-pilot#30
- in_scope_sub_issues:
  - joe-cheung-cae/frame-pilot#33 (F001 high; slice A)
  - joe-cheung-cae/frame-pilot#35 (F002 high; slice B)
  - joe-cheung-cae/frame-pilot#36 (F003 high; slice C)
  - joe-cheung-cae/frame-pilot#34 (F004 medium; slice C)
  - joe-cheung-cae/frame-pilot#31 (F005 medium; slice D)
  - joe-cheung-cae/frame-pilot#32 (F006 medium; same implementation as F001; not a second patch)
- timestamp: 2026-08-20T11:04:47+08:00

Capture directory: `/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-501/desktop-review-fix`

Evidence copy: `/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-goal-7cc6541d0495/implementer`

## A–D commit SHAs

- A `7a8bdba74bfe656a64fd4ae172cbbfd494707fb7` — `desktop: terminate sidecar on ready-line failure` (F001 [joe-cheung-cae/frame-pilot#33](https://github.com/joe-cheung-cae/frame-pilot/issues/33) + F006 [joe-cheung-cae/frame-pilot#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32); one implementation)
- B `c7cda3c20c93725aa5efe74e914e3d6e06e4cca6` — `desktop: avoid sidecar respawn after shutdown` (F002 [joe-cheung-cae/frame-pilot#35](https://github.com/joe-cheung-cae/frame-pilot/issues/35))
- C `2ae116392b169aac2c8b70551624dcfb64582654` — `desktop: fix import quit dialog script and stay fallback` (F003 [joe-cheung-cae/frame-pilot#36](https://github.com/joe-cheung-cae/frame-pilot/issues/36) + F004 [joe-cheung-cae/frame-pilot#34](https://github.com/joe-cheung-cae/frame-pilot/issues/34))
- D `2bd21f6922c47ab379929b0ff6f9dc3f830eac87` — `desktop: route app quit through the close dialog` (F005 [joe-cheung-cae/frame-pilot#31](https://github.com/joe-cheung-cae/frame-pilot/issues/31))

## Tests run and results

`测试` re-ran the review-fix verification plan against the shipped tree at `350c607` (开发 close-out on `feature/desktop-packaging`). rustc/cargo **1.97.1** via user-space rustup (`~/.cargo/bin`). GUI WebView of the overlay was not required: unit tests prove the import script parses and Stay is the unconfirmed fallback.

1. `cargo test` in `apps/desktop/src-tauri` (crate `framepilot-desktop`) **twice** — **35 passed**, 0 failed, 0 ignored each run. Captures: `cargo-test-1.txt`, `cargo-test-2.txt`. New A–D tests included and green:
   - A/F001+F006: `ready_line_timeout_terminates_listener_and_retry_can_bind_same_port`, `ready_line_parse_failure_terminates_listener_and_frees_port`, `missing_stdout_terminates_child_before_return`, `store_child_terminates_when_shutdown_is_set`
   - B/F002: `start_sidecar_process_does_not_spawn_when_shutdown_is_set`, `start_sidecar_process_terminates_child_spawned_after_shutdown`, `start_sidecar_process_and_store_child_do_not_keep_live_child_when_shutdown_is_set`, `close_during_health_probe_leaves_no_sidecar`, `supervisor_rechecks_shutdown_after_health_probe`
   - C/F003+F004: `quit_dialog_script_import_is_valid_javascript_with_cancel_button`, `quit_dialog_script_processing_is_valid_javascript_without_cancel`, `close_choice_from_handshake_unresolved_stays`
   - D/F005: `app_quit_action_prevents_exit_requested_and_shares_close_decision_with_window_close`
2. `npm run test:web` — **exit 0**. Capture: `test-web.log`. Node lib tests **181 passed**; Vitest **8 passed** (4 files). Next.js 15.5.19 generated 7/7 pages; dynamic `projects/[projectId]` routes remain `ƒ`. No `output: export`.
3. `npm run verify` — **exit 0**. Fail-if-invoked wrappers for `rustc` / `cargo` / `rustup` / `tauri` were first on `PATH` (probe exits 99) and **were never called** during verify. Capture: `verify.log`. Included `lint` (ruff + eslint), `typecheck`, `typecheck:desktop`, pytest **214 passed**, `test:web`, `test:scripts`, `check:artifacts`. Did not invoke rustc, cargo, or Tauri.
4. Job pytest was not run as a separate command (API was not touched). Verify’s `test:api` still collected `test_job_reliability.py` (8 passed inside the 214).
5. `npm run test:desktop:smoke` — **exit 0**. Capture: `desktop-smoke.txt`. Health JSON `status`/`version`/`service`; `/api/projects` JSON array `[]`; desktop Origin OPTIONS HTTP 200; attacker Host HTTP 403 with visible detail. WebView half skipped with explicit message. `desktop-smoke ok port=55487`.

## Notes

Do not start Phase 2. Do not bump `APP_VERSION`. Do not redo D1.01–D1.09 product work. Do not open a PR, merge to `main`, or close GitHub issues. F006 is not a second patch. Acceptance boxes stay unticked until `上线`.

Sidecar still binds `127.0.0.1` only. Absolute `--data-dir`. Shipped spawn never `--port 0`. Import cancel stays cooperative. Quit-anyway / SIGTERM is failed + retryable, not cancelled. Processing jobs have no cancel route.

Next stage: `上线`.

# Desktop Review-Fix Handoff Status

- current_stage: 开发-B
- status: complete
- next_stage: 开发-C
- branch: feature/desktop-packaging
- parent_issue: joe-cheung-cae/frame-pilot#30
- in_scope_sub_issues:
  - joe-cheung-cae/frame-pilot#33 (F001 high; slice A committed)
  - joe-cheung-cae/frame-pilot#35 (F002 high; this slice)
  - joe-cheung-cae/frame-pilot#36 (F003 high)
  - joe-cheung-cae/frame-pilot#34 (F004 medium)
  - joe-cheung-cae/frame-pilot#31 (F005 medium)
  - joe-cheung-cae/frame-pilot#32 (F006 medium; same implementation as F001; not a second patch)
- tests_run: cargo test in apps/desktop/src-tauri (crate framepilot-desktop) — 31 passed, 0 failed
- timestamp: 2026-08-20T10:34:13+08:00
- verdict: pass
- blockers: none

Capture directory: `/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-501/desktop-review-fix`

Evidence copy: `/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-goal-7cc6541d0495/implementer`

## Tests run and results

`tests_run=cargo test` in `apps/desktop/src-tauri`. Capture: `cargo-test-B.txt`. 31 passed, 0 failed, 0 ignored. New F002 tests:

- `supervisor_rechecks_shutdown_after_health_probe`
- `start_sidecar_process_does_not_spawn_when_shutdown_is_set`
- `start_sidecar_process_terminates_child_spawned_after_shutdown`
- `start_sidecar_process_and_store_child_do_not_keep_live_child_when_shutdown_is_set`
- `start_sidecar_process_abandons_spawn_error_when_shutdown_is_set`
- `close_during_health_probe_leaves_no_sidecar`
- `sidecar_state_drop_terminates_stored_child`

Did not run `npm run test:web`, `npm run verify`, or pytest. Did not start slice C/D.

## Files changed

- `apps/desktop/src-tauri/src/sidecar.rs` — `supervisor_tick_after_probe`, `start_sidecar_unless_shutdown`, `SidecarState` with Drop that always terminates
- `apps/desktop/src-tauri/src/lib.rs` — `supervise_sidecar` re-checks shutdown after `probe_health` and immediately before `start_sidecar_process` / `store_child`
- `docs/handoff/STATUS.md` — this 开发-B handoff

## Notes

Slice A `desktop: terminate sidecar on ready-line failure` is already on `feature/desktop-packaging`. This slice is F002 ([joe-cheung-cae/frame-pilot#35](https://github.com/joe-cheung-cae/frame-pilot/issues/35)) only. F006 is not a second patch.

`store_child` still terminates instead of storing when `shutdown` is set (slice A). Supervisor now:

1. Re-checks `shutdown` after the 400ms `probe_health`.
2. Re-checks immediately before `start_sidecar_process`.
3. Does not spawn when shutdown is set; any child spawned after shutdown is terminated before return.
4. `SidecarState` Drop always terminates (defense in depth).

`request_shutdown` takes the child then terminates without holding the mutex for the SIGTERM/kill wait. Sidecar still binds `127.0.0.1` only. Absolute `--data-dir`. Shipped spawn never `--port 0`. `APP_VERSION` unchanged. `apps/web` unchanged. Phase 2 not started.

Next stage: `开发` slice C (`desktop: fix import quit dialog script and stay fallback`). Do not start D before C is committed. Do not open a PR, merge to `main`, or close GitHub issues.

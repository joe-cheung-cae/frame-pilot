# Desktop Review-Fix Handoff Status

- current_stage: 开发
- status: complete
- next_stage: 测试
- branch: feature/desktop-packaging
- parent_issue: joe-cheung-cae/frame-pilot#30
- in_scope_sub_issues:
  - joe-cheung-cae/frame-pilot#33 (F001 high; slice A)
  - joe-cheung-cae/frame-pilot#35 (F002 high; slice B)
  - joe-cheung-cae/frame-pilot#36 (F003 high; slice C)
  - joe-cheung-cae/frame-pilot#34 (F004 medium; slice C)
  - joe-cheung-cae/frame-pilot#31 (F005 medium; this slice)
  - joe-cheung-cae/frame-pilot#32 (F006 medium; same implementation as F001; not a second patch)
- tests_run: cargo test in apps/desktop/src-tauri (crate framepilot-desktop) — 35 passed, 0 failed
- timestamp: 2026-08-20T10:58:08+08:00
- verdict: pass
- blockers: none

Capture directory: `/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-501/desktop-review-fix`

Evidence copy: `/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-goal-7cc6541d0495/implementer`

## A–D commit SHAs

- A `7a8bdba74bfe656a64fd4ae172cbbfd494707fb7` — `desktop: terminate sidecar on ready-line failure` (F001 [joe-cheung-cae/frame-pilot#33](https://github.com/joe-cheung-cae/frame-pilot/issues/33) + F006 [joe-cheung-cae/frame-pilot#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32); one implementation)
- B `c7cda3c20c93725aa5efe74e914e3d6e06e4cca6` — `desktop: avoid sidecar respawn after shutdown` (F002 [joe-cheung-cae/frame-pilot#35](https://github.com/joe-cheung-cae/frame-pilot/issues/35))
- C `2ae116392b169aac2c8b70551624dcfb64582654` — `desktop: fix import quit dialog script and stay fallback` (F003 [joe-cheung-cae/frame-pilot#36](https://github.com/joe-cheung-cae/frame-pilot/issues/36) + F004 [joe-cheung-cae/frame-pilot#34](https://github.com/joe-cheung-cae/frame-pilot/issues/34))
- D `2bd21f6922c47ab379929b0ff6f9dc3f830eac87` — `desktop: route app quit through the close dialog` (F005 [joe-cheung-cae/frame-pilot#31](https://github.com/joe-cheung-cae/frame-pilot/issues/31))

## Tests run and results

`tests_run=cargo test` in `apps/desktop/src-tauri`. Capture: `cargo-test-D.txt`. 35 passed, 0 failed, 0 ignored. New F005 test:

- `app_quit_action_prevents_exit_requested_and_shares_close_decision_with_window_close` — `ExitRequested` (and window close) map to `PreventThenCloseDecision`; Stay does not `request_shutdown`; `RunEvent::Exit` and a confirmed quit drain via `RequestShutdown`

Did not run `npm run test:web`, `npm run verify`, or pytest.

## Files changed (this slice)

- `apps/desktop/src-tauri/src/sidecar.rs` — `app_quit_action` / `close_decision_requests_shutdown` routing helpers next to `close_decision`
- `apps/desktop/src-tauri/src/lib.rs` — `ExitRequested` calls `prevent_exit` first, then the same `handle_close_requested` / `close_decision` flow as window close; `RunEvent::Exit` still drains
- `docs/handoff/STATUS.md` — this 开发 close-out

## Notes

开发 A–D is complete on `feature/desktop-packaging`. F006 is not a second patch.

Cmd+Q / `ExitRequested` now `prevent_exit`s first and shares `close_decision` with window close. Stay keeps the sidecar alive and resets `close_in_progress`. Quit and cancel import POSTs cancel and waits up to `CANCEL_WAIT` before SIGTERM. Quit anyway SIGTERMs without labelling the job `cancelled`. After Stay is declined, a later `ExitRequested` drains instead of blocking exit. `RunEvent::Exit` may still `request_shutdown`.

Sidecar still binds `127.0.0.1` only. Absolute `--data-dir`. Shipped spawn never `--port 0`. `APP_VERSION` unchanged. `apps/web` unchanged. Phase 2 not started. No processing cancel route.

Next stage: `测试`. Do not open a PR, merge to `main`, or close GitHub issues.

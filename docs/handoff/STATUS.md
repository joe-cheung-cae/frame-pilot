# Desktop Review-Fix Handoff Status

- current_stage: 开发-C
- status: complete
- next_stage: 开发-D
- branch: feature/desktop-packaging
- parent_issue: joe-cheung-cae/frame-pilot#30
- in_scope_sub_issues:
  - joe-cheung-cae/frame-pilot#33 (F001 high; slice A committed)
  - joe-cheung-cae/frame-pilot#35 (F002 high; slice B committed)
  - joe-cheung-cae/frame-pilot#36 (F003 high; this slice)
  - joe-cheung-cae/frame-pilot#34 (F004 medium; this slice)
  - joe-cheung-cae/frame-pilot#31 (F005 medium)
  - joe-cheung-cae/frame-pilot#32 (F006 medium; same implementation as F001; not a second patch)
- tests_run: cargo test in apps/desktop/src-tauri (crate framepilot-desktop) — 34 passed, 0 failed
- timestamp: 2026-08-20T10:43:37+08:00
- verdict: pass
- blockers: none

Capture directory: `/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-501/desktop-review-fix`

Evidence copy: `/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-goal-7cc6541d0495/implementer`

## Tests run and results

`tests_run=cargo test` in `apps/desktop/src-tauri`. Capture: `cargo-test-C.txt`. 34 passed, 0 failed, 0 ignored. New F003+F004 tests:

- `quit_dialog_script_import_is_valid_javascript_with_cancel_button` — `node --check` on `quit_dialog_script(CloseJobKind::Import)` and `data-choice=cancel_and_quit`
- `quit_dialog_script_processing_is_valid_javascript_without_cancel` — processing script parses and has no Quit and cancel
- `close_choice_from_handshake_unresolved_stays` — `None` / invalid / `dialog_shown` → Stay; explicit `cancel_and_quit` and `quit_anyway` unchanged; import cancel POST only on the cancel button

Did not run `npm run test:web`, `npm run verify`, or pytest. Did not start slice D.

## Files changed

- `apps/desktop/src-tauri/src/sidecar.rs` — import `extra_button` is JS-safe (backslash-quoted `type` like the hardcoded buttons) and still contains `data-choice=cancel_and_quit`; `close_choice_from_handshake` maps unresolved payloads to Stay
- `apps/desktop/src-tauri/src/lib.rs` — `handle_close_requested` treats eval failure and handshake timeout as unresolved Stay and resets `close_in_progress`; `CancelAndQuit` only from an explicit button payload
- `docs/handoff/STATUS.md` — this 开发-C handoff

## Notes

Slices A and B are already on `feature/desktop-packaging`. This slice is F003 ([joe-cheung-cae/frame-pilot#36](https://github.com/joe-cheung-cae/frame-pilot/issues/36)) and F004 ([joe-cheung-cae/frame-pilot#34](https://github.com/joe-cheung-cae/frame-pilot/issues/34)) together. F006 is not a second patch.

Import overlay script now parses as JavaScript and still contains `data-choice=cancel_and_quit`. Processing `extra_button` stays empty, has no Quit and cancel, and still parses. Unresolved handshake (`None`, junk, `dialog_shown`, eval `Err`) is Stay and resets `close_in_progress`. Explicit cancel POSTs cancel for import only. Quit anyway terminates without POST cancel.

Sidecar still binds `127.0.0.1` only. Absolute `--data-dir`. Shipped spawn never `--port 0`. `APP_VERSION` unchanged. `apps/web` unchanged. Phase 2 not started. No processing cancel route.

Next stage: `开发` slice D (`desktop: route app quit through the close dialog`). Do not start D before C is committed. Do not open a PR, merge to `main`, or close GitHub issues.

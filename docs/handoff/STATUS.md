# Desktop Review-Fix Handoff Status

- current_stage: 归档
- status: in_progress
- next_stage: 开发
- branch: feature/desktop-packaging
- parent_issue: joe-cheung-cae/frame-pilot#30
- in_scope_sub_issues:
  - joe-cheung-cae/frame-pilot#33 (F001 high)
  - joe-cheung-cae/frame-pilot#35 (F002 high)
  - joe-cheung-cae/frame-pilot#36 (F003 high)
  - joe-cheung-cae/frame-pilot#34 (F004 medium)
  - joe-cheung-cae/frame-pilot#31 (F005 medium)
  - joe-cheung-cae/frame-pilot#32 (F006 medium; same implementation as F001)
- tests_run: none (docs)
- timestamp: 2026-08-20T10:40:00+08:00
- verdict: accept-with-notes
- blockers: none for this documentation stage. Production Rust/TS/Python was not changed.

Capture directory: `/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-501/desktop-review-fix`

Evidence copy: `/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-goal-7cc6541d0495/implementer`

## Tests run and results

`tests_run=none (docs)`. This stage is documentation only. No `cargo test`, `npm run test:web`, `npm run verify`, pytest, or desktop smoke was run. `docs/handoff/review-fix-review.md` already accepted the breakdown against live `lib.rs` / `sidecar.rs` / `package.json`.

## Files changed

- `docs/handoff/review-fix-backlog.md` — accepted A–D contract (F001+F006, F002, F003+F004, F005)
- `docs/handoff/STATUS.md` — this 归档 handoff
- `docs/handoff/review-fix-requirements.md` — 需求拆解 contract (include if still uncommitted)
- `docs/handoff/review-fix-review.md` — 评审 accept-with-notes (include if still uncommitted)
- `.grok/workflows/desktop-review-fix.rhai` — already-authored pipeline; include if untracked. Do not add `desktop-packaging-review.rhai`

## Notes

Branch confirmed `feature/desktop-packaging` at repo `/Users/chao/workspace/repo/frame-pilot`, parent review HEAD `7e545f80ad9205cc3a7ab67bf1683ab583743f24`.

评审 verdict **accept-with-notes** is folded into `docs/handoff/review-fix-backlog.md`. F006 is not a second feature.

`开发` slices (serial; extra per-slice commits allowed; must finish with these four required subjects; STATUS may be updated in D):

- A. F001+F006 — `desktop: terminate sidecar on ready-line failure`
- B. F002 — `desktop: avoid sidecar respawn after shutdown` (do not start before A is committed)
- C. F003+F004 — `desktop: fix import quit dialog script and stay fallback` (do not start before B is committed)
- D. F005 — `desktop: route app quit through the close dialog` (do not start before C is committed)

§5.1 Phase 1 boxes stay `[x]`. Do not start Phases 2–5. Do not bump `APP_VERSION`. Do not open a PR, merge to `main`, or close GitHub issues. `npm run verify` stays rust-free.

Next stage: `开发` slice A.

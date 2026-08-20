# Desktop review-fix loop — GitHub pull

Handoff stage: `GitHub pull`  
Date: 2026-08-20T14:38:04+08:00  
Branch: `feature/desktop-packaging`  
Live HEAD: `26bcc63d324ef29de84185c5032ad706d257516c`  
Base: `origin/main` `1d6ffa70858e6663f2539fb25d1358fecf519cd4`  
Repo: `joe-cheung-cae/frame-pilot`

This is a **new** review of live HEAD, not the 2026-08-20 review of `7e545f8`. Issues `#30`–`#36` stay **open** by prior contract. Still-open is not evidence they are still broken.

Orchestration: `.grok/workflows/desktop-review-fix-loop.rhai` (bounded review→code→re-review; per-stage write-allowlists; `capability_mode` read-only for Review/Verify).

Scratch dump: captured to the implementer scratch dir as `github-issues-pull.json.txt` via `gh issue view --json` (real API, not invented URLs).

## Parent

### joe-cheung-cae/frame-pilot#30

- Title: Full code review (2026-08-20) — feature/desktop-packaging @ 7e545f8
- State: OPEN
- URL: https://github.com/joe-cheung-cae/frame-pilot/issues/30
- Body: Review of HEAD `7e545f80ad9205cc3a7ab67bf1683ab583743f24` vs `origin/main`. Verdict **block**. Confirmed F001–F006 (3 high, 3 medium). No original-file mutation, cloud, login, or payment path found in that review.

Comments (2):

1. https://github.com/joe-cheung-cae/frame-pilot/issues/30#issuecomment-5349759856 (2026-08-20T00:42:04Z, joe-cheung-cae) — workflow artifact `desktop-packaging-review`; 19 agents; HEAD `7e545f8`; 6 confirmed findings.
2. https://github.com/joe-cheung-cae/frame-pilot/issues/30#issuecomment-5350923707 (2026-08-20T03:16:48Z, joe-cheung-cae) — review-fix close-out. Does **not** close #30. SHA index:

| Slice | Finding | Issue | SHA | Subject |
|-------|---------|-------|-----|---------|
| A | F001+F006 | #33 / #32 | `7a8bdba74bfe656a64fd4ae172cbbfd494707fb7` | desktop: terminate sidecar on ready-line failure |
| B | F002 | #35 | `c7cda3c20c93725aa5efe74e914e3d6e06e4cca6` | desktop: avoid sidecar respawn after shutdown |
| C | F003+F004 | #36 / #34 | `2ae116392b169aac2c8b70551624dcfb64582654` | desktop: fix import quit dialog script and stay fallback |
| D | F005 | #31 | `2bd21f6922c47ab379929b0ff6f9dc3f830eac87` | desktop: route app quit through the close dialog |
| 开发 STATUS | — | — | `350c6073e60b9bf2078193e9fc79d1461edcb868` | docs: record 开发 close-out A-D SHAs |
| 测试 | — | — | `68b8c60ce841ed8be76ab677799171c747634535` | test: verify desktop review-fix behavior |
| 上线 | — | — | `26bcc63d324ef29de84185c5032ad706d257516c` | docs: record desktop review-fix close-out |

Tests cited: `cargo test` twice, 35 passed; `npm run test:web` 0; `npm run verify` rust-free 0; `npm run test:desktop:smoke` 0.

## Sub-issues

### joe-cheung-cae/frame-pilot#31 — F005 medium

- Title: [F005][medium] App quit SIGTERMs the sidecar without the close dialog
- State: OPEN
- URL: https://github.com/joe-cheung-cae/frame-pilot/issues/31
- Body (as filed against `7e545f8`): `ExitRequested` matched with `Exit` and always `request_shutdown()`; `matches!` discarded `ExitRequestApi`.
- Comment: https://github.com/joe-cheung-cae/frame-pilot/issues/31#issuecomment-5350923333 — product SHA `2bd21f6`; `prevent_exit` first; same `close_decision` as window close. Does not close #31.

### joe-cheung-cae/frame-pilot#32 — F006 medium (same implementation as F001)

- Title: [F006][medium] Sidecar process leaked when ready-line wait fails
- State: OPEN
- URL: https://github.com/joe-cheung-cae/frame-pilot/issues/32
- Body (as filed against `7e545f8`): ready-line `?` dropped `Child` without `terminate_sidecar`.
- Comment: https://github.com/joe-cheung-cae/frame-pilot/issues/32#issuecomment-5350923510 — F001==F006 one implementation at `7a8bdba`; no second patch. Does not close #32.

### joe-cheung-cae/frame-pilot#33 — F001 high

- Title: [F001][high] Ready-line failure drops the sidecar without terminating it
- State: OPEN
- URL: https://github.com/joe-cheung-cae/frame-pilot/issues/33
- Body (as filed against `7e545f8`): same leak as F006; retry reuses loopback port and `--data-dir`.
- Comment: https://github.com/joe-cheung-cae/frame-pilot/issues/33#issuecomment-5350922489 — product SHA `7a8bdba`. Does not close #33.

### joe-cheung-cae/frame-pilot#34 — F004 medium

- Title: [F004][medium] Failed quit-dialog handshake defaults to cancel-and-quit
- State: OPEN
- URL: https://github.com/joe-cheung-cae/frame-pilot/issues/34
- Body (as filed against `7e545f8`): handshake timeout `unwrap_or(CancelAndQuit)` POSTed cancel without confirmation.
- Comment: https://github.com/joe-cheung-cae/frame-pilot/issues/34#issuecomment-5350923107 — F003+F004 landed together at `2ae1163`; unresolved handshake is Stay. Does not close #34.

### joe-cheung-cae/frame-pilot#35 — F002 high

- Title: [F002][high] Supervisor can respawn the sidecar after shutdown
- State: OPEN
- URL: https://github.com/joe-cheung-cae/frame-pilot/issues/35
- Body (as filed against `7e545f8`): close during 400ms health probe could Restart after the old child was taken.
- Comment: https://github.com/joe-cheung-cae/frame-pilot/issues/35#issuecomment-5350922709 — product SHA `c7cda3c`; not a second F006 patch. Does not close #35.

### joe-cheung-cae/frame-pilot#36 — F003 high

- Title: [F003][high] Import quit dialog script is invalid JavaScript
- State: OPEN
- URL: https://github.com/joe-cheung-cae/frame-pilot/issues/36
- Body (as filed against `7e545f8`): import `extra_button` quotes broke the JS `innerHTML` string.
- Comment: https://github.com/joe-cheung-cae/frame-pilot/issues/36#issuecomment-5350922883 — F003+F004 at `2ae1163`; import-only. Does not close #36.

## Reviewer instructions for this round

- Classify against **current** HEAD `26bcc63`, not `7e545f8`.
- Do not re-open F001–F006 as P0/P1 unless the live source still has the defect.
- Create new GitHub issues only for **new** confirmed P0/P1. Comment on an existing issue if it is the same defect.
- Do not close issues. Do not open a PR. Do not merge to `main`.

# Desktop review-fix loop — round 1 review

Handoff stage: `Handoff` (round 1)  
Date: 2026-08-20T14:55:31+08:00  
Branch: `feature/desktop-packaging`  
Live HEAD: `4415234217206bf12ca4ceef8490093bee573727`  
Base: `origin/main` `1d6ffa70858e6663f2539fb25d1358fecf519cd4`  
Parent: [joe-cheung-cae/frame-pilot#30](https://github.com/joe-cheung-cae/frame-pilot/issues/30)

This is a **new** adversarial review of **current HEAD**, not the 2026-08-20 review of `7e545f8`. GitHub issue bodies and comments for `#30` `#31` `#32` `#33` `#34` `#35` `#36` were read before classifying (`docs/handoff/loop-github.md`). Still-open issues are not evidence they are still broken.

Orchestration: `.grok/workflows/desktop-review-fix-loop.rhai`  
Review `capability_mode`: read-only. Verify `capability_mode`: read-only. This stage write-allowlist: `docs/handoff/loop-round-1-review.md` ; `docs/handoff/STATUS.md`.

**Totals after adversarial verify: P0=0 · P1=0 · confirmed product P2=0 · confirmed product P3=0.**

Empty confirmed-product list is valid because six area reviewers read live source plus the branch diff plus GitHub comments, and four skeptics independently re-read cited files. Loop-gating is satisfied: **P0=0 and P1=0**. Skip product patches this round.

---

## Panel

Six parallel reviewers (sidecar-rust, web-adapters, jobs-quit, security, tests, packaging) then four skeptics on the only candidate findings (all from tests).

| Area | Product P0/P1 | Notes |
|------|---------------|--------|
| sidecar-rust | none | F001/F002/F006 fixed on HEAD |
| web-adapters | none | `request` / URLs call `resolveApiBase()` at call time |
| jobs-quit | none | F003/F004/F005 fixed on HEAD |
| security | none | loopback, originals, CORS/Host, allowlist, no cloud |
| tests | none product | coverage leftover only (see below) |
| packaging | none | Vite aliases, rust-free verify, no `output: export` |

---

## F001–F006 checked against **current** code

| ID | Issue | Filed at | Still on HEAD `4415234`? | Evidence |
|----|-------|----------|--------------------------|----------|
| F001 | [joe-cheung-cae/frame-pilot#33](https://github.com/joe-cheung-cae/frame-pilot/issues/33) | `7e545f8` | **fixed** | `SpawnedSidecar` Drop terminates on ready-line/missing-stdout (`sidecar.rs` wait_ready / Drop; `lib.rs` `spawn_ready_sidecar`). Tests: `ready_line_timeout_terminates_listener_and_retry_can_bind_same_port`, `missing_stdout_terminates_child_before_return`. SHA `7a8bdba`. |
| F002 | [joe-cheung-cae/frame-pilot#35](https://github.com/joe-cheung-cae/frame-pilot/issues/35) | `7e545f8` | **fixed** | `supervisor_tick_after_probe` after `probe_health`; `start_sidecar_unless_shutdown`; `store_sidecar_child` terminates if shutdown. SHA `c7cda3c`. |
| F003 | [joe-cheung-cae/frame-pilot#36](https://github.com/joe-cheung-cae/frame-pilot/issues/36) | `7e545f8` | **fixed** | Import `extra_button` raw string; `quit_dialog_script_import_is_valid_javascript_with_cancel_button` uses `node --check`. SHA `2ae1163`. |
| F004 | [joe-cheung-cae/frame-pilot#34](https://github.com/joe-cheung-cae/frame-pilot/issues/34) | `7e545f8` | **fixed** | `close_choice_from_handshake` → Stay on `None`/junk; `handle_close_requested` eval `Err` → `None`; Stay resets `close_in_progress`. SHA `2ae1163`. |
| F005 | [joe-cheung-cae/frame-pilot#31](https://github.com/joe-cheung-cae/frame-pilot/issues/31) | `7e545f8` | **fixed** | `app_quit_action(ExitRequested)` → `PreventThenCloseDecision`; `api.prevent_exit()` first (`lib.rs`). SHA `2bd21f6`. |
| F006 | [joe-cheung-cae/frame-pilot#32](https://github.com/joe-cheung-cae/frame-pilot/issues/32) | `7e545f8` | **fixed** | Same implementation as F001 (`store_child_terminates_when_shutdown_is_set`). Not a second patch. SHA `7a8bdba`. |

Do not file F001–F006 again. Comment on the existing issues if restating the re-check; do not create new issues for them.

---

## Finding index (confirmed product defects)

None. **P0=0. P1=0.**

---

## Leftover coverage notes (not loop-gating; skeptics set `real=false` for product)

These came from the tests panel. Independent skeptics confirmed the **shipped** functions are correct; the notes are missing tests, not Phase-1 breakage. Recorded as P2/P3 leftover. Not slices. Not GitHub issues.

| ID | Severity | File | Title | Skeptic |
|----|----------|------|-------|---------|
| C001 | P2 | `apps/desktop/src-tauri/src/sidecar.rs:1105` | F004 helper test does not assert `close_in_progress` reset or cancel POST | product Stay-reset + import-only POST is live in `lib.rs:126-135`; `real=false` |
| C002 | P2 | `apps/desktop/src-tauri/src/sidecar.rs:938` | `sidecar_spawn_spec` test does not assert `--host 127.0.0.1`; `FRAMEPILOT_DESKTOP=1` untested | product hardcodes loopback host and sets the env in `spawn_sidecar`; `real=false` |
| C003 | P2 | `apps/web/src/lib/api.ts:220` | `request()` call-time base untested (URL helpers are) | `request` already calls `resolveApiBase()` at fetch; `real=false` |
| C004 | P3 | `apps/desktop/src/navigation.router.tsx:14` | desktop `Link` (`href`→`to`, drop prefetch) has no runtime test | adapter is correct; Vite alias + dist have no `next/link`; `real=false` |

---

## Security / Phase-1 correctness (checked)

- Original photos: import copies; cancel does not delete sources; export cleanup is under export root.
- Sidecar binds `127.0.0.1` only; shipped spawn never `--port 0`; `--data-dir` absolute.
- CORS/Host: desktop Origin allowed when `FRAMEPILOT_DESKTOP=1`; attacker Host 403.
- Path allowlist: project roots under data-dir/projects or explicit list; desktop spawn does not set `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST=$HOME`.
- Tauri capabilities: no `fs:` / `shell:`.
- No cloud, login, payment.
- `npm run verify` stays rust-free.
- `APP_VERSION` stays `2.0.0-rc2`.
- Missing Phase 2–5 (codesign, installers, auto-update, live WebView clicks) is **not** a defect.

---

## GitHub mapping

- No new confirmed P0/P1 → **do not create issues**.
- Same defects as `#31`–`#36` → **not still present**; comment on [joe-cheung-cae/frame-pilot#30](https://github.com/joe-cheung-cae/frame-pilot/issues/30) (parent at least) with this round’s HEAD, P0=0, P1=0, tests not re-run (docs-only). Optional follow-up comments on `#31`–`#36` that the re-review found the filed bugs still absent.
- Do not close issues. Do not open a PR. Do not merge to `main`.

---

## Verdict

**clean** for loop-gating. Next stage: Close-out (GitHub comments + STATUS). No Fix/Backlog/Code this round.

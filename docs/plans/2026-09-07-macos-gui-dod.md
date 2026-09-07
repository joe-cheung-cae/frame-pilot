# Leftover: dual-platform installer GUI DoD (macOS DMG install+run)

> Language: **English** | [中文](2026-09-07-macos-gui-dod.zh.md)

**GitHub:** [joe-cheung-cae/frame-pilot#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177). Created 2026-09-07 after search found no matching leftover issue (open: none; latest leftover was closed [#175](https://github.com/joe-cheung-cae/frame-pilot/issues/175); latest PR was [#176](https://github.com/joe-cheung-cae/frame-pilot/pull/176)). Do not reopen [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172). Windows pass remains [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144).

**Branch:** `feature/macos-gui-dod` from `origin/main`. Isolation worktree is false. Do not checkout `main` for commits. Do not merge to `main`. Do not squash. Do not force-push.

**Related:** `develop_plan.md` §1.1; `docs/desktop_development_plan.md` §2.2 and §5.6; `docs/desktop_testing.md` S9.12 skip record; workflow `.grok/workflows/macos-gui-dod.rhai`.

This 需求拆解 commit is documentation contract only. Do not implement the smoke script or edit `.github/workflows/desktop.yml` yet.

---

## 1. Why leftover, not Phase 10

Phase 9 remaining-stretch (S9.00–S9.13) is closed on `main` ([#174](https://github.com/joe-cheung-cae/frame-pilot/pull/174)). Leftover cache knobs shipped ([#175](https://github.com/joe-cheung-cae/frame-pilot/issues/175)).

The living pointer still lists **macOS GUI pass** as unscheduled. Dual-platform installer GUI DoD is **not claimed**: Windows NSIS GUI is a pass ([#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144), closed Windows-only 2026-09-04); S9.12 packaged macOS DMG GUI lifecycle ([#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172)) is **skip, not pass**, dated `2026-09-05T12:31:10Z` (Linux/WSL2; `uname -s` is not Darwin). Skip is not a macOS pass.

The user-approved leftover is **install+run DoD**, not a full S9.12 lifecycle re-run and not a new numbered phase. Do **not** invent Phase 10 / S10 / 2.3. Tick `docs/desktop_development_plan.md` §2.2 installer row **only** after dated Darwin evidence from a green `desktop.yml` macOS GUI smoke.

---

## 2. Locked decisions

1. **Local-first.** No cloud upload, login, payment, or bundled neural models.
2. **Never modify or delete original photos.** This leftover smoke does not import photos. Do not commit camera photos, certs, or model weights.
3. **DoD is install+run**, not the full S9.12 quit+job matrix. Same-job DMG attach + launch + loopback `GET /health` is enough to tick §2.2.
4. **Skip ≠ pass.** Keep the S9.12 skip subsection in `docs/desktop_testing.md` as history. A new dated Darwin results subsection is required for a pass.
5. **Windows is already pass.** Do not re-run Windows NSIS GUI. Do not reopen #144 as a macOS vehicle.
6. **Do not reopen #172.** New leftover issue is [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177) only.
7. **CI same-job DMG**, not a downloaded artifact from another job. Wire macOS only, after `npx tauri build --bundles dmg`, against `apps/desktop/src-tauri/target/release/bundle/dmg/*.dmg`.
8. **`verify.yml` stays rust-free.** Do not launch packaged GUI from `verify.yml`. `npm run verify` must not require `rustc` / `cargo` / Tauri.
9. **Darwin-only attach/launch.** Non-Darwin hosts must print that skip is not pass and exit non-zero (use 2). Never print pass on Linux.
10. **No `APP_VERSION` bump.** Product name / window title stay `FramePilot`. Version stays `2.1.0-desktop`.
11. **Do not sign.** Do not claim Gatekeeper-clean or store listing. Unsigned Gatekeeper warnings remain expected.
12. **Do not tick packaged-desktop ≥500 GUI.** Web Playwright `test:e2e:real-browser:large` and API `perf:api` 500 are not packaged-desktop GUI evidence.
13. **Scratch:** `mkdir -p "$HOME/.cache/framepilot-macos-gui-dod" && chmod 700` that directory. Never `/tmp` for secrets or QA photos.
14. **English** for code, comments, tests, commits. **Bilingual** living docs.
15. **One draft PR** for `feature/macos-gui-dod` into `main`. Title: `ci: macOS DMG installer GUI smoke (leftover DoD)`. Body says `Refs` [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177); must not say `Fixes` or `Close` until the evidence commit (上线) when `desktop.yml` macOS GUI smoke is green. Never a second PR.
16. **Out:** Phase 10, packaged-desktop ≥500 GUI, signing, Windows re-run, full quit+job matrix, `APP_VERSION` bump.

---

## 3. Status board

Leftover dual-platform installer GUI DoD (macOS DMG install+run)

- [x] 需求拆解 — bilingual leftover plan + GitHub issue (this commit)
- [ ] 评审
- [ ] 归档
- [ ] 开发 — smoke script + `desktop.yml` macOS step; leftover-plan 开发 `[x]` in that commit; **do not** tick §2.2
- [ ] 测试
- [ ] 上线 — dispatch `desktop.yml`, dated Darwin evidence, then tick §2.2
- [ ] smoke-landed
- [ ] DoD-ticked

This 需求拆解 commit ticks **需求拆解** only. Leave 开发 and DoD-ticked `[ ]`.

---

## 4. Smoke script contract (开发, not this commit)

**Tests first.** Add `tests/desktop/macos-dmg-gui-smoke-nondarwin.sh` (or equivalent) that runs `packaging/scripts/macos-dmg-gui-smoke.sh` on this host and asserts non-zero exit **and** stdout/stderr contains `skip is not pass`. Watch it fail because the smoke script is missing, then implement the smoke script so the host check passes on Linux.

Create `packaging/scripts/macos-dmg-gui-smoke.sh` with `set -euo pipefail`. Darwin-only for the attach/launch path.

Required behavior:

1. If `uname -s` is not Darwin, print that skip is not pass, exit non-zero (use 2). Never print pass on Linux.
2. Require a `.dmg` path argument. `hdiutil attach -nobrowse`. Copy `FramePilot.app` to a throwaway directory under `$HOME/.cache/framepilot-macos-gui-dod` (not `/tmp`). `xattr -cr` the copy. `open` the `.app`.
3. Poll up to 30s (one retry of `open` if needed) for sidecar ready: parse `~/Library/Application Support/FramePilot/logs/sidecar.log` for `FRAMEPILOT_API ready host=127.0.0.1 port=<n>` **or** `lsof` listen of `framepilot-api` on `127.0.0.1`. Reject `0.0.0.0`. Never hardcode ports `8000`/`6300`.
4. `GET http://127.0.0.1:<n>/health` must be 200 JSON with `version` and `service`. Print `APP_VERSION`.
5. Best-effort window title `FramePilot` via `lsappinfo` or `osascript`. If that fails, record `title_ok=false` with the exact error; still pass the smoke if process+health succeeded.
6. Quit the app; wait; no leftover `framepilot-api` LISTEN (`TIME_WAIT` ok). `hdiutil detach`. Delete the copied `.app`. Data directory may remain.
7. Print a machine-readable summary: `os`, utc ISO-8601 timestamp with `Z`, health json, port, `title_ok`, `result=pass`.

Do not import photos. Do not automate quit+import/processing/export dialogs.

Ready-line and log path (live tree, do not change in this leftover unless required):

- Ready prefix: `FRAMEPILOT_API ready ` (`apps/desktop/src-tauri/src/sidecar.rs`)
- Format: `FRAMEPILOT_API ready host=127.0.0.1 port=<n> data_dir=<path>`
- Packaged log: `{data_dir}/logs/sidecar.log` → macOS `~/Library/Application Support/FramePilot/logs/sidecar.log`
- Window title / productName: `FramePilot` (`apps/desktop/src-tauri/tauri.conf.json`)
- Sidecar staging: `packaging/scripts/stage-sidecar.sh` copies `dist/framepilot-api` into `apps/desktop/src-tauri/resources/framepilot-api`

Prefer zero Rust/Python/TypeScript production edits. Do not edit `verify.yml`. Do not add Playwright GUI. Do not add pytest that opens a WebView.

---

## 5. `desktop.yml` macOS-only wiring (开发, not this commit)

Today `.github/workflows/desktop.yml` builds NSIS/DMG, runs frozen sidecar `/health`, uploads artifacts, and **does not** launch the packaged GUI. Header says: do not launch the packaged NSIS/DMG GUI.

开发 must:

- Wire the smoke into the **macOS job only**, after `npx tauri build --bundles dmg`, against the just-built `apps/desktop/src-tauri/target/release/bundle/dmg/*.dmg`.
- Update the header: packaged GUI launch is allowed on macOS for this smoke; still do not launch NSIS; still do not launch GUI from `verify.yml`.
- Keep Windows on the existing unsigned/signed NSIS upload path with no GUI launch.

---

## 6. Tick rules

| When | Tick | Do not tick |
| ---- | ---- | ----------- |
| 需求拆解 (this commit) | leftover board 需求拆解 `[x]` | 开发, DoD-ticked, §2.2 installer row |
| 开发 | leftover board 开发 `[x]`; smoke-landed `[x]` only if the named host check passed | §2.2 installer row; DoD-ticked |
| 上线 green Darwin smoke | leftover board 上线 `[x]` and DoD-ticked `[x]`; `docs/desktop_development_plan.md` §2.2 installer row `[x]` with Windows #144 + leftover [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177) + Actions run URL; §5.6 packaged macOS GUI pass target = this leftover `[x]` for **install+run** DoD, note full quit+job matrix still unscheduled | packaged-desktop ≥500; Gatekeeper-clean; store listing; Phase 10 |

Green evidence commit subject (上线 only): `docs: record dual-platform installer GUI DoD pass`.

That commit **must** add a **new** dated results subsection in `docs/desktop_testing.md` (+ zh) keeping the S9.12 skip subsection as history; update `develop_plan.md` §1.1 (+ zh), `docs/v2_known_limitations.md` (+ zh), `README.md` (+ zh), CHANGELOG Unreleased (+ zh), `implement_goals.md` (+ zh). Use ISO-8601 timestamps with timezone (UTC `Z` is fine).

Red or skip path: do **not** tick §2.2. Comment leftover [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177) with run URL and failure excerpt. DoD not claimed.

---

## 7. Non-goals

- Phase 10 / S10 / 2.3 numbering
- Packaged-desktop ≥500 GUI
- Signing, notarization, Gatekeeper-clean claim, store listing
- Windows NSIS GUI re-run
- Full S9.12 quit+import/processing/export dialog matrix
- `APP_VERSION` bump
- Launching packaged GUI from `verify.yml`
- Photo import in this leftover smoke
- Reopening #172
- Second PR; merge to `main`; squash; force-push

---

## 8. File map

| File | This commit | 开发 | 上线 |
| ---- | ----------- | ---- | ---- |
| `docs/plans/2026-09-07-macos-gui-dod.md` (+ zh) | create; 需求拆解 `[x]` | tick 开发 | tick 上线 + DoD-ticked |
| `.grok/workflows/macos-gui-dod.rhai` | include if present | unchanged | unchanged |
| `packaging/scripts/macos-dmg-gui-smoke.sh` | out | create | unchanged |
| `tests/desktop/macos-dmg-gui-smoke-nondarwin.sh` | out | create | unchanged |
| `.github/workflows/desktop.yml` | out | macOS smoke step + header | unchanged |
| `.github/workflows/verify.yml` | out | **do not edit** | **do not edit** |
| `docs/desktop_development_plan.md` (+ zh) §2.2 | **do not tick** | **do not tick** | tick installer row only if Darwin green |
| `docs/desktop_testing.md` (+ zh) | out | out | new dated results subsection; keep S9.12 skip |
| `develop_plan.md` §1.1, known limitations, README, CHANGELOG, `implement_goals.md` (+ zh) | out | out | evidence commit only |

---

## 9. GitHub / PR

After every finished stage commit: `git push -u origin HEAD`. After the first successful push of this branch, if no open PR exists for head `feature/macos-gui-dod` against `main`, create **one** draft PR:

- Title: `ci: macOS DMG installer GUI smoke (leftover DoD)`
- Body: `Refs` [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177); `Refs` #144 / #172 as historical. Must not say `Fixes` or `Close` until the evidence commit (上线). Never `Fixes #172`.

Fallback: GitHub MCP `create_pull_request` with `draft` true. Never a second PR.

Append SHA, subject, push result, and PR URL to `$HOME/.cache/framepilot-macos-gui-dod/git-github.txt` after every push.

If commit fails with empty ident, set `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME`, `GIT_COMMITTER_EMAIL` for that command only to match `git log -1 --format='%an <%ae>'`. Do not add Co-authored-by Cursor or similar trailers. Do not run `git config --global` or `git config user.name`.

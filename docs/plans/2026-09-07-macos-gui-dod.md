# Leftover: dual-platform installer GUI DoD (macOS DMG install+run)

> Language: **English** | [中文](2026-09-07-macos-gui-dod.zh.md)

**GitHub:** [joe-cheung-cae/frame-pilot#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177). Created 2026-09-07 after search found no matching leftover issue (open: none; latest leftover was closed [#175](https://github.com/joe-cheung-cae/frame-pilot/issues/175); latest PR was [#176](https://github.com/joe-cheung-cae/frame-pilot/pull/176)). Do not reopen [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172). Windows pass remains [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144).

**Branch:** `feature/macos-gui-dod` from `origin/main`. Isolation worktree is false. Do not checkout `main` for commits. Do not merge to `main`. Do not squash. Do not force-push.

**Related:** `develop_plan.md` §1.1; `docs/desktop_development_plan.md` §2.2 and §5.6; `docs/desktop_testing.md` S9.12 skip record; workflow `.grok/workflows/macos-gui-dod.rhai`.

需求拆解 was documentation contract only. This 评审 commit corrects spec holes against the live tree. Do not implement the smoke script or edit `.github/workflows/desktop.yml` yet. Do not tick 开发, DoD-ticked, or §2.2.

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
7. **CI same-job DMG**, not a downloaded artifact. Live tree `.github/workflows/desktop.yml` is one matrix `build` job (`os: [windows-latest, macos-latest]`), not a separate macOS job. Add a **new** step on that existing job, gated `if: runner.os == 'macOS'`, after `npx tauri build --bundles dmg`, against the just-built `apps/desktop/src-tauri/target/release/bundle/dmg/*.dmg`. Do not add a second job that downloads `FramePilot-macos-dmg`. Do not fold the smoke into the `Build Tauri installer` step (`scripts/test-release-checks.sh` forbids `exit 1` there).
8. **`verify.yml` stays rust-free.** Do not launch packaged GUI from `verify.yml`. `npm run verify` must not require `rustc` / `cargo` / Tauri (`typecheck:desktop` is `tsc --noEmit`).
9. **Darwin-only attach/launch.** Non-Darwin hosts (Linux/WSL2 开发/测试) must print that skip is not pass and exit non-zero (use 2). Never print pass on Linux. GitHub-hosted `macos-latest` is Darwin (`uname -s`); the attach/launch path **must** run there. Do not treat that runner as the S9.12 Linux skip.
10. **No `APP_VERSION` bump.** Product name / window title stay `FramePilot`. Version stays `2.1.0-desktop`.
11. **Do not sign in this leftover.** Do not require secrets, do not add signing/notarization, and do not claim Gatekeeper-clean or store listing. Keep the existing S9.11 secret-gated sign/notarize branch in `desktop.yml` unchanged (do not strip it). Unsigned Gatekeeper warnings remain expected when secrets are absent.
12. **Do not tick packaged-desktop ≥500 GUI.** Web Playwright `test:e2e:real-browser:large` and API `perf:api` 500 are not packaged-desktop GUI evidence.
13. **Scratch:** `mkdir -p "$HOME/.cache/framepilot-macos-gui-dod" && chmod 700` that directory. Never `/tmp` for secrets or QA photos.
14. **English** for code, comments, tests, commits. **Bilingual** living docs.
15. **One draft PR** for `feature/macos-gui-dod` into `main`. Title: `ci: macOS DMG installer GUI smoke (leftover DoD)`. Body says `Refs` [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177); must not say `Fixes` or `Close` until the evidence commit (上线) when `desktop.yml` macOS GUI smoke is green. Never a second PR.
16. **Out:** Phase 10, packaged-desktop ≥500 GUI, signing, Windows re-run, full quit+job matrix, `APP_VERSION` bump.

---

## 3. Status board

Leftover dual-platform installer GUI DoD (macOS DMG install+run)

- [x] 需求拆解 — bilingual leftover plan + GitHub issue
- [x] 评审 — adversarial review vs live tree (this commit)
- [ ] 归档
- [ ] 开发 — smoke script + `desktop.yml` macOS step; leftover-plan 开发 `[x]` in that commit; **do not** tick §2.2
- [ ] 测试
- [ ] 上线 — dispatch `desktop.yml`, dated Darwin evidence, then tick §2.2
- [ ] smoke-landed
- [ ] DoD-ticked

This 评审 commit ticks **评审** only. Leave 开发, DoD-ticked, and §2.2 `[ ]`.

---

## 4. Smoke script contract (开发, not this commit)

**Tests first.** Add `tests/desktop/macos-dmg-gui-smoke-nondarwin.sh` (or equivalent) that runs `packaging/scripts/macos-dmg-gui-smoke.sh` on this host and asserts non-zero exit **and** stdout/stderr contains `skip is not pass`. Watch it fail because the smoke script is missing, then implement the smoke script so the host check passes on Linux.

Create `packaging/scripts/macos-dmg-gui-smoke.sh` with `set -euo pipefail`. Darwin-only for the attach/launch path.

Required behavior:

1. If `uname -s` is not Darwin, print that skip is not pass, exit non-zero (use 2). Never print pass on Linux.
2. Require a `.dmg` path argument. `hdiutil attach -nobrowse`. Copy `FramePilot.app` to a throwaway directory under `$HOME/.cache/framepilot-macos-gui-dod` (not `/tmp`). `xattr -cr` the copy. `open` the `.app`.
3. Poll up to 30s (one retry of `open` if needed) for sidecar ready. **Do not treat `{data_dir}/logs/sidecar.log` as the ready-line source.** Live tree: `sidecar_main.py` prints `FRAMEPILOT_API ready host=127.0.0.1 port=<n> data_dir=<path>` to **stdout**; `spawn_sidecar` pipes stdout to the Tauri parent and appends **stderr** (uvicorn) to sidecar.log. Desktop allocates an ephemeral port via `allocate_loopback_port()` and passes `--port <n>` (never `--port 0`). Discover the port from `framepilot-api` argv `--port` **or** `lsof` LISTEN of `framepilot-api` on `127.0.0.1`. Reject `0.0.0.0`. Never hardcode ports `8000`/`6300`. Never trust a uvicorn “running on …:8000” line in sidecar.log (Config default is 8000; the bound port is the allocated one). Optionally scan sidecar.log for the ready prefix if present; **absence is not failure**.
4. `GET http://127.0.0.1:<n>/health` must be 200 JSON with `version` and `service` (live payload also has `status`). Print `APP_VERSION`. Bypass proxy like `tests/desktop/smoke.sh` (`curl --noproxy '*'` and/or unset `http_proxy`/`HTTP_PROXY`).
5. Best-effort window title `FramePilot` via `lsappinfo` or `osascript`. If that fails, record `title_ok=false` with the exact error; still pass the smoke if process+health succeeded.
6. Quit `FramePilot.app` (sidecar is a child of that process); wait; no leftover `framepilot-api` LISTEN (`TIME_WAIT` ok). Killing only `framepilot-api` is not a GUI quit. `hdiutil detach`. Delete the copied `.app`. Data directory may remain (`~/Library/Application Support/FramePilot`, not `com.framepilot.app`).
7. Print a machine-readable summary: `os`, utc ISO-8601 timestamp with `Z`, health json, port, `title_ok`, `result=pass`.

Do not import photos. Do not automate quit+import/processing/export dialogs.

Ready-line and log path (live tree, do not change in this leftover unless required):

- Ready prefix: `FRAMEPILOT_API ready ` (`apps/desktop/src-tauri/src/sidecar.rs`)
- Format: `FRAMEPILOT_API ready host=127.0.0.1 port=<n> data_dir=<path>` (stdout of `framepilot-api`, consumed by Tauri; **not** guaranteed in sidecar.log)
- Frozen binary: `framepilot-api` with argv `--host 127.0.0.1 --port <n> --data-dir <abs>`
- Packaged log: `{data_dir}/logs/sidecar.log` is **stderr** → macOS `~/Library/Application Support/FramePilot/logs/sidecar.log`
- Window title / productName: `FramePilot` (`apps/desktop/src-tauri/tauri.conf.json`); identifier `com.framepilot.app` is not the data-dir folder name
- Sidecar staging: `packaging/scripts/stage-sidecar.sh` copies `dist/framepilot-api` into `apps/desktop/src-tauri/resources/framepilot-api`

Prefer zero Rust/Python/TypeScript production edits. Do not edit `verify.yml`. Do not add Playwright GUI. Do not add pytest that opens a WebView.

---

## 5. `desktop.yml` macOS-only wiring (开发, not this commit)

Today `.github/workflows/desktop.yml` is a **single matrix `build` job** (`windows-latest` + `macos-latest`, `fail-fast: false`). It builds NSIS/DMG, runs frozen sidecar `/health`, uploads artifacts, and **does not** launch the packaged GUI. Header says: do not launch the packaged NSIS/DMG GUI. `on:` is `workflow_dispatch` plus push to `main` with path filters (PRs do not run this workflow).

开发 must:

- Add a **new** step on that existing `build` job, `if: runner.os == 'macOS'` (same gate as `Upload macOS DMG`), after `npx tauri build --bundles dmg`, against the just-built `apps/desktop/src-tauri/target/release/bundle/dmg/*.dmg` (repo-root path; the build step’s `working-directory` is `apps/desktop`).
- Do not add a follow-on job that `needs:` the matrix and downloads `FramePilot-macos-dmg`.
- Do not put `hdiutil` / `open` / the smoke inside the `Build Tauri installer` step.
- Update the header: packaged GUI launch is allowed on macOS for this smoke; still do not launch NSIS; still do not launch GUI from `verify.yml`.
- Keep Windows on the existing unsigned/signed NSIS upload path with no GUI launch. Keep S9.11 secret-gated signing as-is.
- Keep `scripts/test-release-checks.sh` green (`npm run test` includes `test:scripts`). Edit it only if a new assertion is required.

---

## 6. Tick rules

| When | Tick | Do not tick |
| ---- | ---- | ----------- |
| 需求拆解 | leftover board 需求拆解 `[x]` | 开发, DoD-ticked, §2.2 installer row |
| 评审 (this commit) | leftover board 评审 `[x]` | 开发, DoD-ticked, §2.2 installer row |
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

| File | 需求拆解 | 评审 (this commit) | 开发 | 上线 |
| ---- | -------- | ------------------ | ---- | ---- |
| `docs/plans/2026-09-07-macos-gui-dod.md` (+ zh) | create; 需求拆解 `[x]` | holes + 评审 `[x]` | tick 开发 | tick 上线 + DoD-ticked |
| `.grok/workflows/macos-gui-dod.rhai` | include if present | unchanged | unchanged | unchanged |
| `packaging/scripts/macos-dmg-gui-smoke.sh` | out | out | create | unchanged |
| `tests/desktop/macos-dmg-gui-smoke-nondarwin.sh` | out | out | create | unchanged |
| `.github/workflows/desktop.yml` | out | out | new macOS-gated step + header | unchanged |
| `.github/workflows/verify.yml` | out | out | **do not edit** | **do not edit** |
| `scripts/test-release-checks.sh` | out | out | keep green; edit only if a new assertion is required | out |
| `docs/desktop_development_plan.md` (+ zh) §2.2 | **do not tick** | **do not tick** | **do not tick** | tick installer row only if Darwin green |
| `docs/desktop_testing.md` (+ zh) | out | out | out | new dated results subsection; keep S9.12 skip |
| `develop_plan.md` §1.1, known limitations, README, CHANGELOG, `implement_goals.md` (+ zh) | out | out | out | evidence commit only |

开发 follows **this reviewed plan**, not the pre-review sidecar.log wording still duplicated in `.grok/workflows/macos-gui-dod.rhai` `develop_prompt`.

---

## 9. GitHub / PR

After every finished stage commit: `git push -u origin HEAD`. After the first successful push of this branch, if no open PR exists for head `feature/macos-gui-dod` against `main`, create **one** draft PR:

- Title: `ci: macOS DMG installer GUI smoke (leftover DoD)`
- Body: `Refs` [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177); `Refs` #144 / #172 as historical. Must not say `Fixes` or `Close` until the evidence commit (上线). Never `Fixes #172`.

Fallback: GitHub MCP `create_pull_request` with `draft` true. Never a second PR.

Append SHA, subject, push result, and PR URL to `$HOME/.cache/framepilot-macos-gui-dod/git-github.txt` after every push.

If commit fails with empty ident, set `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME`, `GIT_COMMITTER_EMAIL` for that command only to match `git log -1 --format='%an <%ae>'`. Do not add Co-authored-by Cursor or similar trailers. Do not run `git config --global` or `git config user.name`.

---

## 10. Review findings (评审, 2026-09-07)

Reviewed against the live tree on `feature/macos-gui-dod` after 需求拆解. Confirmed:

- DoD is **install+run**, not a full S9.12 quit+job matrix. `docs/desktop_development_plan.md` §2.2 installer row is still `[ ]`. Do not tick it in 开发.
- S9.12 in `docs/desktop_testing.md` is **skip, not pass** at `2026-09-05T12:31:10Z` (Linux/WSL2). Keep that subsection. Do not reopen [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172).
- Windows NSIS GUI pass remains closed [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144) (Windows-only, 2026-09-04). Do not re-run.
- Leftover issue is [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177) (matches GitHub). Draft PR is [#178](https://github.com/joe-cheung-cae/frame-pilot/pull/178). No Phase 10 / S10 / 2.3.
- `.github/workflows/verify.yml` does not install Rust; `npm run verify` is lint / typecheck / `tsc --noEmit` / pytest / `test:scripts`. Stays rust-free. Do not launch GUI from `verify.yml`.
- `APP_VERSION` / productName / window title are `2.1.0-desktop` / `FramePilot`. Do not bump.
- Packaged macOS data dir is `~/Library/Application Support/FramePilot` (`apps/desktop/src-tauri/src/data_dir.rs`), not `com.framepilot.app`.
- Health is `GET /health` → JSON `status`, `version`, `service`.

Holes fixed in this commit (live tree made the 需求拆解 spec wrong):

1. **Ready line is not in sidecar.log.** stdout is piped to Tauri; sidecar.log is stderr. Discover `--port` / `lsof` on `127.0.0.1`. Do not trust uvicorn `:8000`.
2. **`desktop.yml` is one matrix `build` job.** New `if: runner.os == 'macOS'` step; no artifact-download job; do not fold into `Build Tauri installer`.
3. **Do not sign** means do not add/require/claim signing. Keep S9.11 secret-gated sign/notarize.
4. **`macos-latest` is Darwin.** Exit-2 skip is for Linux/WSL2 开发/测试, not the macOS runner.
5. **Loopback GET must bypass proxy**, same as `tests/desktop/smoke.sh`.

Non-holes: Windows job still uploads NSIS with no GUI; no packaged-desktop ≥500 tick; scratch dir is not `/tmp`; this leftover does not import photos; living docs tick only on 上线.

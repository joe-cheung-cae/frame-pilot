# Leftover: packaged macOS quit+job matrix (2026-09-08)

> Language: **English** | [中文](2026-09-08-desktop-quit-job-matrix.zh.md)

**GitHub:** [joe-cheung-cae/frame-pilot#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181). Created 2026-09-08 after `list_issues` found **no open issues** (latest leftover closed [#179](https://github.com/joe-cheung-cae/frame-pilot/issues/179) via [#180](https://github.com/joe-cheung-cae/frame-pilot/pull/180)). Do not reopen [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144), [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172), or [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177). Do not fold this work into `macos-dmg-gui-smoke.sh` or `desktop-500-gui.sh`.

**Branch:** `cursor/desktop-quit-job-matrix-186e` from `origin/main` @ `d75a8dc` (`fix(desktop): harden Path B QA ACL, milestone allowlist, and canonicalize`). Isolation worktree is false. Do not checkout `main` for commits. Do not merge to `main`. Do not squash. Do not force-push.

**Related:** `develop_plan.md` §1.1; `docs/desktop_development_plan.md` §2.2 and §5.6; `docs/desktop_testing.md`; `.github/workflows/desktop.yml`. Implementation merged as [#182](https://github.com/joe-cheung-cae/frame-pilot/pull/182). 上线 docs PR: [#183](https://github.com/joe-cheung-cae/frame-pilot/pull/183).

---

## 1. Why leftover, not Phase 10

Phase 9 remaining-stretch is closed on `main` ([#174](https://github.com/joe-cheung-cae/frame-pilot/pull/174)). Cache knobs ([#175](https://github.com/joe-cheung-cae/frame-pilot/issues/175)), dual-platform install+run ([#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177)), and packaged-desktop ≥500 GUI ([#179](https://github.com/joe-cheung-cae/frame-pilot/issues/179)) shipped.

`develop_plan.md` §1.1 listed **full packaged macOS quit+job matrix** as unscheduled when this leftover started. [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177) claimed **install+run only**. [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172) S9.12 stays **skip, not pass**. [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144) stays Windows-only history (Quit clean / Quit+import; processing/export quit dialogs shipped later). This leftover later shipped on `main` via [#182](https://github.com/joe-cheung-cae/frame-pilot/pull/182) plus this 上线 docs stamp.

Do **not** invent Phase 10 / S10 / 2.3. Product stays `2.1.0-desktop`. Do not bump `APP_VERSION`.

---

## 2. Locked decisions

1. **Local-first.** No cloud upload, login, payment, telemetry, or bundled neural models.
2. **Never modify or delete original photos.** Copy-mode `POST .../imports/from-paths` only. Do not commit camera photos, certs, or model weights. Do not attach photos, project DBs, or export trees to GitHub artifacts.
3. **DoD is four Darwin rows** on the same `desktop.yml` `macos-latest` job: Quit clean, Quit+import, Quit+processing, Quit+export. Tick only when **all four** are `result=pass`.
4. **Path B starts the job.** Native folder dialog stays stubbed. Production quit path is File → Quit / `osascript` quit / `ExitRequested` → `handle_close_requested` → `#framepilot-quit-dialog`. Path B clicks `[data-choice=cancel_and_quit]`.
5. **Fail-closed `qa_request_close`.** QA off → error. ACL stays on `capabilities/qa.json` **main only**. Do not put QA commands on `default.json`. No extra `fs:` / `shell:`. Use only if Apple Event quit is flaky.
6. **Same-job unsigned DMG.** Do not download installer artifacts into a second job. Do not fold into `macos-dmg-gui-smoke.sh` or `desktop-500-gui.sh`.
7. **`verify.yml` stays rust-free.** Do not launch packaged GUI from `verify.yml`.
8. **Skip ≠ pass.** Linux/WSL2: print `skip is not pass`, **exit 2**, never `result=pass`. GHA `macos-latest`: **fail (exit 1)**, never skip.
9. **No `APP_VERSION` bump.** Window title stays `FramePilot`. Version stays `2.1.0-desktop`.
10. **Do not sign** in this leftover. Do not claim Gatekeeper-clean or store listing.
11. **Scratch prefix:** `$HOME/.cache/framepilot-desktop-quit-job` (`chmod 700`). Never `/tmp` for QA photos. Siblings: `photos/`, `project/`, `data/`, `evidence/` (optional `app/`). Fail-closed prefix gate must accept this prefix **and** keep the #179 `framepilot-desktop-500-gui` prefix.
12. **500** generated 3000×2000 q88 JPEGs so import/processing/export stay active long enough for cancel. GHA [34227247641](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/34227247641) showed 30-photo processing already `complete` when cancel posted (HTTP 200, not 202). Do not add production sleeps.
13. **Stay / Quit anyway** stay Rust unit-tested. Packaged evidence must still record all three dialog buttons before the Cancel click.
14. **Windows is not this leftover’s tick.** Do not reopen #144.
15. **English** for code, comments, tests, commits. **Bilingual** living docs.
16. **One draft PR.** Title: `ci: packaged macOS quit+job matrix (leftover)`. Body `Refs` [#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181); `Refs` #177 / #144 / #172 as historical. No `Fixes` until 上线 when all four Darwin rows are green. Never a second PR.
17. **Out:** Phase 10, Path C, packaged Stay/Quit-anyway click-through, Windows DoD, sidecar-crash / port-in-use / install-uninstall rows, `APP_VERSION` bump, folding quit into #177/#179 scripts.

---

## 3. Status board

Leftover packaged macOS quit+job matrix

- [x] 需求拆解 — bilingual leftover plan + GitHub issue [#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181)
- [x] 开发 — Path B quit modes + harness + `desktop.yml` macOS step
- [x] 测试 — Linux skip-not-pass + `npm run verify`
- [x] 上线 — [desktop.yml run 34230112750](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/34230112750) (`8658e14`, `2026-09-08T13:26:18Z`) four Darwin rows `result=pass`; implementation merged as [#182](https://github.com/joe-cheung-cae/frame-pilot/pull/182) (`Refs` only); 上线 docs PR [#183](https://github.com/joe-cheung-cae/frame-pilot/pull/183) uses `Fixes` [#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181)
- [x] DoD-ticked — leftover-plan 上线 + `docs/desktop_development_plan.md` §5.6 quit+job `[x]` with the run URL; do **not** re-tick §2.2

Failed Darwin oracles stay history: [34209655915](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/34209655915) (`osascript` quit before `quit_dialog`); [34227247641](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/34227247641) (30-photo processing already `complete`). Skip ≠ pass. Do **not** invent a later Darwin pass.

---

## 4. Rows

| Row | Path B mode | Pass |
| --- | ----------- | ---- |
| Quit clean | `quit-clean` | no active job; sidecar exits; no leftover `framepilot-api` LISTEN (`TIME_WAIT` ok); no quit dialog required |
| Quit + import | `quit-import` | title `Import is still running`; buttons stay / cancel_and_quit / quit_anyway; click cancel; job `cancelled`; originals unchanged |
| Quit + processing | `quit-processing` | title `Grouping and ranking is still running`; click cancel; partial groups cleared; originals unchanged |
| Quit + export | `quit-export` | title `Export is still running`; click cancel; partial export artifacts under the project export root removed; originals unchanged |

Each CancelAndQuit row writes JSONL `*_running` as soon as the job is `queued` or `running`, then waits for `#framepilot-quit-dialog`. Do **not** wait for `complete` before quit. Quit clean writes `idle` only; the harness quits.

Four packaged launches (CancelAndQuit exits the app).

---

## 5. Tick rules

| When | Tick | Do not tick |
| ---- | ---- | ----------- |
| 需求拆解 | leftover board 需求拆解 | 开发, DoD-ticked, §5.6 quit+job |
| 开发 | leftover board 开发 | §5.6 quit+job; §2.2 install+run / ≥500 |
| 上线 green Darwin four-row pass | leftover board 上线 + DoD-ticked; `docs/desktop_development_plan.md` §5.6 quit+job `[x]` with run URL; §1.1 remaining unscheduled drops this leftover | §2.2 re-tick; Gatekeeper-clean; store listing; Phase 10 |

Green evidence commit subject (上线 only): `docs: record packaged macOS quit+job matrix leftover pass`.

# Leftover: packaged Windows quit+job matrix (2026-09-08)

> Language: **English** | [中文](2026-09-08-desktop-quit-job-windows.zh.md)

**GitHub:** [joe-cheung-cae/frame-pilot#184](https://github.com/joe-cheung-cae/frame-pilot/issues/184). Created 2026-09-08 after leftover packaged macOS quit+job matrix shipped ([#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181) / [#182](https://github.com/joe-cheung-cae/frame-pilot/pull/182) / [#183](https://github.com/joe-cheung-cae/frame-pilot/pull/183), [desktop.yml run 34230112750](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/34230112750)). Do not reopen [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144), [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172), [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177), or [#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181). Do not fold this work into `macos-dmg-gui-smoke.sh` or `desktop-500-gui.sh`. Reuse/extend `packaging/scripts/desktop-quit-job-gui.sh`.

**Branch:** `cursor/desktop-quit-job-windows-7bb0` from `origin/main` @ `cf79b1829c9f22e52431bec971c1040b8f0ffae4`. Isolation worktree is false. Do not checkout `main` for commits. Do not merge to `main`. Do not squash. Do not force-push.

**Related:** `develop_plan.md` §1.1; `docs/desktop_development_plan.md` §2.2 and §5.6; `docs/desktop_testing.md`; `.github/workflows/desktop.yml`. macOS leftover plan: [2026-09-08-desktop-quit-job-matrix.md](2026-09-08-desktop-quit-job-matrix.md). Draft PR [#185](https://github.com/joe-cheung-cae/frame-pilot/pull/185).

---

## 1. Why leftover, not Phase 10

Phase 9 remaining-stretch is closed on `main` ([#174](https://github.com/joe-cheung-cae/frame-pilot/pull/174)). Cache knobs ([#175](https://github.com/joe-cheung-cae/frame-pilot/issues/175)), dual-platform install+run ([#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177)), packaged-desktop ≥500 GUI ([#179](https://github.com/joe-cheung-cae/frame-pilot/issues/179)), and packaged macOS quit+job matrix ([#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181)) shipped.

`develop_plan.md` §1.1 listed **packaged Windows quit+job matrix** as the next lowest desktop gate after Darwin #181. [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144) stays Windows-only history (Quit clean / Quit+import; processing/export quit dialogs shipped later). Do **not** reopen it.

Do **not** invent Phase 10 / S10 / 2.3. Product stays `2.1.0-desktop`. Do not bump `APP_VERSION`.

---

## 2. Locked decisions

1. **Local-first.** No cloud upload, login, payment, telemetry, or bundled neural models.
2. **Never modify or delete original photos.** Copy-mode `POST .../imports/from-paths` only. Do not commit camera photos, certs, or model weights. Do not attach photos, project DBs, or export trees to GitHub artifacts.
3. **DoD is four Windows rows** on the same `desktop.yml` `windows-latest` job: Quit clean, Quit+import, Quit+processing, Quit+export. Tick only when **all four** are `result=pass`.
4. **Path B starts the job.** Native folder dialog stays stubbed. Production quit path is File → Quit / window close / `CloseRequested` / `ExitRequested` → `handle_close_requested` → `#framepilot-quit-dialog`. Path B clicks `[data-choice=cancel_and_quit]`. Same approach as leftover [#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181) / [#182](https://github.com/joe-cheung-cae/frame-pilot/pull/182).
5. **Fail-closed `qa_request_close`.** QA off → error. ACL stays on `capabilities/qa.json` **main only**. Do not put QA commands on `default.json`. No extra `fs:` / `shell:`. Job rows must not `CloseMainWindow` / `taskkill` before `quit_dialog`.
6. **Same-job unsigned NSIS.** Do not download installer artifacts into a second job. Do not fold into `macos-dmg-gui-smoke.sh` or `desktop-500-gui.sh`. Reuse/extend `desktop-quit-job-gui.sh`.
7. **`verify.yml` stays rust-free.** Do not launch packaged GUI from `verify.yml`.
8. **Skip ≠ pass.** Linux/WSL2: print `skip is not pass`, **exit 2**, never `result=pass`. GHA `windows-latest`: **fail (exit 1)**, never skip.
9. **No `APP_VERSION` bump.** Window title stays `FramePilot`. Version stays `2.1.0-desktop`.
10. **Do not sign** in this leftover. Do not claim SmartScreen-clean or store listing.
11. **Scratch prefix:** `%LOCALAPPDATA%\framepilot-desktop-quit-job` (`chmod 700` / equivalent). Never `/tmp` for QA photos. Siblings: `photos/`, `project/`, `data/`, `evidence/` (optional `app/`). Fail-closed prefix gate must accept this prefix **and** keep the #179 `framepilot-desktop-500-gui` prefix **and** the POSIX `#181` `$HOME/.cache/framepilot-desktop-quit-job` prefix.
12. **500** generated 3000×2000 q88 JPEGs so import/processing/export stay active long enough for cancel. Do not add production sleeps.
13. **Stay / Quit anyway** stay Rust unit-tested. Packaged evidence must still record all three dialog buttons before the Cancel click.
14. **Do not reopen #144 / #172 / #177 / #181.** Darwin #181 pass stays history. Do not re-tick §2.2 install+run / ≥500.
15. **English** for code, comments, tests, commits. **Bilingual** living docs.
16. **One draft PR.** Title: `ci: packaged Windows quit+job matrix (leftover)`. Body `Refs` [#184](https://github.com/joe-cheung-cae/frame-pilot/issues/184); `Refs` #181 / #177 / #144 / #172 as historical. No `Fixes` until 上线 when all four Windows rows are green. Implementer does not merge.
17. **Out:** Phase 10, Path C, packaged Stay/Quit-anyway click-through, reopening #144, sidecar-crash / port-in-use / install-uninstall rows, `APP_VERSION` bump, signing, XMP, merging #41, reopening D3.06, folding quit into #177/#179 scripts.

---

## 3. Status board

Leftover packaged Windows quit+job matrix

- [x] 需求拆解 — bilingual leftover plan + GitHub issue [#184](https://github.com/joe-cheung-cae/frame-pilot/issues/184)
- [x] 开发 — Path B Windows NSIS launch + production `CloseMainWindow` quit-clean + `desktop.yml` windows step
- [x] 测试 — Linux skip-not-pass + packaged-path Windows checks + `npm run verify`
- [ ] 上线 — same-job `desktop.yml` `windows-latest` four rows `result=pass`; evidence downloadable
- [ ] DoD-ticked — leftover-plan 上线 + `docs/desktop_development_plan.md` §5.6 Windows quit+job `[x]` with the run URL; do **not** re-tick §2.2 / ≥500 / Darwin #181

Skip ≠ pass. Do **not** invent a Windows pass.

---

## 4. Rows

| Row | Path B mode | Pass |
| --- | ----------- | ---- |
| Quit clean | `quit-clean` | no active job; sidecar exits; no leftover `framepilot-api` LISTEN (`TIME_WAIT` ok); no quit dialog required; production window close (`CloseMainWindow` / `CloseRequested`) |
| Quit + import | `quit-import` | title `Import is still running`; buttons stay / cancel_and_quit / quit_anyway; click cancel; job `cancelled`; originals unchanged |
| Quit + processing | `quit-processing` | title `Grouping and ranking is still running`; click cancel; partial groups cleared; originals unchanged |
| Quit + export | `quit-export` | title `Export is still running`; click cancel; partial export artifacts under the project export root removed; originals unchanged |

Each CancelAndQuit row writes JSONL `*_running` as soon as the job is `queued` or `running`, then waits for `#framepilot-quit-dialog`. Do **not** wait for `complete` before quit. Quit clean writes `idle` only; the harness quits via production close.

Four packaged launches (CancelAndQuit exits the app). Install NSIS once; launch four times.

---

## 5. Tick rules

| When | Tick | Do not tick |
| ---- | ---- | ----------- |
| 需求拆解 | leftover board 需求拆解 | 开发, DoD-ticked, §5.6 Windows quit+job |
| 开发 | leftover board 开发 | §5.6 Windows quit+job; §2.2 install+run / ≥500; Darwin #181 |
| 上线 green Windows four-row pass | leftover board 上线 + DoD-ticked; `docs/desktop_development_plan.md` §5.6 Windows quit+job `[x]` with run URL; §1.1 remaining unscheduled drops this leftover | §2.2 re-tick; Darwin #181 re-stamp; SmartScreen-clean; store listing; Phase 10 |

Green evidence commit subject (上线 only): `docs: record packaged Windows quit+job matrix leftover pass`.

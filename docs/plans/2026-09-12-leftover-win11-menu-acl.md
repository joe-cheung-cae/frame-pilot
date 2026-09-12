# Leftover: Win11 File menu take_menu_command is denied by ACL (2026-09-12)

> Language: **English** | [中文](2026-09-12-leftover-win11-menu-acl.zh.md)

**GitHub:** [joe-cheung-cae/frame-pilot#208](https://github.com/joe-cheung-cae/frame-pilot/issues/208). After leftover [#206](https://github.com/joe-cheung-cae/frame-pilot/issues/206) / [#207](https://github.com/joe-cheung-cae/frame-pilot/pull/207) (`5d15588`) Joe installed the #206 payload on Win11 (`zhangc`). File → Import / Export still does not navigate. Sidecar stays on Recent Projects. This is not leftover [#194](https://github.com/joe-cheung-cae/frame-pilot/issues/194). Do not reopen #194. Do not touch [#41](https://github.com/joe-cheung-cae/frame-pilot/issues/41) / D3.06 tray. Do not invent Phase 10.

**Branch:** `feature/leftover-win11-menu-acl` from `origin/main`. Do not stack on `feature/leftover-raw-develop` / [#203](https://github.com/joe-cheung-cae/frame-pilot/pull/203). Do not merge to `main`. Implementer does not merge.

**Related:** `develop_plan.md` §1.1; `apps/desktop/src-tauri/capabilities/default.json`; `apps/desktop/src-tauri/permissions/menu.toml`; `apps/desktop/src-tauri/src/menu.rs`; `apps/desktop/src/lib/nativeMenu.ts`.

---

## 1. Why leftover, not Phase 10

#206 queued File menu commands and polled `invoke("take_menu_command")`. That leftover assumed packaged `invoke` already worked because leftover GUI Path B can call `qa_bootstrap`. `qa_*` is allowed only by `allow-qa-write-evidence` on the QA capability. The default capability has no app-command permission. Tauri 2 denies `take_menu_command` there. `app.emit` still uses `webview.eval` and stays silent on this WebView.

Host evidence after the #206 overlay (`2026-09-12T08:56:28+08:00`; later PID 46452, sidecar `127.0.0.1:5664` health 200): File → Import id=`1002` `POST=True`. Sidecar stayed on `GET /api/projects` plus three `qa-144-*` `jobs?limit=50`. Joe confirmed after that install: still not fixed.

Product rule stays: File → Import **navigates** to Import Images (or Create Project with *Create a project before opening Import.*). The picker is still **Choose a folder** / **Choose image files**.

Do **not** invent Phase 10 / S10 / 2.3. Product string stays `2.1.0-desktop`. Do not bump `APP_VERSION`.

---

## 2. Locked decisions

1. **Local-first.** No cloud upload, login, payment, telemetry, or bundled neural models.
2. **File → Import still navigates only.** Do not open a native picker from the menu.
3. **Allow the existing IPC command.** Add `permissions/menu.toml` `allow-take-menu-command` for `take_menu_command` and put it on `capabilities/default.json`. Same pattern as `allow-qa-write-evidence`. No `fs:` / `shell:`. Keep emit/listen as a secondary path. No `window.eval` / DOM `dispatchEvent` from Rust.
4. **Do not move QA ACL onto default.** `qa_*` stays on `capabilities/qa.json`.
5. **No `APP_VERSION` bump.** No NSIS/DMG in this leftover. No `desktop.yml` dispatch. No tray / D3.06 / #41.
6. **One draft PR.** Body must include `Closes #208`. Implementer does not merge.
7. **Out:** native picker on File → Import, signing, treating a blank Import page as a #195 regression, reopening #194 / #206.

---

## 3. Status board

Leftover Win11 File menu take_menu_command is denied by ACL

- [x] 需求拆解 — bilingual leftover plan + GitHub issue [#208](https://github.com/joe-cheung-cae/frame-pilot/issues/208)
- [x] 开发 — `allow-take-menu-command` on default capability
- [x] 测试 — desktop `nativeMenu` / `desktopQaRunner` 54; `typecheck:desktop`; web unit 272 + vitest 73. Do not invent a cargo pass on this WSL host.
- [ ] 上线 — merge + follow-on unsigned NSIS for packaged Win11 (implementer does not merge)
- [ ] DoD-ticked — leftover-plan 上线 after a #208+ NSIS exists and File → Import leaves the three-list poll; do **not** invent a dated Win11 GUI pass / Phase 10 / re-tick §2.2

---

## 4. Tick rules

| When | Tick | Do not tick |
| ---- | ---- | ----------- |
| 需求拆解 | leftover board 需求拆解 | 上线; §2.2; leftover shipped |
| 开发 + named tests green | leftover board 开发 + 测试 | 上线; Gatekeeper-clean; store listing; Win11 GUI pass |
| #208+ NSIS is installed on Joe’s Win11 and File → Import leaves the three-list `jobs?limit=50` poll | leftover board 上线 + DoD-ticked; §1.1 leftover shipped | §2.2 re-tick; public signing checklist; Phase 10; invent Win11 pass |

---

## 5. Win11 acceptance (after a new NSIS; this PR does not invent a pass)

1. Cold start to Recent Projects.
2. File → Import: Create Project with *Create a project before opening Import.*, or (with lastOpened) that project’s Import Images. Sidecar must leave the three-list `jobs?limit=50` poll.
3. File → Export / File → New also navigate.
4. On Import Images, **Choose a folder** remains the picker.
5. File → Open data folder / Quit unchanged.

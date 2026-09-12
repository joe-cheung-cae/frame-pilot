# Leftover: Win11 File menu emit still does not navigate (2026-09-11)

> Language: **English** | [中文](2026-09-11-leftover-win11-menu-ipc.zh.md)

**GitHub:** [joe-cheung-cae/frame-pilot#206](https://github.com/joe-cheung-cae/frame-pilot/issues/206). After leftover [#204](https://github.com/joe-cheung-cae/frame-pilot/issues/204) / [#205](https://github.com/joe-cheung-cae/frame-pilot/pull/205) (`cb06ce5`) Joe installed the new NSIS on Win11 (`zhangc`). File → Import / Export still does not navigate. Sidecar stays on Recent Projects. This is not leftover [#194](https://github.com/joe-cheung-cae/frame-pilot/issues/194). Do not reopen #194. Do not touch [#41](https://github.com/joe-cheung-cae/frame-pilot/issues/41) / D3.06 tray. Do not invent Phase 10.

**Branch:** `feature/leftover-win11-menu-ipc` from `origin/main`. Do not stack on `feature/leftover-raw-develop` / [#203](https://github.com/joe-cheung-cae/frame-pilot/pull/203). Do not merge to `main`. Implementer does not merge.

**Related:** `develop_plan.md` §1.1; `apps/desktop/src-tauri/src/menu.rs`; `apps/desktop/src/App.tsx`; `apps/desktop/src/lib/nativeMenu.ts`.

---

## 1. Why leftover, not Phase 10

#204 replaced silent `window.eval(CustomEvent)` with `app.emit("framepilot-menu")` + `listen`. Tauri 2.11 still delivers that emit to the webview with `webview.eval` (`emit_js` / `listen_js`). Joe’s packaged Win11 WebView can drop that path. The same NSIS already uses `invoke` successfully (`qa_bootstrap`, sidecar fetch).

Host evidence after the #204 NSIS (`2026-09-11T19:44:01+08:00`, PID 51388, sidecar `127.0.0.1:5715` health 200): `GET /api/projects` plus three `qa-144-*` `jobs?limit=50`. No Import/Export page fetches. No POST.

Product rule stays: File → Import **navigates** to Import Images (or Create Project with *Create a project before opening Import.*). The picker is still **Choose a folder** / **Choose image files**.

Do **not** invent Phase 10 / S10 / 2.3. Product string stays `2.1.0-desktop`. Do not bump `APP_VERSION`.

---

## 2. Locked decisions

1. **Local-first.** No cloud upload, login, payment, telemetry, or bundled neural models.
2. **File → Import still navigates only.** Do not open a native picker from the menu.
3. **Packaged path is IPC.** `handle_menu_event` queues the command. `NativeMenuListener` `invoke("take_menu_command")` then `resolveMenuCommand` + `navigator.push`. Keep emit/listen as a secondary path. No `window.eval` / DOM `dispatchEvent` from Rust.
4. **Refs, not effect churn.** Poll and listen subscribe once. Read `pathname` / `navigator` from refs.
5. **No `APP_VERSION` bump.** No NSIS/DMG in this leftover. No `desktop.yml` dispatch. No tray / D3.06 / #41.
6. **One draft PR.** Body must include `Closes #206`. Implementer does not merge.
7. **Out:** native picker on File → Import, signing, treating a blank Import page as a #195 regression, reopening #194.

---

## 3. Status board

Leftover Win11 File menu emit still does not navigate

- [x] 需求拆解 — bilingual leftover plan + GitHub issue [#206](https://github.com/joe-cheung-cae/frame-pilot/issues/206)
- [x] 开发 — `PendingMenuCommand` + `take_menu_command`; desktop poll
- [x] 测试 — desktop `nativeMenu` / `desktopQaRunner` unit tests; `typecheck:desktop`; web unit 272 + vitest 73. Do not invent a cargo pass on this WSL host.
- [ ] 上线 — #207 merged (`5d15588`); Joe’s #206 overlay (`2026-09-12T08:56:28+08:00`) still stayed on the three-list poll. Follow-on leftover [#208](https://github.com/joe-cheung-cae/frame-pilot/issues/208). Do not tick.
- [ ] DoD-ticked — do **not** invent a dated Win11 GUI pass / Phase 10 / re-tick §2.2

---

## 4. Tick rules

| When | Tick | Do not tick |
| ---- | ---- | ----------- |
| 需求拆解 | leftover board 需求拆解 | 上线; §2.2; leftover shipped |
| 开发 + named tests green | leftover board 开发 + 测试 | 上线; Gatekeeper-clean; store listing; Win11 GUI pass |
| #206+ NSIS is installed on Joe’s Win11 and File → Import leaves the three-list `jobs?limit=50` poll | leftover board 上线 + DoD-ticked; §1.1 leftover shipped | §2.2 re-tick; public signing checklist; Phase 10; invent Win11 pass |

---

## 5. Win11 acceptance (after a new NSIS; this PR does not invent a pass)

1. Cold start to Recent Projects.
2. File → Import: Create Project with *Create a project before opening Import.*, or (with lastOpened) that project’s Import Images. Sidecar must leave the three-list `jobs?limit=50` poll.
3. File → Export / File → New also navigate.
4. On Import Images, **Choose a folder** remains the picker.
5. File → Open data folder / Quit unchanged.

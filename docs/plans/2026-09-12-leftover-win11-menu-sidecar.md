# Leftover: Win11 File menu still does not navigate after ACL (2026-09-12)

> Language: **English** | [中文](2026-09-12-leftover-win11-menu-sidecar.zh.md)

**GitHub:** [joe-cheung-cae/frame-pilot#210](https://github.com/joe-cheung-cae/frame-pilot/issues/210). After leftover [#208](https://github.com/joe-cheung-cae/frame-pilot/issues/208) / [#209](https://github.com/joe-cheung-cae/frame-pilot/pull/209) (`0418bd6`) Joe installed the #208 NSIS on Win11 (`zhangc`). File → Import / Export still does not navigate. Sidecar stays on Recent Projects. This is not leftover [#194](https://github.com/joe-cheung-cae/frame-pilot/issues/194). Do not reopen #194 / #206 / #208. Do not touch [#41](https://github.com/joe-cheung-cae/frame-pilot/issues/41) / D3.06 tray. Do not invent Phase 10.

**Branch:** `feature/leftover-win11-menu-sidecar` from `origin/main`. Do not stack on `feature/leftover-raw-develop` / [#203](https://github.com/joe-cheung-cae/frame-pilot/pull/203). Do not merge to `main`. Implementer does not merge.

**Related:** `develop_plan.md` §1.1; `apps/api/app/services/desktop_menu.py`; `apps/api/app/api/routes.py`; `apps/desktop/src-tauri/src/menu.rs`; `apps/desktop/src-tauri/src/sidecar.rs`; `apps/desktop/src/lib/nativeMenu.ts`; `apps/desktop/src/App.tsx`.

---

## 1. Why leftover, not Phase 10

#204 `window.eval`, #206 `app.emit` / `listen` (still `webview.eval`), and #208 `invoke("take_menu_command")` plus default ACL did not navigate on this packaged Win11 WebView. The #208 NSIS exe contains `allow-take-menu-command`. File → Import id=`1002` `POST=True`. Sidecar stayed on `GET /api/projects` plus three `jobs?limit=50`.

Path B `qa_bootstrap` is not proof that production menu IPC works. The same WebView already fetches the sidecar over loopback HTTP.

Product rule stays: File → Import **navigates** to Import Images (or Create Project with *Create a project before opening Import.*). The picker is still **Choose a folder** / **Choose image files**.

Do **not** invent Phase 10 / S10 / 2.3. Product string stays `2.1.0-desktop`. Do not bump `APP_VERSION`.

---

## 2. Locked decisions

1. **Local-first.** No cloud upload, login, payment, telemetry, or bundled neural models.
2. **File → Import still navigates only.** Do not open a native picker from the menu.
3. **Packaged path is sidecar HTTP.** `handle_menu_event` POSTs `{command}` to loopback `POST /api/desktop/menu-command`. `NativeMenuListener` polls `GET /api/desktop/menu-command` (take, `Cache-Control: no-store`) then `resolveMenuCommand` + `navigator.push`. Keep emit/listen and `take_menu_command` as secondary. No `window.eval` / DOM `dispatchEvent` from Rust. No `fs:` / `shell:`.
4. **Desktop-only endpoint.** 404 unless `FRAMEPILOT_DESKTOP=1`. Only navigable commands: `new`, `shortcuts`, `import`, `export`, `process`, `cull`. Loopback Host already required. Do not move QA ACL onto default.
5. **No `APP_VERSION` bump.** No NSIS/DMG in this leftover. No `desktop.yml` dispatch. No tray / D3.06 / #41.
6. **One draft PR.** Body must include `Closes #210`. Implementer does not merge.
7. **Out:** native picker on File → Import, signing, treating a blank Import page as a #195 regression, reopening #194 / #206 / #208.

---

## 3. Status board

Leftover Win11 File menu still does not navigate after ACL

- [x] 需求拆解 — bilingual leftover plan + GitHub issue [#210](https://github.com/joe-cheung-cae/frame-pilot/issues/210)
- [x] 开发 — sidecar menu-command queue; Rust POST; desktop poll GET
- [x] 测试 — API `test_desktop_menu_command` 5; desktop `nativeMenu` sidecar take; `typecheck:desktop`; web `menuRoutes` 8. Do not invent a cargo pass on this WSL host.
- [ ] 上线 — merge + follow-on unsigned NSIS for packaged Win11 (implementer does not merge)
- [ ] DoD-ticked — leftover-plan 上线 after a #210+ NSIS exists and File → Import leaves the three-list poll; do **not** invent a dated Win11 GUI pass / Phase 10 / re-tick §2.2

---

## 4. Tick rules

| When | Tick | Do not tick |
| ---- | ---- | ----------- |
| 需求拆解 | leftover board 需求拆解 | 上线; §2.2; leftover shipped |
| 开发 + named tests green | leftover board 开发 + 测试 | 上线; Gatekeeper-clean; store listing; Win11 GUI pass |
| #210+ NSIS is installed on Joe’s Win11 and File → Import leaves the three-list `jobs?limit=50` poll | leftover board 上线 + DoD-ticked; §1.1 leftover shipped | §2.2 re-tick; public signing checklist; Phase 10; invent Win11 pass |

---

## 5. Win11 acceptance (after a new NSIS; this PR does not invent a pass)

1. Cold start to Recent Projects.
2. File → Import: Create Project with *Create a project before opening Import.*, or (with lastOpened) that project’s Import Images. Sidecar must leave the three-list `jobs?limit=50` poll.
3. File → Export / File → New also navigate.
4. On Import Images, **Choose a folder** remains the picker.
5. File → Open data folder / Quit unchanged.

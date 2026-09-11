# Leftover: Win11 File menu invoke does not navigate (2026-09-11)

> Language: **English** | [中文](2026-09-11-leftover-win11-menu-bridge.zh.md)

**GitHub:** [joe-cheung-cae/frame-pilot#204](https://github.com/joe-cheung-cae/frame-pilot/issues/204). Joe’s Win11 packaged `v2.1.3-desktop` (product string still `2.1.0-desktop`) File → New / Import / Export is invoked by Windows, but the WebView stays on Recent Projects. This is not a missing file-picker UX and not leftover [#194](https://github.com/joe-cheung-cae/frame-pilot/issues/194) / [#195](https://github.com/joe-cheung-cae/frame-pilot/pull/195). #194 assumed a `framepilot-menu` CustomEvent reached React. Do not reopen #194. Do not touch [#41](https://github.com/joe-cheung-cae/frame-pilot/issues/41) / D3.06 tray. Do not invent Phase 10.

**Branch:** `feature/leftover-win11-menu-bridge` from `origin/main`. Do not stack on `feature/leftover-raw-develop` / [#203](https://github.com/joe-cheung-cae/frame-pilot/pull/203). Do not merge to `main`. Implementer does not merge.

**Related:** `develop_plan.md` §1.1; `apps/desktop/src-tauri/src/menu.rs`; `apps/desktop/src/App.tsx`; `apps/web/src/components/MenuCommandListener.tsx`; `apps/web/src/lib/menuRoutes.ts`.

---

## 1. Why leftover, not Phase 10

Phase 9 remaining-stretch is closed. Native File menu clicks already reach `handle_menu_event`. `emit_menu_command` then `window.eval`s a `framepilot-menu` CustomEvent. On the packaged Win11 WebView that eval is silent: missing `main` or eval failure is discarded, and the MemoryRouter never `push`es.

Product rule stays: File → Import **navigates** to Import Images (or Create Project with *Create a project before opening Import.*). The picker is still **Choose a folder** / **Choose image files** on that page.

Do **not** invent Phase 10 / S10 / 2.3. Product string stays `2.1.0-desktop`. Do not bump `APP_VERSION`. Packaged Win11 acceptance is a follow-on unsigned Release leftover — not this issue.

---

## 2. Locked decisions

1. **Local-first.** No cloud upload, login, payment, telemetry, or bundled neural models.
2. **File → Import still navigates only.** Do not open a native picker from the menu.
3. **Rust main path is Tauri emit.** `app.emit(MENU_EVENT, command)` like detached preview. Event name stays `framepilot-menu`. Missing `main` window or emit failure must `eprintln!`. No `let _ = window.eval(...)`.
4. **Packaged shell listens inside MemoryRouter.** `NativeMenuListener` uses `@tauri-apps/api/event` `listen`, then `resolveMenuCommand` + `navigator.push` + `loadLastOpenedProjectId`. `pathname` is an effect dependency; re-subscribe when it changes. Do not import `@tauri-apps/api` into `apps/web` `MenuCommandListener`.
5. **Keep CustomEvent tests.** Web `MenuCommandListener` and `MenuCommandListener.test.tsx` stay for unit tests and DOM dispatch. The packaged path must not depend on eval.
6. **No `APP_VERSION` bump.** No NSIS/DMG. No `desktop.yml` dispatch. No tray / D3.06 / #41.
7. **One draft PR.** Body must include `Closes #204`. Implementer does not merge.
8. **Out:** native picker on File → Import, signing, treating a blank Import page as a #195 regression, sidecar-failure `eval` in `lib.rs`.

---

## 3. Status board

Leftover Win11 File menu invoke does not navigate

- [x] 需求拆解 — bilingual leftover plan + GitHub issue [#204](https://github.com/joe-cheung-cae/frame-pilot/issues/204)
- [ ] 开发 — `menu.rs` Tauri emit; desktop `NativeMenuListener` listen + `resolveMenuCommand`
- [ ] 测试 — `npm run test:web`; desktop `nativeMenu` unit tests; `typecheck:desktop` / `lint:desktop`. `cargo test --lib` blocked on this WSL host (pkg-config / GTK missing); rustc 1.98.0 is present. Do not invent a cargo pass.
- [ ] 上线 — merge + follow-on unsigned Release leftover for packaged Win11 (implementer does not merge)
- [ ] DoD-ticked — leftover-plan 上线 after a #204+ NSIS exists; do **not** invent a dated Win11 GUI pass / Phase 10 / re-tick §2.2

---

## 4. Tick rules

| When | Tick | Do not tick |
| ---- | ---- | ----------- |
| 需求拆解 | leftover board 需求拆解 | 上线; §2.2; leftover shipped |
| 开发 + named tests green | leftover board 开发 + 测试 | 上线; Gatekeeper-clean; store listing; Win11 GUI pass |
| #204+ NSIS is published (Actions or a later Release) | leftover board 上线 + DoD-ticked; §1.1 leftover shipped | §2.2 re-tick; public signing checklist; Phase 10; invent Win11 pass |

---

## 5. Win11 acceptance (after a new NSIS; this PR does not invent a pass)

1. Cold start to Recent Projects.
2. File → Import: Create Project with *Create a project before opening Import.*, or (with lastOpened) that project’s Import Images. Sidecar must leave the three-list `jobs?limit=50` poll.
3. File → Export / File → New also navigate.
4. On Import Images, **Choose a folder** remains the picker.
5. File → Open data folder / Quit unchanged.

Host evidence already recorded (`zhangc`, `2026-09-11T16:48:02+08:00`): menu child `1000` New, `1002` Import, `1003` Export; sidecar stayed on `GET /api/projects` plus `qa-144-*` `jobs?limit=50`.

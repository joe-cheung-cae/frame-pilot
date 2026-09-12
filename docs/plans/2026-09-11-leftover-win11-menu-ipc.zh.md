# 残留：Win11 File 菜单 emit 仍不跳页（2026-09-11）

> 语言：**中文** | [English](2026-09-11-leftover-win11-menu-ipc.md)

**GitHub：** [joe-cheung-cae/frame-pilot#206](https://github.com/joe-cheung-cae/frame-pilot/issues/206)。残留 [#204](https://github.com/joe-cheung-cae/frame-pilot/issues/204) / [#205](https://github.com/joe-cheung-cae/frame-pilot/pull/205)（`cb06ce5`）之后，Joe 在 Win11（`zhangc`）装了新 NSIS。File → Import / Export **仍然不跳页**。sidecar 停在 Recent Projects。这不是残留 [#194](https://github.com/joe-cheung-cae/frame-pilot/issues/194)。不要重开 #194。不要动 [#41](https://github.com/joe-cheung-cae/frame-pilot/issues/41) / D3.06 托盘。不要发明第十阶段。

**分支：** `feature/leftover-win11-menu-ipc`，从 `origin/main` 拉出。不要叠在 `feature/leftover-raw-develop` / [#203](https://github.com/joe-cheung-cae/frame-pilot/pull/203) 上。不要合入 `main`。实现者不合并。

**相关：** `develop_plan.md` §1.1；`apps/desktop/src-tauri/src/menu.rs`；`apps/desktop/src/App.tsx`；`apps/desktop/src/lib/nativeMenu.ts`。

---

## 1. 为什么是残留，不是第十阶段

#204 把静默 `window.eval(CustomEvent)` 换成 `app.emit("framepilot-menu")` + `listen`。Tauri 2.11 把这次 emit 送到 WebView 时 **仍然走 `webview.eval`**（`emit_js` / `listen_js`）。Joe 的包装 Win11 WebView 可以继续把这条路丢掉。同一个 NSIS 里 `invoke`（`qa_bootstrap`、sidecar fetch）是通的。

#204 NSIS 装完后的主机证据（`2026-09-11T19:44:01+08:00`，PID 51388，sidecar `127.0.0.1:5715` health 200）：仍是 `GET /api/projects` 加三个 `qa-144-*` 的 `jobs?limit=50`。没有进入 Import/Export 页，也没有 POST。

产品约定不变：File → Import **只跳页**到 Import Images（或带 *Create a project before opening Import.* 的新建工程）。选文件仍是页上的 **Choose a folder** / **Choose image files**。

不要发明第十阶段 / S10 / 2.3。产品字符串仍是 `2.1.0-desktop`。不要改 `APP_VERSION`。

---

## 2. 锁定决定

1. **本地优先。** 不要云上传、登录、付费、遥测或捆绑神经网络模型。
2. **File → Import 仍然只跳页。** 不要从菜单打开系统选文件框。
3. **包装路径走 IPC。** `handle_menu_event` 把 command 入队。`NativeMenuListener` `invoke("take_menu_command")`，再 `resolveMenuCommand` + `navigator.push`。emit/listen 留作辅路。Rust 侧不要 `window.eval` / DOM `dispatchEvent`。
4. **用 ref，不要把 listen/poll 绑在每次 render。** `pathname` / `navigator` 从 ref 读。
5. **不改 `APP_VERSION`。** 本残留不打 NSIS/DMG。不 dispatch `desktop.yml`。不要托盘 / D3.06 / #41。
6. **一个 draft PR。** 正文必须有 `Closes #206`。实现者不合并。
7. **不做：** File → Import 弹系统选文件框、签名、把空白 Import 页当成 #195 回退、重开 #194。

---

## 3. 状态板

残留 Win11 File 菜单 emit 仍不跳页

- [x] 需求拆解 — 双语残留计划 + GitHub issue [#206](https://github.com/joe-cheung-cae/frame-pilot/issues/206)
- [x] 开发 — `PendingMenuCommand` + `take_menu_command`；桌面 poll
- [x] 测试 — desktop `nativeMenu` / `desktopQaRunner` 单元测试；`typecheck:desktop`；web unit 272 + vitest 73。不要在这台缺 GTK 的 WSL 上编造 cargo 通过。
- [ ] 上线 — #207 已合入（`5d15588`）；Joe 的 #206 overlay（`2026-09-12T08:56:28+08:00`）仍停在三列表轮询。后续残留 [#208](https://github.com/joe-cheung-cae/frame-pilot/issues/208)。不要勾。
- [ ] DoD-ticked — **不要**编造带日期的 Win11 GUI 通过 / 第十阶段 / 重勾 §2.2

---

## 4. 勾选规则

| 何时 | 勾 | 不要勾 |
| ---- | ---- | ----------- |
| 需求拆解 | 残留板 需求拆解 | 上线；§2.2；leftover shipped |
| 开发 + 点名测试绿 | 残留板 开发 + 测试 | 上线；Gatekeeper-clean；商店上架；Win11 GUI 通过 |
| Joe 的 Win11 装上 #206+ NSIS，且 File → Import 离开三列表 `jobs?limit=50` 轮询 | 残留板 上线 + DoD-ticked；§1.1 leftover shipped | 重勾 §2.2；公开签名清单；第十阶段；编造 Win11 通过 |

---

## 5. Win11 验收（要等新 NSIS；本 PR 不编造通过）

1. 冷启动到 Recent Projects。
2. File → Import：带 *Create a project before opening Import.* 的新建工程，或（有 lastOpened）该工程的 Import Images。sidecar 必须离开三列表 `jobs?limit=50` 轮询。
3. File → Export / File → New 也要跳页。
4. Import Images 上，选文件仍是 **Choose a folder**。
5. File → Open data folder / Quit 不变。

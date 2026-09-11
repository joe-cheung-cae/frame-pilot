# 残留：Win11 File 菜单 invoke 不跳页（2026-09-11）

> 语言：[English](2026-09-11-leftover-win11-menu-bridge.md) | **中文**

**GitHub：** [joe-cheung-cae/frame-pilot#204](https://github.com/joe-cheung-cae/frame-pilot/issues/204)。Joe 在 Win11 上已装的 `v2.1.3-desktop`（产品字符串仍是 `2.1.0-desktop`）点 File → New / Import / Export，Windows 已经 invoke，但 WebView 停在 Recent Projects。这不是「菜单应该弹系统选文件框」，也不是残留 [#194](https://github.com/joe-cheung-cae/frame-pilot/issues/194) / [#195](https://github.com/joe-cheung-cae/frame-pilot/pull/195)。#194 假定 `framepilot-menu` CustomEvent 能进 React。不要重开 #194。不要动 [#41](https://github.com/joe-cheung-cae/frame-pilot/issues/41) / D3.06 托盘。不要发明第十阶段。

**分支：** `feature/leftover-win11-menu-bridge`，从 `origin/main` 开出。不要叠在 `feature/leftover-raw-develop` / [#203](https://github.com/joe-cheung-cae/frame-pilot/pull/203) 上。不要合入 `main`。实现者不合入。

**相关：** `develop_plan.md` §1.1；`apps/desktop/src-tauri/src/menu.rs`；`apps/desktop/src/App.tsx`；`apps/web/src/components/MenuCommandListener.tsx`；`apps/web/src/lib/menuRoutes.ts`。

---

## 1. 为什么是残留，不是第十阶段

第九阶段 remaining-stretch 已关闭。原生 File 菜单点击已经到达 `handle_menu_event`。`emit_menu_command` 随后 `window.eval` 派发 `framepilot-menu` CustomEvent。包装后的 Win11 WebView 上这次 eval 是静默的：缺 `main` 或 eval 失败被丢掉，MemoryRouter 从不 `push`。

产品约定不变：File → Import **只跳页**到 Import Images（或新建工程并出现 *Create a project before opening Import.*）。选文件仍在该页的 **Choose a folder** / **Choose image files**。

**不要**发明第十阶段 / S10 / 2.3。产品字符串仍是 `2.1.0-desktop`。不改 `APP_VERSION`。包装 Win11 验收是后续未签名 Release 残留——不是本 issue。

---

## 2. 已锁定决定

1. **本地优先。** 无云上传、登录、付费、遥测或捆绑神经模型。
2. **File → Import 仍只跳页。** 不要从菜单弹出原生选文件框。
3. **Rust 主通道改成 Tauri emit。** 与独立预览一样用 `app.emit(MENU_EVENT, command)`。事件名保持 `framepilot-menu`。缺 `main` 窗口或 emit 失败必须 `eprintln!`。禁止再 `let _ = window.eval(...)`。
4. **包装壳在 MemoryRouter 里 listen。** `NativeMenuListener` 用 `@tauri-apps/api/event` 的 `listen`，再 `resolveMenuCommand` + `navigator.push` + `loadLastOpenedProjectId`。`pathname` 放进 effect 依赖并重新订阅。不要把 `@tauri-apps/api` 引进 `apps/web` 的 `MenuCommandListener`。
5. **保留 CustomEvent 测试。** Web `MenuCommandListener` 与 `MenuCommandListener.test.tsx` 留给单元测试和 DOM 派发。包装路径不再依赖 eval。
6. **不改 `APP_VERSION`。** 不打 NSIS/DMG。不调度 `desktop.yml`。不动托盘 / D3.06 / #41。
7. **一个 draft PR。** 正文必须含 `Closes #204`。实现者不合入。
8. **不做：** File → Import 弹原生选文件框、签名、把空白导入页当成 #195 回退、`lib.rs` 里 sidecar 失败页的 `eval`。

---

## 3. 状态板

残留 Win11 File 菜单 invoke 不跳页

- [x] 需求拆解 — 中英残留计划 + GitHub 议题 [#204](https://github.com/joe-cheung-cae/frame-pilot/issues/204)
- [x] 开发 — `menu.rs` 改 Tauri emit；桌面 `NativeMenuListener` listen + `resolveMenuCommand`
- [x] 测试 — `npm run test:web`；桌面 `nativeMenu` 单元测试；`typecheck:desktop` / `lint:desktop`。本机 WSL 缺 pkg-config / GTK，`cargo test --lib` 无法链接；rustc 1.98.0 在场。不要编造 cargo pass。
- [ ] 上线 — 合入 + 后续未签名 Release 残留做包装 Win11 验收（实现者不合入）
- [ ] DoD-ticked — 有 #204+ NSIS 之后再勾残留计划上线；**不要**编造带日期的 Win11 GUI pass / 第十阶段 / 重勾 §2.2

---

## 4. 勾选规则

| 何时 | 勾 | 不要勾 |
| ---- | -- | ------ |
| 需求拆解 | 残留板 需求拆解 | 上线；§2.2；leftover shipped |
| 开发 + 点名测试绿灯 | 残留板 开发 + 测试 | 上线；Gatekeeper 干净；商店上架；Win11 GUI pass |
| 已发布 #204+ NSIS（Actions 或后续 Release） | 残留板上线 + DoD-ticked；§1.1 本残留已交付 | 重勾 §2.2；公开签名清单；第十阶段；编造 Win11 pass |

---

## 5. Win11 验收（有新 NSIS 之后；本 PR 不编造通过）

1. 冷启动到 Recent Projects。
2. File → Import：应到新建工程并出现 *Create a project before opening Import.*，或（有 lastOpened）到该工程 Import Images。sidecar 不再只刷三个列表的 `jobs?limit=50`。
3. File → Export / File → New 同样跳页。
4. Import Images 上 **Choose a folder** 仍是选文件入口。
5. File → Open data folder / Quit 行为不变。

宿主机证据已记录（`zhangc`，`2026-09-11T16:48:02+08:00`）：菜单 child `1000` New、`1002` Import、`1003` Export；sidecar 仍停在 `GET /api/projects` 与 `qa-144-*` 的 `jobs?limit=50`。

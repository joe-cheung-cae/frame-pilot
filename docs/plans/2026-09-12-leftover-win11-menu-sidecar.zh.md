# 残留：Win11 File 菜单在 ACL 之后仍不跳页（2026-09-12）

> 语言：**中文** | [English](2026-09-12-leftover-win11-menu-sidecar.md)

**GitHub：** [joe-cheung-cae/frame-pilot#210](https://github.com/joe-cheung-cae/frame-pilot/issues/210)。残留 [#208](https://github.com/joe-cheung-cae/frame-pilot/issues/208) / [#209](https://github.com/joe-cheung-cae/frame-pilot/pull/209)（`0418bd6`）之后，Joe 在 Win11（`zhangc`）装了 #208 NSIS。File → Import / Export **仍然不跳页**。sidecar 停在 Recent Projects。这不是残留 [#194](https://github.com/joe-cheung-cae/frame-pilot/issues/194)。不要重开 #194 / #206 / #208。不要动 [#41](https://github.com/joe-cheung-cae/frame-pilot/issues/41) / D3.06 托盘。不要发明第十阶段。

**分支：** `feature/leftover-win11-menu-sidecar`，从 `origin/main` 拉出。不要叠在 `feature/leftover-raw-develop` / [#203](https://github.com/joe-cheung-cae/frame-pilot/pull/203) 上。不要合入 `main`。实现者不合并。

**相关：** `develop_plan.md` §1.1；`apps/api/app/services/desktop_menu.py`；`apps/api/app/api/routes.py`；`apps/desktop/src-tauri/src/menu.rs`；`apps/desktop/src-tauri/src/sidecar.rs`；`apps/desktop/src/lib/nativeMenu.ts`；`apps/desktop/src/App.tsx`。

---

## 1. 为什么是残留，不是第十阶段

#204 `window.eval`、#206 `app.emit` / `listen`（仍走 `webview.eval`）、#208 `invoke("take_menu_command")` 加 default ACL，在这台包装 Win11 WebView 上都不跳页。#208 NSIS 的 exe 里已有 `allow-take-menu-command`。File → Import id=`1002` `POST=True`。sidecar 仍是 `GET /api/projects` 加三个 `jobs?limit=50`。

Path B 能调 `qa_bootstrap`，不等于生产壳的菜单 IPC 通。同一个 WebView 对 sidecar 的 loopback HTTP 已经通。

产品约定不变：File → Import **只跳页**到 Import Images（或带 *Create a project before opening Import.* 的新建工程）。选文件仍是页上的 **Choose a folder** / **Choose image files**。

不要发明第十阶段 / S10 / 2.3。产品字符串仍是 `2.1.0-desktop`。不要改 `APP_VERSION`。

---

## 2. 锁定决定

1. **本地优先。** 不要云上传、登录、付费、遥测或捆绑神经网络模型。
2. **File → Import 仍然只跳页。** 不要从菜单打开系统选文件框。
3. **包装路径走 sidecar HTTP。** `handle_menu_event` 把 `{command}` POST 到本机 `POST /api/desktop/menu-command`。`NativeMenuListener` poll `GET /api/desktop/menu-command`（取出，`Cache-Control: no-store`），再 `resolveMenuCommand` + `navigator.push`。emit/listen 和 `take_menu_command` 留作辅路。Rust 侧不要 `window.eval` / DOM `dispatchEvent`。不要加 `fs:` / `shell:`。
4. **仅桌面端点。** 没有 `FRAMEPILOT_DESKTOP=1` 就 404。只接受可跳页命令：`new`、`shortcuts`、`import`、`export`、`process`、`cull`。Host 本来就只允许 loopback。不要把 QA ACL 挪到 default。
5. **不改 `APP_VERSION`。** 本残留不打 NSIS/DMG。不 dispatch `desktop.yml`。不要托盘 / D3.06 / #41。
6. **一个 draft PR。** 正文必须有 `Closes #210`。实现者不合并。
7. **不做：** File → Import 弹系统选文件框、签名、把空白 Import 页当成 #195 回退、重开 #194 / #206 / #208。

---

## 3. 状态板

残留 Win11 File 菜单在 ACL 之后仍不跳页

- [x] 需求拆解 — 双语残留计划 + GitHub issue [#210](https://github.com/joe-cheung-cae/frame-pilot/issues/210)
- [x] 开发 — sidecar menu-command 队列；Rust POST；桌面 poll GET
- [x] 测试 — API `test_desktop_menu_command` 5；desktop `nativeMenu` sidecar take；`typecheck:desktop`；web `menuRoutes` 8。不要在这台缺 GTK 的 WSL 上编造 cargo 通过。
- [ ] 上线 — 合并 + 后续未签名 NSIS 给包装 Win11（实现者不合并）
- [ ] DoD-ticked — 有 #210+ NSIS 且 File → Import 离开三列表轮询后再勾 上线；**不要**编造带日期的 Win11 GUI 通过 / 第十阶段 / 重勾 §2.2

---

## 4. 勾选规则

| 何时 | 勾 | 不要勾 |
| ---- | ---- | ----------- |
| 需求拆解 | 残留板 需求拆解 | 上线；§2.2；leftover shipped |
| 开发 + 点名测试绿 | 残留板 开发 + 测试 | 上线；Gatekeeper-clean；商店上架；Win11 GUI 通过 |
| Joe 的 Win11 装上 #210+ NSIS，且 File → Import 离开三列表 `jobs?limit=50` 轮询 | 残留板 上线 + DoD-ticked；§1.1 leftover shipped | 重勾 §2.2；公开签名清单；第十阶段；编造 Win11 通过 |

---

## 5. Win11 验收（要等新 NSIS；本 PR 不编造通过）

1. 冷启动到 Recent Projects。
2. File → Import：带 *Create a project before opening Import.* 的新建工程，或（有 lastOpened）该工程的 Import Images。sidecar 必须离开三列表 `jobs?limit=50` 轮询。
3. File → Export / File → New 也要跳页。
4. 在 Import Images 上，选文件仍是 **Choose a folder**。
5. File → Open data folder / Quit 不变。

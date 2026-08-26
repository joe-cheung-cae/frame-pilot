# 桌面端可行性笔记

> 语言：[English](desktop_feasibility_notes.md) | **中文**

**状态：FINAL** — Phase 1 `上线`，2026-08-19T19:00:41+08:00，分支 `feature/desktop-packaging`。

Phase 0 测量仍见下文。Phase 1 收尾在 **Phase 1 notes** 和 **Phase 1 go/no-go**。`测试` 重跑了 web/desktop/verify/jobs/sidecar/cargo；`上线` 负责 §5.1 Phase 1 勾选，并记录了一次现场 `npm run dev:desktop` 窗口以及浏览器 `:3000`/`:8000`。

本主机是 **macOS**，不是 WSL2。

## 结论

**GO — close desktop Phase 0.**

| 决策 | 结果 | 原因 |
| -------- | ------ | --- |
| Close Phase 0 | **GO** | Sidecar、health、origin/Host、路径导入、CI、smoke、`npm run verify` 成立。D0.07 为 `[~]`，这是允许的。 |
| Shell | **Stay Tauri 2 + Python sidecar** | Sidecar **确实**被拉起。Tauri 编译因缺少 `rustc` 受阻。那 **不是** 切到 Electron 的触发条件。 |
| Frontend | **Vite SPA follow-up; do not export Next** | `output: 'export'` 在动态 `projects/[projectId]` 路由上失败。`apps/web` 继续用 Next.js。 |
| Scoring stack | **Keep imagehash / scipy / PyWavelets** | 未打包 sidecar 体积 **未测量**（本主机没有 PyInstaller `dist/`）。不要丢掉 scipy。 |
| Phase 1 | **Not started** | `next_stage=none`。 |

## 阻断项

### D0.07 Tauri GUI / Rust toolchain `[~]` — 2026-08-19

本主机 `上线` 期间重跑。命令和精确错误：

```text
$ cargo --version
zsh:1: command not found: cargo

$ rustc --version
zsh:1: command not found: rustc

$ command -v rustup || echo rustup not found
rustup not found
```

本工作区 eval shell 打印了同样的缺失二进制失败：

```text
(eval):1: command not found: cargo
(eval):1: command not found: rustc
```

两条命令都以 **127** 退出。捕获：`/var/folders/b6/8k06h5td1cx92vtlp6x1_z380000gn/T/grok-goal-a63c25686341/implementer/tauri-gui.txt`。

未安装系统 Rust 工具链。`npm run verify` 不调用 `cargo`、`rustc` 或 Tauri（`测试` 的 fail-if-invoked 包装器从未被调用）。`apps/desktop/` 下有一份对 verify 安全的骨架（空白 HTML health probe、`src-tauri/tauri.conf.json` 中锁定的 CSP、`src-tauri/src/lib.rs` 中的 sidecar spawn 说明）。Sidecar smoke 在没有 WebView 的情况下运行。

在有日期的 `cargo` / WebView 运行成功之前，D0.07 保持 `[~]`。缺少 `rustc` 意味着本主机无法编译 Tauri。那 **不** 意味着 Tauri 无法拉起 sidecar：Python sidecar 在 `测试` 下启动了两次，并经由 `scripts/sidecar-smoke.sh` 启动了一次。Electron 仍不在考虑范围内。

## D0.06 — Next.js `output: 'export'` spike

曾对 `apps/web/next.config.ts` 做过一次性尝试性改动：

```ts
output: 'export',
```

`npm --prefix apps/web run build` 完成编译后失败：

```text
Error: Page "/projects/[projectId]/cull" is missing "generateStaticParams()" so it cannot be used with "output: export" config.
```

当前 App Router 页面位于 `apps/web/src/app/projects/[projectId]/`，没有 `generateStaticParams`：

- `page.tsx`
- `cull/page.tsx`
- `export/page.tsx`
- `import/page.tsx`
- `process/page.tsx`

`CullingWorkspace.tsx` 从 `next/navigation` 调用 `useSearchParams()`。本次导出构建从未走到完整静态产出，因此本轮未观察到 `useSearchParams` 的 Suspense 警告。如果以后强制 export，它们仍是已知的 Next 15 App Router 问题。

一次性的 `output: 'export'` 行在同一次工作中 **已回退**。现场 `apps/web/next.config.ts` 没有 `output: 'export'`。`测试` 的 `npm run verify` 成功重建了 Next.js 15.5.19（`Generating static pages (7/7)`；五个项目路由保持动态 `ƒ`）。`apps/web` 继续用 Next.js。锁定的后续仍是 `apps/desktop` 中的 Vite SPA（Phase 1）。未开始前端迁移。Next 静态导出 **不可行**。

## 基线

2026-08-19 记录于本 macOS 主机。

Sidecar 启动和 health 来自 `测试` 现场拉起（venv 模块，不是打包二进制）：

```text
PYTHONPATH=apps/api .venv/bin/python -m app.sidecar_main --host 127.0.0.1 --port 0 --data-dir <tmp>
```

| 测量 | 结果 | 来源 |
| ----------- | ------ | ------ |
| Ready line (run 1) | `FRAMEPILOT_API ready host=127.0.0.1 port=55238 data_dir=<tmp>` | `sidecar-run-1.txt` |
| Ready line (run 2) | `FRAMEPILOT_API ready host=127.0.0.1 port=55243 data_dir=<tmp>` | `sidecar-run-2.txt` |
| `GET /health` body | `{"status":"ok","version":"2.0.0-rc2","service":"framepilot-api"}` | 两次现场运行，HTTP 200 |
| `GET /api/health` body | 相同 JSON | 仅 run 1，HTTP 200 |
| SIGTERM | 进程已退出（wait_rc=143） | 两次现场运行 |
| Sidecar smoke | `sidecar-smoke ok port=55271` | `sidecar-smoke.txt` |
| Time to ready + `/health` | 0.703 s (ready ~0.663 s, curl ~0.040 s) | `开发` venv 计时，同一主机/同一天 |
| Sidecar RSS after `/health` | 98320 KB (~96 MB) | `开发` 测量，同一主机/同一天 |
| PyInstaller `dist/framepilot-api` size | 本主机 **not built**（smoke 使用 `.venv` 模块） | 未测量 |
| Tauri hello RSS | **blocked-gui** — 缺少 rustc/WebView | `tauri-gui.txt`，2026-08-19 |
| `imagehash` | 4.3.2 已安装 | `开发` |
| `numpy` | 2.5.2 已安装 | `开发` |
| `scipy` | 1.18.0 已安装 | `开发` |
| `pywt` (PyWavelets) | 1.8.0 已安装 | `开发` |

`scripts/sidecar-smoke.sh` 通过：临时 `--data-dir`、`--port 0`、解析 ready line、curl `/health` 检查 `version`、SIGTERM、进程在 5 s 内退出。

`测试` 还记录：Phase 0 pytest **57 passed**；`npm run test:api` **211 passed**；`npm run verify` **exit 0**，且未调用 rustc/cargo。

未打包 sidecar **>250 MB** **未被观察到**，因为没有产出 PyInstaller `dist/`。保留评分栈。

## Go / no-go（最终）

`上线` 措辞，2026-08-19：

1. **Shell: GO Tauri 2 + Python sidecar.** 只有当有日期的运行表明 Tauri 无法拉起 sidecar，或 WebView 无法访问 loopback 时，Electron 才进入考虑。Sidecar **已被拉起**（venv CLI，两次，外加 smoke）。Tauri **编译**受阻（`cargo`/`rustc` command not found，2026-08-19）。编译受阻 **不是** Electron 触发条件。保留 `apps/desktop` 骨架，不要切换 shell。

2. **Frontend: GO Vite SPA follow-up. Next `output: 'export'` is not viable.** 浏览器 + Playwright 继续把 `apps/web` 留在 Next.js。不要迁移 `apps/web`。桌面 UI 仍是 Phase 1 在 `apps/desktop` 中的 Vite SPA。

3. **Scoring stack: GO keep imagehash / scipy / PyWavelets.** 丢弃触发条件是未打包 sidecar **>250 MB**。Dist 体积为 **not measured / not built**。不要丢掉 scipy。

4. **Phase 0 API 工作已到位：** loopback sidecar CLI、health `version`/`service`、origin + Host 策略、路径导入（100 文件 leftover-file 分块），以及 copy-mode 不可变性测试。`npm run test:api` 和 `npm run verify` 在无 Rust 的情况下为绿。

5. **不要从本次收尾开始 Phase 1。** 不要发布安装包、push 或打开 PR。

Phase 0 验收（见 §5.1 / D0.09）：sidecar/health/SIGTERM `[x]`；origin+Host `[x]`；路径导入 + 不可变性 `[x]`；可行性笔记 `[x]`；`test:api` + `verify` `[x]`；浏览器 web 应用 `[x]`；GUI shell `[~]`，附带上面有日期的 `cargo`/`rustc` 错误。

## Phase 1 notes — 2026-08-19

用户空间 rustup（`curl https://sh.rustup.rs -sSf | sh -s -- -y`）把 `rustc 1.97.1` / `cargo 1.97.1` 安装到 `$HOME/.cargo`。无 brew/apt。`apps/desktop/src-tauri` 中的 `cargo test` 通过了 D1.04 单元测试（分配/释放端口、ready-line 解析含带空格的 `data_dir`、拒绝 port 0 / mismatch）。D0.07 保持 `[~]`，作为 Phase 0 收尾（有日期的 `cargo`/`rustc` command not found，exit 127）。

Windows sidecar 关闭（源码；未在本 macOS 主机执行）：spawn 使用 `CREATE_NEW_PROCESS_GROUP`，关闭发送 `GenerateConsoleCtrlEvent(CTRL_BREAK_EVENT)`，等待 5s，然后 `Child::kill()`（`TerminateProcess`）。Unix 使用 SIGTERM，等待 5s，然后 kill。

D1.06 于 2026-08-19 在 `apps/desktop/src-tauri` 成功 `cargo check`（`tauri-plugin-window-state` 2.4.1，`tauri-plugin-single-instance` 2.4.3）。

D1.08 HTTP sidecar smoke（`npm run test:desktop:smoke`）于 2026-08-19 通过：ready line 为 `host=127.0.0.1` 且端口非零，`GET /health` 含 `status`/`version`/`service`，`GET /api/projects` 是 JSON 数组，攻击者 `Host` 返回可见的 HTTP 403 JSON（`Host not allowed for local FramePilot API`），桌面 Origin `:1420` CORS preflight 允许，SIGTERM 退出。HTTP smoke 脚本仍按设计打印 `desktop-smoke: skipping WebView project-list render`。

`上线` 2026-08-19T18:54:32+08:00 运行了 `npm run dev:desktop`（`npx tauri dev`）。它编译并运行了 `target/debug/framepilot-desktop`。osascript 记录进程 `framepilot-desktop`，窗口标题 `FramePilot`（1200×800）。Sidecar 以 `--host 127.0.0.1 --port 54451 --data-dir <repo>/.framepilot-desktop-dev` 拉起。`GET /health` → `{"status":"ok","version":"2.0.0-rc2","service":"framepilot-api"}`。`GET /api/projects` → `[]`。`sidecar.log` 显示 WebView `OPTIONS` 然后 `GET /api/projects` 200。Vite 在 `http://[::1]:1420/` 响应 FramePilot HTML shell。D1.08 WebView 为 `[x]`。

D1.09 退出对话框是注入的 HTML。Rust 单元测试覆盖 Kill-after-5s 以及 cancel-vs-quit-anyway 决策；pytest 覆盖 cancel/retry 和 killed-worker 启动清扫。本次收尾没有点击屏幕上的确认。

`上线` 2026-08-19T18:59:32+08:00 还运行了浏览器 `npm run dev`：`GET http://127.0.0.1:8000/health` 200，同一 health JSON；`GET http://127.0.0.1:8000/api/projects` `[]`；`GET http://127.0.0.1:3000/` 200，含 `<title>FramePilot</title>`。

## Phase 1 go/no-go（最终）

`上线` 措辞，2026-08-19T19:00:41+08:00，`feature/desktop-packaging`：

1. **GO — close desktop Phase 1** 于本功能分支。不要发布安装包。不要打开 PR。不要合并到 `main`。不要开始 Phase 2。
2. **Shell stays Tauri 2 + Python sidecar.** 用户空间 rustup 提供 `rustc 1.97.1` / `cargo 1.97.1`。`cargo test --lib` **19 passed**。Sidecar HTTP smoke 通过。`npm run dev:desktop` 打开了 `FramePilot` 窗口，其 WebView 调用了 `GET /api/projects`。D0.07 保持有日期的 `[~]`，作为 Phase 0 记录。缺失的 Phase 0 GUI **不是** Electron 触发条件。
3. **Frontend: Vite SPA in `apps/desktop`.** 共享的 navigation/API/shell 适配器已落地。`apps/web` 继续用 Next.js。现场 `npm run dev` 仍服务 `:3000` / `:8000`。
4. **`npm run verify` stays rust-free.** fail-if-invoked 的 `rustc`/`cargo`/`tauri` 包装器未被 verify 调用（`verify.log`）。
5. **Jobs:** cancel-then-retry 后没有照片停留在 `processing`；被杀死的导入经启动清扫为 `failed`+可重试；处理任务没有取消路由。见 [v2 已知限制](v2_known_limitations.zh.md)。
6. **`APP_VERSION` remains `2.0.0-rc2`.** 不要升到 `2.1.0-desktop`。

Phase 1 验收（见 §5.1）：HTTP/home 项目列表 `[x]`；sidecar health `[x]`；无 Tauri 的 `verify` `[x]`；浏览器 `:3000`/`:8000` `[x]`。

## D3.02 状态栏 — 2026-08-26

分支 `feature/d3-02-status-bar`。非 GUI 测试已通过。本机未在现场 WebView 中查看桌面状态栏。

剩余 GUI / Rust 编译验证的命令与确切错误：

```text
$ rustc --version
rustc 1.85.0 (4d91de4e4 2025-02-17) (built from a source tarball)

$ cargo --version
cargo 1.85.0 (d73d2caf9 2024-12-31)

$ cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --lib
error: rustc 1.85.0 is not supported by the following packages:
  darling@0.23.0 requires rustc 1.88.0
  ... (icu_*, plist, serde_with, time, zbus require rustc 1.86–1.88)
```

`npm run test:web`（node unit + vitest + Next build）和 `npm run typecheck:desktop` 已通过。`APP_VERSION` 仍为 `2.0.0-rc2`。未启动 `npm run dev:desktop`，因为它会触发同样失败的 `cargo` 编译。未安装 display-server 包。

直到有日期的 `cargo test` / WebView 状态栏渲染成功，D3.02 保持 `[~]`。

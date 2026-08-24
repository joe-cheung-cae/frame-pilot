# FramePilot 桌面打包实施计划

> 语言：[English](2026-08-18-desktop-packaging.md) | **中文**

> **给 Grok / Claude Goal Mode：** 必需子技能：使用 `superpowers:executing-plans`（或本文的循环）**一次只实现一个 task id**。在当前任务已实现、测试、审阅并提交之前，不要开始下一个任务。
>
> **Opus 5 审阅（2026-08-18）：** 结论已并入本计划；原审阅文件已作为冗余删除。从 **D0.00** 开始。状态见 §5.1。

**目标：** 将 FramePilot 发布为可安装的 Windows 与 macOS 桌面应用：自动启动本地 Python sidecar，复用当前 v2.0.0-rc2 筛选工作流，且永不修改原图。

**架构：** 把现有 FastAPI + SQLite 后端作为仅监听 localhost 的 sidecar。保留 `apps/web` 作为浏览器 / E2E 前端。新增 `apps/desktop`：Tauri 2 壳 + 复用 `apps/web/src/components` 与 `apps/web/src/lib` 的 Vite SPA。通过运行时注入的端口，经 `http://127.0.0.1:<port>` 与 sidecar 通信。增加分块的基于路径导入 API，使原生文件夹选择器不必经浏览器 File API 再上传成千上万张照片字节。

**技术栈：** Tauri 2（Rust）、PyInstaller sidecar、FastAPI/Uvicorn、Vite + React 19 + TypeScript + Tailwind，以及现有 SQLModel/SQLite/Pillow/imagehash 栈。

**产品计划来源：** `docs/desktop_development_plan.md`  
**当前产品基线：** FramePilot `2.0.0-rc2` 本地 Web 应用  
**建议分支：** `feature/desktop-packaging`  
**首个桌面版本：** `2.1.0-desktop`（`2.0.x` 继续作为本地 Web 产品线）

---

## 0. 文档层级

| 问题 | 事实来源 |
| ---- | -------- |
| 为何做桌面版、范围、阶段、UI 意图、工作量估算 | `docs/desktop_development_plan.md`（产品） |
| 每一项技术决策、task id、文件路径、测试、命令、验收框 | 本文件（实施） |
| 一次会话中 agent 可以做什么、不可以做什么 | `docs/desktop_goal_mode.md` + `AGENTS.md` |
| 实测结果、阻塞项、go/no-go 记录 | `docs/desktop_feasibility_notes.md` |
| 仓库级约束（本地优先、原图安全、英文、测试） | `AGENTS.md`，然后是 `develop_plan.md` |

冲突规则：任何技术冲突以本实施计划为准，且必须在解决冲突的同一次提交中修改产品计划。产品计划永不新增 task id。

---

## Goal Mode 必须如何工作

把 `docs/desktop_goal_mode.md` 复制进 Grok Build Goal Mode。agent 必须对**每一个** task id 执行此循环：

1. 阅读 `develop_plan.md`、`AGENTS.md`、本计划（含 §5.1）以及 `git status`。
2. 选取依赖已是 `[x]` 的、编号最低的未完成（`[ ]`）task id。
3. **先**编写任务中点名的测试，并确认它们因正确原因失败。
4. 只实现该任务，做到最小，直到那些测试通过。
5. 运行所列命令。修到全绿。
6. 审阅 `git diff`。
7. 在 §5.1 勾选该任务（或标 `[~]`，并在 `docs/desktop_feasibility_notes.md` 留下带日期的说明）。
8. 将实现、测试与跟踪表勾选连同建议的提交说明一起提交。
9. 然后才开始下一个任务。

不要把 Phase 0 打包试探与 Phase 3 UI 打磨混在一次提交里。不要提交失败的测试。不要修改原图。不要加入云、登录、支付或捆绑模型文件。

如果任务无法安全完成：缩小它，提交更小的绿色切片，并在 `docs/desktop_feasibility_notes.md` 留下阻塞说明（若缺失则在 D0.01 创建该文件）。

会话预算：每次会话最多 **5 个 task id 或一个阶段**，然后停止并总结。

---

## 1. 当前仓库状态（2026-08-18）

已对照当时的活树核对。桌面打包当时**尚未开始**。

| 区域 | 当时状态 | 桌面含义 |
| ---- | -------- | -------- |
| Version | 根目录 / `apps/web` / `apps/api` 以及 `FastAPI(version=...)` 中为 `2.0.0-rc2` | D0.02 单一来源 `apps/api/app/core/version.py`；仅在 D5.04 升版本 |
| Frontend | Next.js 15 App Router、React 19、客户端 fetch | 不要用 Server Actions、middleware 或 `next/image` |
| API base | `apps/web/src/lib/api.ts:1` 中 `NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000"` | 模块级常量看不到加载之后注入的端口 |
| Import | 仅 multipart `UploadFile`（`apps/api/app/api/routes.py:281-299`）；最多 100 个文件（`importing.py:43`） | 路径导入必须分块展开；永不在一次 HTTP 调用中复制 2000 个文件 |
| Project path | 手输文本框；API 拒绝 `{data_dir}/projects` 或 allowlist 之外的根（`projects.py:33-37`）；非空目录需要 `acknowledge_nonempty`（`projects.py:40-43`） | 原生选择器需要 D2.00 注册 + 确认 UI |
| Drag-drop | 未实现 | 新的桌面工作 |
| CORS/origin | 写请求必须来自 `localhost:3000` 或 `:3100`（`apps/api/app/main.py:14-65`）；GET 没有 Host 检查 | Tauri origin 会 403；GET 资源存在 DNS rebinding |
| Data dir | `FRAMEPILOT_DATA_DIR` 或相对 CWD 的 `.framepilot-data`；`create_app()` 在 import 时运行（`main.py:76`） | 冻结后的 CWD 不可用；必须有 `--data-dir`；必须在 import `app.main` **之前**设置环境变量 |
| Jobs | 进程内 FastAPI `BackgroundTasks` | 没有 D1.09 时，导入中退出看起来像丢数据 |
| Health | `GET /health` 与 `GET /api/health` → `{"status": "ok"}`；`test_projects_api.py:19` 精确相等断言 | 保留 `status`；从单一来源加 version |
| CI | 无 `.github/workflows` | 先做 D0.00 |
| Artifact check | `scripts/check-release-artifacts.sh` 阻止所有被跟踪的 `*.png` | 任何图标提交之前必须先做 D0.07a |
| Tauri/Electron | 仅文档 | 全新的 `apps/desktop` + `packaging/` |
| E2E | Playwright 打 Next `:3100` + API `:8000`；`ImportPanel.tsx` 文件输入在 234–261 | 桌面不得移除浏览器文件输入 |
| Test runners | `src/lib/*.test.ts` = node `--test`；vitest 只收集 `src/**/*.test.tsx` | React 适配层测试必须是 `.test.tsx` |

### 前端 export 试探预期

`output: 'export'` **不能直接套用**。五条 `projects/[projectId]/...` 路由没有 `generateStaticParams`。**不要把 `apps/web` 迁离 Next.js。** D0.06 仅为文档。

### 环境说明（本机）

当时工作区是 **Linux WSL2**。PyInstaller sidecar 工作可以在此推进。WSL 内 Tauri 窗口可能失败。不要因为 GUI 阻塞后端 / API 任务。§5.1 中的 `[~]` 在没有记录的 GUI 运行（Windows 主机、macOS 或 CI）之前，永远不要升为 `[x]`。

---

## 2. 锁定决策

除非 Phase 0 在 `docs/desktop_feasibility_notes.md` 中写出 go/no-go 变更，Goal Mode 期间不再重开这些决策。

1. **壳：** Tauri 2 + Python sidecar。仅当 D0.09 之后书面确认 Tauri 受阻时才用 Electron。
2. **后端：** 保留 FastAPI。用 PyInstaller one-dir（不是 one-file）打包，因为 numpy/scipy/Pillow 从 one-file 解压加载很差。
3. **前端：** 双壳、单组件库。
   - `apps/web` = Next.js，用于浏览器 + Playwright。
   - `apps/desktop` = Tauri + Vite SPA。
   - 共享：`apps/web/src/components/*`、`apps/web/src/lib/*`、`apps/web/src/store/*`。
   - 导航适配层用 **Vite alias** 替换，而不是一个再导出 `next/link` 的 barrel。
4. **IPC：** v2.1 用 HTTP 打 sidecar。不要把评分 / 分组改写到 Rust。可选的 Tauri IPC 仅用于对话框、路径和在文件夹中显示。
5. **导入：** 基于路径的导入是桌面主路径。保留 multipart 以保持浏览器对等。
6. **绑定：** sidecar 只监听 `127.0.0.1`。永不 `0.0.0.0`。
7. **端口：** Tauri 分配空闲回环 TCP 端口，并始终传入显式 `--port <n>`。sidecar 也支持 `--port 0` 供测试与独立使用；该模式下它自己绑定套接字，经 `getsockname()` 解析真实端口，打印 ready 行，然后才开始 serve。sidecar 永不猜测或重新报告端口 0。
8. **数据目录：** Tauri 把 `--data-dir` / `FRAMEPILOT_DATA_DIR` 设为操作系统应用支持目录：
   - macOS: `~/Library/Application Support/FramePilot`
   - Windows: `%APPDATA%\FramePilot`
   - Linux（仅开发）：`~/.local/share/FramePilot`
     sidecar 的 `--data-dir` **必填**。永不回退到相对 CWD 的 `.framepilot-data`。
9. **安全：** 复制模式存储不变。原图复制进项目；源文件永不被修改或删除。资源 / 导出路径约束测试必须保持全绿。
10. **Web 应用必须继续工作。** 每次触及共享代码的桌面提交之后，`npm run dev`、`npm run verify` 和 Playwright 必须保持全绿。
11. **桌面上的项目根：** `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` 仍是部署级控制，Tauri 壳永远不得把它设为 `$HOME`、`/`、盘符根或任何过宽的父目录。用户选择的项目根只有在 D2.00 注册并持久化到 `{data_dir}/desktop_project_roots.json` 之后才合法。`test_create_project_rejects_root_outside_allowlist` 必须保持全绿且不变。
12. **路径导入请求形态：** 一次 HTTP 请求最多消费 `IMPORT_MAX_FILES_PER_REQUEST`（100）个展开后的文件，并返回 `remaining_paths` 与 `expanded_total`。客户端用同一个 `job_id` 循环。2000 张照片的文件夹永远不是一次 HTTP 调用。
13. **GUI 阻塞的任务：** 当剩余验证需要真实 WebView 且主机无法打开时，标 `[~]`，追加带日期的可行性说明，并继续做未阻塞的工作。没有记录的 GUI 运行时，`[~]` 永远不是 `[x]`。
14. **桌面下载：** 桌面壳不通过 WebView 下载 API 响应。每种导出模式已经返回 `output_path`；桌面在文件管理器中显示产物。浏览器保留 `<a download>`。
15. **单一版本来源：** `apps/api/app/core/version.py` 定义 `APP_VERSION`。`main.py` 和两个 health 端点读取它。`pyproject.toml` 和两个 `package.json` 仅在 D5.04 更新。
16. **壳检测：** `window.__FRAMEPILOT_DESKTOP__ === true`，由 Tauri 在前端加载前注入。共享代码只通过 `apps/web/src/lib/shell.ts` 中的 `isDesktopShell()` 读取它。

---

## 3. 硬约束

从 `AGENTS.md` 与 `develop_plan.md` 复制而来；适用于每一个桌面任务：

- 仅本地优先。不要云上传、账户、支付、遥测要求或远程处理。
- 永不修改或删除原始照片文件。
- 不要提交私人照片、生成的数据集、SQLite 文件、安装包或大模型文件。
- 代码、注释、测试、文档、提交说明和新 UI 字符串使用英文。
- 优先小型确定性算法。本桌面轨道不要加入 HEIC/RAW/XMP/模型。
- 不要从零重启产品。
- 不要削弱导出 / 资源路径逃逸测试。
- 提交说明使用英文。首选前缀：`desktop:`、`api:`、`web:`、`test:`、`docs:`、`ci:`。
- 不要把 `scripts/check-release-artifacts.sh` 放宽到超出单一显式 `apps/desktop/src-tauri/icons/` 例外（D0.07a）。
- 不要削弱 `apps/api/tests/test_projects_api.py::test_create_project_rejects_root_outside_allowlist`。
- 每个任务都带有 Depends on / Files / Implement / Tests / Commit。

---

## 4. 目标目录树

```text
frame-pilot/
├── apps/
│   ├── api/                      # existing FastAPI; add sidecar CLI
│   ├── web/                      # existing Next.js browser app
│   └── desktop/                  # NEW
│       ├── package.json
│       ├── vite.config.ts
│       ├── index.html
│       ├── src/                  # Vite entry, router, desktop adapters
│       └── src-tauri/
│           ├── Cargo.toml
│           ├── tauri.conf.json
│           ├── capabilities/
│           ├── icons/            # allowed by D0.07a exception only
│           └── src/lib.rs
├── packaging/
│   ├── pyinstaller/
│   │   ├── framepilot-api.spec
│   │   ├── hooks/
│   │   └── build.sh
│   └── scripts/
│       └── stage-sidecar.sh
├── tests/
│   ├── e2e/                      # existing Playwright (keep)
│   └── desktop/                  # NEW sidecar/lifecycle smokes (shell, not pytest under apps/api)
├── docs/
│   ├── desktop_development_plan.md
│   ├── desktop_goal_mode.md
│   ├── desktop_feasibility_notes.md
│   └── plans/2026-08-18-desktop-packaging.md
└── .github/workflows/
    ├── verify.yml                # D0.00
    └── desktop.yml               # D4.04
```

---

## 5. 共享验收门槛

除非任务列出更窄的命令，否则运行这些：

```bash
npm run lint:api
npm run test:api
npm run typecheck # if web/desktop TS changed
npm run test:web  # if apps/web changed
npm run verify    # before finishing a phase; must not require Rust
```

仅桌面的额外项，随阶段加入：

```bash
npm run test:sidecar       # D0.05+
npm run typecheck:desktop  # D1.03a+
npm run test:desktop:smoke # D1.08+
```

原图安全始终在范围内：任何导入 / 导出变更必须让 `apps/api/tests/test_ranking_export.py` 与导入不可变覆盖保持通过。

### 5.1 任务跟踪表

状态键：`[ ]` 未开始，`[x]` 已完成并提交，`[~]` 阻塞于 GUI 或签名能力（锁定决策 13），`[-]` 已取消或已迁移。

更新此列表必须与它所描述的任务**在同一次提交**中完成。

Phase 0 — 已于 2026-08-19 在 `refactor` 上 `上线` 关闭（GO；Phase 1 未开始）

- [x] D0.00 CI verify 工作流
- [x] D0.01 Sidecar CLI 启动器
- [x] D0.02 带 version 的 health 负载
- [x] D0.03 Origin 与 Host 策略
- [x] D0.04a 导入路径展开辅助函数
- [x] D0.04b 基于路径的导入端点
- [x] D0.04c 路径导入不可变测试
- [x] D0.05 PyInstaller spec 与 sidecar smoke
- [x] D0.06 Next static export 试探（文档）
- [x] D0.07a Tauri artifact / gitignore 卫生
- [~] D0.07 最小 Tauri 壳与 sidecar 健康检查 — Phase 0 (2026-08-19T08:26:40Z) `cargo --version` / `rustc --version`: `zsh:1: command not found: cargo` / `zsh:1: command not found: rustc` (exit 127)。Phase 0 收尾时该框保持 `[~]`。Phase 1 后来安装了用户空间 rustup 并打开了 FramePilot 窗口（见 D1.08）。编译受阻并不是切换 Electron 的触发条件；sidecar 已被拉起。见 `docs/desktop_feasibility_notes.md`。
- [x] D0.08 基线
- [x] D0.09 Go / no-go

Phase 1 — 已于 2026-08-19 在 `feature/desktop-packaging` 上 `上线` 关闭（GO；Phase 2 未开始）

- [x] D1.01 导航适配层
- [x] D1.02 运行时 API base
- [x] D1.02a 桌面壳标志
- [x] D1.03a Vite 构建、别名、Tailwind
- [x] D1.03b 桌面路由器
- [x] D1.04 Rust 中的 sidecar 生命周期
- [x] D1.05 应用支持数据目录
- [x] D1.06 窗口基础与单实例
- [x] D1.07 开发脚本与 verify 接线
- [x] D1.08 桌面 smoke：health + 项目列表 — HTTP `[x]`（`npm run test:desktop:smoke` 两次，2026-08-19T18:54:03+08:00 / 18:54:04+08:00）。WebView `[x]` 2026-08-19T18:54:32+08:00 `npm run dev:desktop` 打开窗口标题 `FramePilot`；sidecar `127.0.0.1:54451` `GET /health` 以及 WebView `OPTIONS`+`GET /api/projects` 200（空列表 OK）。
- [x] D1.09 有运行中任务时的优雅退出

Phase 2

- [x] D2.00 已注册的项目根
- [x] D2.01 原生文件对话框适配器
- [x] D2.02 用原生选择器创建项目
- [x] D2.03 导入面板路径导入
- [x] D2.04 拖放
- [x] D2.05 在文件管理器中显示项目与导出文件夹
- [x] D2.06 最近项目
- [x] D2.07 跨平台路径加固
- [x] D2.08 完整工作流验证
- [x] D2.09 显示导出产物而不是下载

Phase 3

- [ ] D3.01 原生菜单栏
- [ ] D3.02 状态栏
- [ ] D3.03 设置中的数据目录（`GET /api/meta`）
- [ ] D3.04 跟随系统主题
- [ ] D3.05 空状态与错误文案
- [ ] D3.06 可选托盘（可能以 `[-]` 结束）
- [ ] D3.07 快捷键与菜单加速键核对

Phase 4

- [ ] D4.01 把 sidecar 打进 Tauri resources
- [ ] D4.02 NSIS 与 DMG 配置
- [-] D4.03 已迁移到 D0.00
- [ ] D4.04 桌面 CI 矩阵
- [ ] D4.05 签名手册
- [ ] D4.06 体积核对

Phase 5

- [ ] D5.01 桌面测试矩阵
- [ ] D5.02 README 与用户文档
- [ ] D5.03 桌面性能说明
- [ ] D5.04 版本升到 2.1.0-desktop
- [ ] D5.05 已知限制

---

## Phase 0 — Feasibility and desktop-critical API (about 3–5 days)

**Phase goal:** Prove sidecar can be packaged and hosted; land APIs the desktop shell cannot live without.

**Phase exit:** §5.1 Phase 0 boxes are `[x]` or `[~]` per locked decision 13. `docs/desktop_feasibility_notes.md` records baselines and go/no-go.

### D0.00 — CI verify workflow (web/api, no GUI)

**Depends on:** none — implement this first  
**Files:**

- Create: `.github/workflows/verify.yml`

**Implement:**

- Triggers: `pull_request`, and `push` to `main` and `feature/desktop-packaging`.
- Single job on `ubuntu-latest`: checkout, Python 3.11, Node 22.
- Steps: `npm run install:all`, then `npm run verify`.
- Do not install Rust. Do not run Playwright here.
- Concurrency group per ref with `cancel-in-progress: true`.

**Tests:** none (CI config). Run locally before commit: `npm run verify`

**Commit:** `ci: run npm verify on pull requests`

### D0.01 — Sidecar CLI launcher

**Depends on:** none  
**Files:**

- Create: `apps/api/app/sidecar_main.py`
- Create: `docs/desktop_feasibility_notes.md` (stub: Blockers + Baselines)
- Modify: `apps/api/pyproject.toml` (`[project.scripts] framepilot-api = "app.sidecar_main:main"`)
- Test: `apps/api/tests/test_sidecar_cli.py`

**Implement:**

- argparse: `--host` (default `127.0.0.1`), `--port` (default `8000`, `0` = ephemeral), `--data-dir` (**required**), `--log-level` (default `info`).
- Exit code 2 if `--host` is not `127.0.0.1` or `localhost`.
- Exit code 2 if `--data-dir` is missing or not absolute. Never fall back to CWD-relative `.framepilot-data`.
- Set `os.environ["FRAMEPILOT_DATA_DIR"]` **before** the first `import app.main`. `app.main` builds the app at import time (`main.py:76`), so the import must happen inside `main()` after argparse.
- Port discovery: bind a `socket` yourself, read `getsockname()[1]`, print the ready line, then `uvicorn.Server(config).run(sockets=[sock])`. On POSIX set `SO_REUSEADDR`; do not set it on Windows (port hijacking).
- Print exactly one stdout line after bind and before serve, `flush=True`: `FRAMEPILOT_API ready host=127.0.0.1 port=<actual> data_dir=<path>`. `<actual>` comes from `getsockname()`, never from the parsed argument.
- Pass the FastAPI **object** to uvicorn, not the string `"app.main:app"`.
- All logs go to stderr. Never print anything else to stdout.

**Tests (write first):**

- `parse_args` rejects `--host 0.0.0.0` and `--host 192.168.1.5` (exit 2).
- `parse_args` rejects a missing or relative `--data-dir`.
- `bind_listen_socket("127.0.0.1", 0)` returns a socket whose port is non-zero and address is `127.0.0.1`; close it in the test.
- `ready_line(...)` renders the exact expected string.
- `--data-dir` is applied before settings load.
- `--help` exits 0.
- Do not start a live server; monkeypatch `uvicorn.Server.run`.

**Commit:** `api: add localhost-only sidecar CLI`

### D0.02 — Health payload for desktop probes

**Depends on:** D0.01  
**Files:**

- Create: `apps/api/app/core/version.py` (`APP_VERSION = "2.0.0-rc2"`)
- Modify: `apps/api/app/main.py` (`FastAPI(version=APP_VERSION)`, `/health`)
- Modify: `apps/api/app/api/routes.py` (`/api/health`)
- Modify: `docs/api.md`
- Test: `apps/api/tests/test_projects_api.py` (assertion currently `== {"status": "ok"}` at line 19)

**Implement:** both `/health` and `/api/health` return:

```json
{ "status": "ok", "version": "2.0.0-rc2", "service": "framepilot-api" }
```

`version` is `APP_VERSION`. No extra version literals in `main.py`, `routes.py`, or tests. Keep `status` as `"ok"` (`playwright.config.ts:23`).

**Tests:**

- `test_api_health_returns_ok` asserts `status`, `service`, and `version == APP_VERSION`.
- Same for unprefixed `/health`.
- `create_app().version == APP_VERSION`.

**Commit:** `api: extend health payload with version`

### D0.03 — Origin and Host policy for desktop without weakening local web

**Depends on:** none (can parallel D0.01)  
**Files:**

- Create: `apps/api/app/core/origins.py`
- Modify: `apps/api/app/main.py` (allowlist, CORS, mutation guard)
- Test: `apps/api/tests/test_desktop_origins.py`

**Implement:**

- `allowed_origins()`: always the current four web origins (3000 and 3100). When `FRAMEPILOT_DESKTOP=1`, also `http://localhost:1420`, `http://127.0.0.1:1420`, `http://tauri.localhost`, `https://tauri.localhost`, `tauri://localhost`.
- Compute the set **inside `create_app()`**. Feed both `CORSMiddleware` and the mutating-origin guard. `allow_credentials=True` stays; wildcard is forbidden.
- Host check on **all** methods: 403 unless hostname is `127.0.0.1`, `localhost`, `::1`, or `tauri.localhost`. Missing Host is rejected. This closes DNS rebinding against GET `/api/projects`, `/api/assets/...`, and export download.
- Do not disable the origin guard globally.

**Tests:**

- POST `/api/projects` Origin `http://localhost:3000` → 201.
- POST Origin `https://evil.example` → 403 with the existing detail.
- POST Origin `tauri://localhost` → 403 unless `FRAMEPILOT_DESKTOP=1`.
- POST with **no** Origin → 201 (Host check is why this is safe).
- GET `/api/projects` `Host: attacker.example` → 403; `Host: 127.0.0.1:8000` → 200.
- Desktop-mode CORS preflight for `tauri://localhost`.

**Commit:** `api: allow Tauri origins and reject non-loopback hosts in desktop mode`

### D0.04a — Import path expansion helper (pure, no HTTP)

**Depends on:** none  
**Files:**

- Modify: `apps/api/app/services/importing.py`
- Test: `apps/api/tests/test_import_path_expansion.py`

**Implement:** add next to `IMPORT_MAX_FILES_PER_REQUEST`:

```python
PATH_IMPORT_MAX_INPUT_ENTRIES = 5000
PATH_IMPORT_MAX_EXPANDED_FILES = 20000
```

`expand_import_paths(paths, project_root) -> ExpandedImportPaths` with `files` and `skipped`.

Rules:

- `ValueError` for empty list, too many input entries, any non-absolute path, missing path, or expansion over the cap.
- Directories: `os.walk(followlinks=False)`; drop entries whose `resolve()` is not under the walked root.
- Regular files only (`stat.S_ISREG`). Skip FIFOs/devices (`mkfifo photo.jpg` would block `_copy_file_to_path` forever).
- Extension filter reuses existing supported/unsupported helpers (HEIC/RAW skip reasons match upload).
- Skip sources under `project_root.resolve()` (`"Source is inside the project folder"`).
- Deduplicate by resolved path; sort for determinism.

**Tests:** nested JPEGs + txt + heic; relative/missing/empty errors; symlink-out not followed (POSIX); FIFO skipped (POSIX); file inside project originals skipped; deterministic order.

**Commit:** `api: add import path expansion helper`

### D0.04b — Path-based import endpoint

**Depends on:** D0.04a  
**Files:**

- Modify: `apps/api/app/schemas/api.py`, `apps/api/app/api/routes.py`
- Test: `apps/api/tests/test_import_from_paths.py`
- Docs: `docs/api.md`

**Implement:**

```
POST /api/projects/{project_id}/imports/from-paths
{"paths": ["/abs/folder", "/abs/file.jpg"], "job_id": null, "expected_total": null, "finalize": true}
```

- Expand; `ValueError` → 422.
- Consume at most 100 expanded files. Return `remaining_paths` + `expanded_total`. Client re-posts remainder with the same `job_id`; `finalize: true` only on the last slice.
- Reuse multipart control flow (active-import 409, stale-job, expected_total).
- Per file: `source.open("rb")` then existing `register_import_file`. Do not add a second copy path.
- Queue derivative job on the same `finalize` terms as multipart.
- When finalize, a single input directory was given, and `source_root_path` is empty, record it as read-only metadata. No rescan.
- Multipart `ImportResult` gains `remaining_paths: []` and `expanded_total` so the browser client stays compatible.

**Tests:** two JPEGs; 250-file three-request loop with one job; relative/empty 422; concurrent 409; destinations under `originals/`; unsupported skip reason; `docs/api.md` documents the loop.

**Commit:** `api: add path-based local import`

### D0.04c — Original-file immutability for path import

**Depends on:** D0.04b  
**Files:**

- Test: `apps/api/tests/test_import_from_paths_immutability.py`

**Implement:** no production change expected. If a test fails, fix the service, not the test.

**Tests:** source `st_size` / `st_mtime_ns` / SHA-256 unchanged; directory entry count unchanged; not a hard link to the copy (POSIX); read-only source dir still imports (POSIX, skip as root); cancel mid-import leaves sources untouched.

**Commit:** `test: assert path import never mutates source files`

### D0.05 — PyInstaller spec and Linux sidecar smoke

**Depends on:** D0.01, D0.02  
**Files:**

- Create: `packaging/pyinstaller/framepilot-api.spec`, `packaging/pyinstaller/build.sh`, `packaging/pyinstaller/hooks/hook-app.py` if needed
- Create: `scripts/sidecar-smoke.sh` (not a pytest file under repo-root `tests/desktop/` — `npm run test:api` only collects `apps/api/tests`)
- Modify: root `package.json` (`packaging:sidecar`, `test:sidecar`)

**Implement:**

- one-dir build named `framepilot-api`.
- Hiddenimports: `app.main`, `app.sidecar_main`, `uvicorn.loops.auto`, `uvicorn.protocols.http.auto`, `uvicorn.protocols.websockets.auto`, `uvicorn.lifespan.on`, `uvicorn.lifespan.off`, `httptools`, `sqlalchemy.dialects.sqlite`, `PIL.JpegImagePlugin`, `PIL.PngImagePlugin`, `PIL.WebPImagePlugin`, `imagehash`, `numpy`, scipy submodules pulled by imagehash.
- Pass the FastAPI object, not `"app.main:app"`.
- Windows: document `--loop asyncio` if uvloop is absent.
- `build.sh` must fail if `/health` is not OK after start.
- Do not commit `dist/` (`dist/` and `build/` are already gitignored).

**Tests:** `bash scripts/sidecar-smoke.sh` — tmp `--data-dir`, `--port 0`, parse ready line, curl `/health` for `version`, SIGTERM, exit within 5s, no leftover children.

**Commit:** `desktop: add PyInstaller sidecar spec and smoke`

### D0.06 — Next.js static export spike (document only)

**Depends on:** none  
**Files:** `docs/desktop_feasibility_notes.md`

**Implement:** Attempt `output: 'export'` in a throwaway change. Record whether `next build` succeeds, what happens to `projects/[projectId]` routes, and `useSearchParams` Suspense warnings. Revert any Next config that breaks `npm run test:web`. Locked follow-up is Vite SPA.

**Tests:** none (documentation). After revert: `npm run test:web` if any Next config was touched.

**Commit:** `docs: record Next static export spike`

### D0.07a — Keep `npm run verify` green with Tauri assets

**Depends on:** D0.00  
**Files:**

- Modify: `scripts/check-release-artifacts.sh`, `.gitignore`
- Test: `scripts/test-release-checks.sh`

**Implement:**

- Add exactly one exception after the blocked-pattern match:

```bash
allowed_pattern='^apps/desktop/src-tauri/icons/[^/]+\.(png|ico|icns)$'
```

- Do not broaden `blocked_pattern`. Do not add any other exception.
- `.gitignore`: add `target/` and `.framepilot-desktop-dev/`.

**Tests:** tracked `apps/desktop/src-tauri/icons/128x128.png` passes; tracked `apps/desktop/other.png` still fails.

**Commit:** `desktop: allow tauri icons in the release artifact check`

### D0.07 — Minimal Tauri 2 hello + sidecar spawn

**Depends on:** D0.01, D0.03, D0.05, D0.07a  
**Files:**

- Create: `apps/desktop/**` skeleton plus `apps/desktop/src-tauri/icons/` (32x32.png, 128x128.png, 128x128@2x.png, icon.icns, icon.ico)
- Modify: root `package.json` (`dev:desktop`)

**Implement:**

- Tauri 2 blank window.
- Spawn sidecar (dev: venv uvicorn via sidecar CLI; prod later) with `--host 127.0.0.1 --port <free> --data-dir <app-support>`.
- Set `FRAMEPILOT_DESKTOP=1`.
- Poll `/health` (15s timeout). Show “API ready” or the error.
- On exit: SIGTERM, then kill after 5s.
- Locked CSP (`app.security.csp`):

```text
default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';
img-src 'self' data: blob: http://127.0.0.1:* http://localhost:*;
connect-src 'self' http://127.0.0.1:* http://localhost:* ipc: http://ipc.localhost;
font-src 'self' data:; object-src 'none'; frame-ancestors 'none'
```

`assetUrl` returns absolute `http://127.0.0.1:PORT/...` used in `<img src>` (`ImportPanel.tsx`, `CullingWorkspace.tsx`). Missing `img-src` looks like a backend bug.

If WSL cannot open a WebView: keep the Rust spawn/health code, run sidecar smoke without GUI, mark `[~]`.

**Tests:** none (Rust/config). Run: `npm run verify`, `bash scripts/sidecar-smoke.sh`. Record WebView result or WSL error in feasibility notes.

**Commit:** `desktop: add minimal Tauri shell with sidecar health`

### D0.08 — Measure baselines

**Depends on:** D0.05, D0.07  
**Files:** `docs/desktop_feasibility_notes.md`

Record, even if only Linux sidecar: dist size, RSS after `/health`, time to `/health`, Tauri hello RSS or “blocked on WSL”, scipy/pywavelets presence.

**Tests:** none (documentation).

**Commit:** `docs: record desktop feasibility baselines`

### D0.09 — Go / no-go

**Depends on:** D0.06, D0.08  
**Files:** `docs/desktop_feasibility_notes.md`

Write: Shell Tauri 2 (or Electron only if Tauri cannot spawn sidecar / WebView cannot reach loopback). Frontend Vite SPA. Keep imagehash/scipy unless unpacked sidecar **>250 MB**.

**Tests:** none (documentation). Run: `npm run test:api`

**Phase 0 acceptance** (ticked `上线` 2026-08-19; GUI remains `[~]`):

- [x] Sidecar starts, answers `/health`, exits on SIGTERM
- [x] Origin + Host policy rejects random sites and attacker Host headers
- [x] Path-based import exists, chunks at 100, does not mutate sources
- [x] Feasibility notes committed
- [x] `npm run test:api` and `npm run verify` green
- [x] Browser web app still runs
- [~] GUI shell is `[x]` or `[~]` with a recorded command/error — 2026-08-19 `cargo --version` / `rustc --version`: command not found (exit 127); see `docs/desktop_feasibility_notes.md`

---

## Phase 1 — Desktop Shell and Sidecar Lifecycle (about 1.5–2 weeks)

**Phase goal:** `npm run dev:desktop` opens FramePilot UI that can list projects through the sidecar (or `[~]` with a Vite/HTTP equivalent on WSL).

### D1.01 — Navigation adapter (keep Next working)

**Depends on:** Phase 0 exit  
**Files:**

- Create: `apps/web/src/lib/navigation.ts`, `apps/web/src/lib/navigation.next.tsx`
- Modify (grep-verified): `Shell.tsx`, `ProjectList.tsx`, `ProjectDashboard.tsx`, `ProcessingPanel.tsx`, `ImportPanel.tsx`, `ProjectCreator.tsx`, `CullingWorkspace.tsx`
- Modify mocks: `CullingWorkspace.test.tsx`, `ProcessingPanel.test.tsx`, `ImportExportPanels.test.tsx`
- Test: `apps/web/src/lib/navigation.test.tsx` (not `.test.ts` — node `--test` has no JSX; vitest only collects `*.test.tsx`)

**Implement:**

- Types + re-export point only. `Link`, `useNavigator`, `useQueryParams` come from `./navigation.next` in the web build.
- Desktop Vite aliases that module to `apps/desktop/src/navigation.router.tsx` in D1.03a. A barrel that re-exports `next/link` would pull Next into Vite.
- `useQueryParams(): URLSearchParams` hides Next vs React Router shape differences. `CullingWorkspace.tsx` must consume only the wrapper.
- Shared components import `@/lib/navigation` only. No `next/link` or `next/navigation` under `apps/web/src/components/`.
- Re-point existing mocks at `@/lib/navigation` in the same commit.

**Tests:** Link renders `<a href>`; `push` called with expected href; `useQueryParams` reads a value; guard that components do not import `next/link` or `next/navigation`; existing component tests pass. Run: `npm run typecheck && npm run test:web`

Allowed split: (a) adapter + tests, (b) Shell/list/dashboard/processing, (c) import/creator/culling + mocks. Finish all three before D1.03a.

**Commit:** `web: isolate Next navigation behind an adapter`

### D1.02 — Runtime API base (stop baking :8000)

**Depends on:** D1.01  
**Files:**

- Create: `apps/web/src/lib/apiBase.ts`, `apps/web/src/types/globals.d.ts`
- Modify: `apps/web/src/lib/api.ts` (`API_BASE`, `request`, `exportDownloadUrl`, `assetUrl`)
- Test: `apps/web/src/lib/apiBase.test.ts`, `apps/web/src/lib/api.test.ts`

**Implement:**

- `resolveApiBase()`: `window.__FRAMEPILOT_API_BASE__`, then `NEXT_PUBLIC_API_BASE_URL`, then `http://127.0.0.1:8000`. Safe when `window` is undefined (`next build`).
- Keep exporting `API_BASE` but read `resolveApiBase()` **at call time** inside `request` / URL helpers. A frozen module-level constant cannot see a port injected after load.
- Trim trailing slash. Declare Window extras in `globals.d.ts`.

**Tests:** window wins; env second; default third; trailing slash trimmed; no throw without window; with injected base, `assetUrl` and `exportDownloadUrl` use that host; existing encoding assertions still hold with the default.

**Commit:** `web: resolve API base at runtime for desktop`

### D1.02a — `window.__FRAMEPILOT_DESKTOP__` shell flag

**Depends on:** D1.02  
**Files:**

- Create: `apps/web/src/lib/shell.ts`
- Test: `apps/web/src/lib/shell.test.ts` (and `.test.tsx` if DOM is required)

**Implement:** `isDesktopShell()` is true only for literal `true`. `applyShellDataset()` sets `document.documentElement.dataset.shell`. Call from desktop entry (D1.03b) and from `Providers.tsx` (browser → `"browser"`). D3.02/D3.04 consume the helper / `[data-shell="desktop"]`, never inline `window` checks.

**Tests:** true only for `true`; false for undefined/`"1"`/`0`; no throw without window.

**Commit:** `web: add desktop shell detection helper`

### D1.03a — Vite desktop build with shared aliases and Tailwind

**Depends on:** D1.01, D1.02  
**Files:**

- Create: `apps/desktop/package.json`, `index.html`, `vite.config.ts`, `tsconfig.json`, `tailwind.config.ts`, `postcss.config.js`, `src/main.tsx`, `src/styles.css`
- Modify: root `package.json` (`install:all`, `typecheck:desktop`, `lint:desktop`; add both to `verify` **without** Rust)

**Implement:**

- Dependencies mirroring web: react, react-dom, tanstack query/virtual, zustand, lucide-react, plus `react-router-dom`. Dev: vite, plugin-react, typescript, tailwindcss ^3.4, postcss, autoprefixer, `@tauri-apps/cli`.
- Vite alias `"@"` → `../web/src` (shared files import `@/lib/...`). Alias `./navigation.next` → `./src/navigation.router.tsx` (file may be a stub until D1.03b).
- `server.fs.allow` includes `../web`. Port **1420**, `strictPort: true`.
- Tailwind content includes `../web/src/**/*.{ts,tsx}` and the **same** theme tokens as `apps/web/tailwind.config.ts` (import shared object; do not duplicate hex).
- `src/styles.css`: `@import "../../web/src/app/globals.css";` — do not fork CSS.

**Tests:** `npm --prefix apps/desktop run build` succeeds with non-trivial CSS; `npm run typecheck:desktop`; `npm run verify` still does not require Rust.

**Commit:** `desktop: add Vite build with shared aliases and Tailwind`

### D1.03b — Desktop router reusing shared page components

**Depends on:** D1.03a, D1.02a  
**Files:**

- Create: `apps/desktop/src/router.tsx`, `navigation.router.tsx`, `App.tsx`
- Modify: `apps/desktop/src/main.tsx`

**Implement:** React Router implements the D1.01 contract (`href` → `to`, drop `prefetch`). Routes match `apps/web/src/app` exactly plus a catch-all to home. Same providers as `Providers.tsx`. Call `applyShellDataset()`. Leave `"use client"` directives in shared files.

**Tests:** `npm run typecheck:desktop` and desktop build; `npm run test:web` unaffected.

**Commit:** `desktop: add router reusing web page components`

### D1.04 — Sidecar lifecycle in Rust

**Depends on:** D0.07, D1.03b  
**Files:** `apps/desktop/src-tauri/src/` (`sidecar.rs`, `lib.rs`)

**Implement:**

- Allocate port in Rust (`TcpListener::bind("127.0.0.1:0")`, read addr, drop listener, pass `--port <n>`). Never pass `--port 0` in the shipped path.
- Always pass `--data-dir`. Env `FRAMEPILOT_DESKTOP=1`.
- Inject both globals before frontend load: `__FRAMEPILOT_API_BASE__` and `__FRAMEPILOT_DESKTOP__ = true`.
- Parse stdout ready line; fail fast if reported port differs.
- Crash policy: one automatic restart; if health fails twice, blocking error page.
- Shutdown: SIGTERM, wait 5s, then kill. Windows: job object or `GenerateConsoleCtrlEvent` — document which in feasibility notes.
- Log sidecar stderr to `{data_dir}/logs/sidecar.log`.

**Tests:** Rust unit tests for `allocate_loopback_port()` and `parse_ready_line()`. Run: `cargo test` in `src-tauri`, `npm run verify`. Mark GUI-only `[~]` if needed.

**Commit:** `desktop: manage sidecar lifecycle and API base injection`

### D1.05 — App-support data directory

**Depends on:** D1.04  
**Files:** Rust path helper only (do not duplicate in TS)

**Implement:** Default dirs as locked decision 8. Create on first launch. Packaged runs never use repo `.framepilot-data`. Dev may use `.framepilot-desktop-dev` (gitignored in D0.07a).

**Tests:** table-driven Rust tests for macOS/Windows/Linux prefixes. Run: `cargo test`.

**Commit:** `desktop: use OS app-support data directory`

### D1.06 — Window basics and single instance

**Depends on:** D1.04  
**Files:** `tauri.conf.json`, Rust setup

**Implement:** Title `FramePilot`; min size ~1100×720; remember position/size; single instance focuses the first window; close window stops sidecar.

**Tests:** none (shell). Run: `cargo check`. Record GUI or `[~]`.

**Commit:** `desktop: add window state and single-instance lock`

### D1.07 — Dev scripts and verify wiring

**Depends on:** D1.03a, D1.04  
**Files:** root `package.json`, `apps/desktop/package.json`, short README section

**Implement:** `npm run dev:desktop` → tauri dev + Vite + sidecar. `build:desktop` may wait until Phase 4. `verify` must **not** require Rust. `install:all` already installs desktop from D1.03a.

**Tests:** none (scripts). Run: `npm run verify`.

**Commit:** `desktop: add tauri dev scripts`

### D1.08 — Desktop smoke: health + project list

**Depends on:** D1.04, D1.05, D1.07  
**Files:** `tests/desktop/smoke.sh` or Playwright against Vite `:1420`

**Acceptance:** UI (or the Vite page) can call `GET /api/projects` and render the home list (empty is OK). Failure must be visible, not a silent CORS 403. On WSL, HTTP-level smoke against the sidecar + Vite is enough for `[x]` of the non-GUI part; WebView render stays `[~]` if needed — split the tracker note accordingly, do not leave the whole id `[ ]`.

**Tests:** script asserts `/health` and `/api/projects` 200 from the injected base. Run: `npm run test:desktop:smoke` (skip with explicit message only for the WebView half).

**Commit:** `test: add desktop project-list smoke`

### D1.09 — Graceful quit while a job is running

**Depends on:** D1.04, D1.06  
**Files:**

- Modify: sidecar/window close handler; reuse existing cancel route
- Test: `apps/api/tests/test_job_reliability.py`; Rust shutdown state machine
- Docs: `docs/v2_known_limitations.md` if any remaining gap

**Implement:** On close, if an import/process job is active: confirm — Cancel quit / Quit and cancel job / Quit anyway. Cancel: existing POST cancel, wait up to 10s, then SIGTERM. Quit anyway: SIGTERM then kill after 5s. Next launch: existing startup sweep; UI must show the recovery message (`importLoadRecoveryMessage`), not a bare “failed”.

**Tests:** cancelled-then-restarted import leaves no photo in `processing`; job terminal `cancelled` not `failed`; killed worker still retryable; Rust state machine returns Kill after grace window.

**Commit:** `desktop: cancel or drain jobs before quitting`

**Phase 1 acceptance** (ticked `上线` 2026-08-19; Phase 2 not started):

- [x] Home UI or HTTP smoke lists projects — `GET /api/projects` `[]` from `test:desktop:smoke`, live sidecar, desktop sidecar `:54451`, and browser API `:8000`
- [x] Sidecar health OK — `GET /health` `{"status":"ok","version":"2.0.0-rc2","service":"framepilot-api"}`
- [x] `npm run verify` green without Tauri — exit 0; fail-if-invoked `rustc`/`cargo`/`tauri` wrappers were not called by verify
- [x] Browser `npm run dev` still works on :3000/:8000 — 2026-08-19T18:59:32+08:00 `npm run dev`: `:8000/health` 200, `:8000/api/projects` `[]`, `:3000/` 200 title `FramePilot`

---

## Phase 2 — Native Filesystem and Core Workflow (about 1.5–2 weeks)

**Phase goal:** Import → Process → Cull → Export works using native folder pickers. Originals stay immutable.

### D2.00 — Registered project roots for desktop folder pickers

**Depends on:** D0.03  
**Files:**

- Create: `apps/api/app/core/project_roots.py`
- Modify: `apps/api/app/services/projects.py` (allowed roots), `apps/api/app/api/routes.py`
- Docs: `docs/api.md` (`root_path` currently omits the allowlist)
- Test: `apps/api/tests/test_desktop_project_roots.py`

**Implement:**

- Problem: allowlist is read once via `lru_cache`; the user picks a folder **after** spawn. Setting `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST=$HOME` voids the control.
- Process-level registry **not** inside `Settings` (mutating settings resets the DB engine). Persist `{data_dir}/desktop_project_roots.json`, cap 50.
- `register_root`: absolute, exists, directory, resolved; reject `BLOCKED_ROOT_NAMES`, filesystem anchors, data dir and its parents.
- `create_project` allowed roots = `[projects_root, *allowlist, *registered_roots()]`. Do not change error messages.
- Endpoints **only when `FRAMEPILOT_DESKTOP=1`** (else 404): `POST /api/desktop/project-roots` `{"path"}`, `GET` same.
- Desktop flow: pick → POST register → POST `/api/projects` with `root_path`.

**Tests:** existing allowlist test still passes unchanged; outside root 422 until registered; `/`, `/etc`, `C:\Windows`, data dir 422; relative/file 422; endpoints 404 when desktop env unset; roots survive `create_app()` restart; `clear_registered_roots()` in fixtures.

**Commit:** `api: register desktop project roots before use`

### D2.01 — Desktop capability: pick files and directories

**Depends on:** Phase 1  
**Files:** `apps/desktop/src/lib/nativeFs.ts`, Tauri dialog plugin, capabilities JSON

**Implement:** `pickDirectory()`, `pickImageFiles()`, `revealInFileManager()`. Web builds must not import Tauri plugins. `getNativeFs()` returns `null` in the browser.

**Tests:** unit-test the null-browser branch; desktop wrappers mocked.

**Commit:** `desktop: add native file dialog adapters`

### D2.02 — Project create/open with native directory picker

**Depends on:** D2.00, D2.01  
**Files:** `ProjectCreator.tsx`, `apps/web/src/lib/api.ts`, `apps/web/src/lib/projectCreation.ts`

**Implement:** If native FS exists, Browse fills `root_path` after `POST /api/desktop/project-roots`. Surface 422 verbatim. Extend `createProject` with `acknowledgeNonempty`. Confirm: “This folder already contains files. FramePilot will create its project folders inside it and will not modify existing files. Continue?” Browser: text field stays; no acknowledge flag unless confirmed.

**Tests:** `projectCreation.test.ts` — `acknowledgeNonempty` only after confirmation. API: registered nonempty root fails without the flag and succeeds with it; existing files still present.

**Commit:** `web: use native directory picker when desktop APIs exist`

### D2.03 — Import panel uses path import on desktop

**Depends on:** D0.04b, D2.01  
**Files:** `ImportPanel.tsx`, `apps/web/src/lib/api.ts`, `apps/web/src/lib/importWorkflow.ts`

**Implement:**

- Desktop: pick folder/files → `importPhotosFromPaths`, loop `remaining_paths` with same `job_id`, `finalize: true` only on last slice. Progress uses `expanded_total`.
- Browser: existing multipart.
- **Invariant:** when `isDesktopShell()` is false, both `<input type="file">` elements (`ImportPanel.tsx` ~234 and ~253 including `webkitdirectory`) keep current DOM position, labels, and disabled semantics. `tests/e2e/local-workflow.spec.ts` depends on them.

**Tests:** `importWorkflow.test.ts` branch + remaining-paths loop. Run `npm run test:e2e` before closing Phase 2.

**Commit:** `web: import from local paths in desktop mode`

### D2.04 — Drag-and-drop folders/files onto import view

**Depends on:** D2.03  
**Files:** `ImportPanel.tsx`; Tauri drag-drop if WebView drop is insufficient

**Implement:** Dropped paths feed `from-paths`. Overlay `pointer-events: none` unless a drag is active (must not block Playwright file inputs). Do not start import on drop outside the import page.

**Tests:** `collectDroppedPaths(event)` unit test. Run `npm run test:web` and note E2E in Phase 2 close.

**Commit:** `desktop: add import drag-and-drop`

### D2.05 — Reveal project, originals, and export folders

**Depends on:** D2.01  
**Files:** `ProjectDashboard.tsx`, `ExportPanel.tsx`

**Implement:** “Open project folder”, “Open export folder” via `revealInFileManager`. Folder export already returns `output_path`.

**Tests:** one helper test that the reveal callback is invoked with `output_path`. Run: `npm run test:web`.

**Commit:** `desktop: reveal project and export paths in the OS file manager`

### D2.06 — Recent projects (desktop)

**Depends on:** D1.05  
**Files:** helper + `ProjectList.tsx`

**Implement:** last-opened project id in localStorage. Do not invent a second database. `GET /api/projects` remains the list.

**Tests:** `recentProjects.test.ts` (or `.test.tsx`). Run: `npm run test:web`.

**Commit:** `desktop: remember last opened project`

### D2.07 — Cross-platform path hardening

**Depends on:** D0.04a  
**Files:** `importing.py`, `projects.py`, tests

**Implement / test:** Windows drive letters, spaces, non-ASCII, trailing separators, reject NUL; keep `os.pathsep` allowlist parsing. Skip live Win32-only cases on POSIX.

**Commit:** `api: harden desktop import paths`

### D2.08 — Full workflow verification

**Depends on:** D2.03, D2.05  
**Files:** `tests/desktop/workflow.md` + pytest using `from-paths` then process + export

**Automated:** create project, import synthetic JPEGs via from-paths, process, mark Pick, CSV/ZIP/folder export, originals unchanged.

**Manual checklist** when GUI exists: pick folder, cull with keyboard, export, reveal folder.

**Tests:** the pytest above. Run: `npm run test:api` and `npm run test:e2e` if ImportPanel changed.

**Commit:** `test: cover path-import process export workflow`

### D2.09 — Reveal exports instead of downloading them on desktop

**Depends on:** D2.01, D2.05  
**Files:** `ExportPanel.tsx` (`<a download>` around lines 241 and 308); `ImportExportPanels.test.tsx`

**Implement:** On desktop, replace download anchors with “Show in folder” using `output_path`. Browser keeps anchors. Branch on `isDesktopShell()`. If macOS WKWebView blocks loopback HTTP images, record it — do not redesign the asset pipeline here.

**Tests:** with `__FRAMEPILOT_DESKTOP__ = true`, reveal button and no `<a download>`; flag unset → current href.

**Commit:** `desktop: reveal export artifacts instead of downloading them`

**Phase 2 acceptance:**

- [x] Desktop (or API-equivalent) completes Import → Process → Cull → Export — API pytest `test_path_import_process_pick_and_export_leaves_originals_unchanged` plus browser e2e smoke (`npm run test:e2e`, 45 passed, 2026-08-21T08:36:30+08:00)
- [x] Source files unmodified — D2.08 pytest asserts source `st_size` / `st_mtime_ns` / SHA-256 unchanged; `test_import_from_paths_immutability.py` green
- [x] Multipart browser import and E2E file inputs still work — `ImportExportPanels.test.tsx` `webkitdirectory` inputs; e2e `Choose image files` smoke
- [x] `npm run verify` green — rust-free wrappers, exit 0, 2026-08-21T08:36:30+08:00

---

## Phase 3 — Desktop UI and Native Chrome (about 2 weeks)

**Phase goal:** Feel like a desktop product. Do not rewrite the culling workspace. Detached preview / concurrency knobs / updater are **out of 2.1**.

### D3.01 — Native menu bar

**Depends on:** Phase 2  
**Files:** Rust menu, JS listeners as needed

Menus: File (New, Open data folder, Import, Export, Close, Quit); Edit (OS defaults); View (Fullscreen); Project (Process, Culling); Help (Shortcuts, About dialog only — no updater).

Preserve P/M/X/U/1–5/0/Space/Z/C/G/F/E. **No native menu item may use a bare-key accelerator** for those keys.

**Tests:** `menuRoutes.test.ts` if a pure map is extracted; `reviewShortcutCommandFromEvent` still returns null for modifier chords (`reviewShortcuts.ts`). Run: `npm run test:web`. GUI recorded or `[~]`.

**Commit:** `desktop: add native application menu`

### D3.02 — Status bar and processing visibility

**Depends on:** D3.01, D1.02a  
**Files:** desktop-only status bar or `Shell.tsx` gated by `isDesktopShell()`

Show sidecar connected, project name, job step/percent. Reuse `processingProgress.ts`. Keep browser shell unchanged if possible.

**Tests:** helper/render test when `isDesktopShell()` is true. Run: `npm run test:web`.

**Commit:** `desktop: add status bar for sidecar and jobs`

### D3.03 — Settings: data directory display

**Depends on:** D1.05  
**Files:** `SettingsPanel.tsx`; new `GET /api/meta` (do **not** extend `/health`)

**Implement:** `GET /api/meta` → `{version, service, data_dir, desktop_mode}`. Settings: read-only data directory + “Open data folder” on desktop. Changing data dir is out of 2.1.

**Tests:** `/api/meta` returns monkeypatched `FRAMEPILOT_DATA_DIR`; `desktop_mode` follows env. Component shows the value.

**Commit:** `desktop: show data directory in settings`

### D3.04 — System theme follow (light/dark)

**Depends on:** D3.02  
**Files:** CSS / Tailwind `dark:` scoped to `[data-shell="desktop"]`

Browser may stay light-only.

**Tests:** none (CSS) plus visual note. Run: `npm run test:web` if components changed.

**Commit:** `desktop: follow system light/dark theme`

### D3.05 — Window chrome and empty/error copy

**Depends on:** D3.02  
**Files:** empty states on list, import, culling, export

Desktop copy: “Choose a folder”, not “Choose files in your browser”. Keep Help shortcuts accurate.

**Tests:** string/helper tests if copy is centralized. Run: `npm run test:web`.

**Commit:** `desktop: adapt empty and error copy for native folders`

### D3.06 — Optional tray (defer if timeboxed)

**Depends on:** D3.02  
**Skip unless Phase 3 is ahead of schedule.** Not required for DoD. If skipped: `[-]` and D5.05 note.

**Tests:** none if deferred (`docs` commit). If implemented: smoke that tray menu has Show + Quit.

**Commit:** `desktop: add optional tray status` **or** `docs: defer desktop tray to a later release`

### D3.07 — Keyboard vs native menu conflict pass

**Depends on:** D3.01  
**Files:** `CullingWorkspace.tsx` keydown, menu accelerators, Help page

Do not steal P/M/X. Document accelerators on Help.

**Tests:** `reviewShortcutCommandFromEvent` still ignores modifier chords. Run: `npm run test:web`.

**Commit:** `desktop: reconcile shortcuts with native menus`

**Phase 3 acceptance:**

- [ ] Menu actions reach real routes
- [ ] Keyboard culling still matches Help
- [ ] Settings shows data dir
- [ ] Desktop import does not require a browser file input
- [ ] `npm run verify` green

---

## Phase 4 — Installers, CI, Signing Prep (about 1–1.5 weeks)

**Phase goal:** Unsigned (then optionally signed) Windows NSIS and macOS DMG from CI.

### D4.01 — Bundle sidecar into Tauri resources

**Depends on:** D0.05, Phase 1  
**Files:** `tauri.conf.json` `externalBin` / `resources`, `packaging/scripts/stage-sidecar.sh`

Dev uses venv; release uses PyInstaller output.

**Tests:** none (build config). Run: `npm run verify`. Record GUI or `[~]`.

**Commit:** `desktop: bundle PyInstaller sidecar in Tauri resources`

### D4.02 — Windows NSIS and macOS DMG config

**Depends on:** D4.01  
**Files:** `tauri.conf.json`

App name `FramePilot`; bundle id `com.framepilot.app`.

**Tests:** none (bundle config). Run: `cargo check`.

**Commit:** `desktop: configure NSIS and DMG bundle targets`

### D4.03 — MOVED

Moved to **D0.00**. Do not implement twice. If `.github/workflows/verify.yml` exists, this id is done (`[-]` in §5.1).

**Depends on:** n/a  
**Files:** none  
**Implement:** no-op  
**Tests:** none  
**Commit:** none

### D4.04 — GitHub Actions desktop matrix

**Depends on:** D4.01, D4.02, D0.00  
**Files:** `.github/workflows/desktop.yml`

Matrix: `windows-latest`, `macos-latest` (optional `ubuntu-latest` sidecar-only). Build sidecar, `tauri build`, upload installer artifacts only. Unsigned until certs exist. Never upload photos.

**Tests:** none (CI). After merge, confirm artifacts exist.

**Commit:** `ci: build Windows and macOS desktop artifacts`

### D4.05 — Signing and notarization documentation

**Depends on:** D4.04  
**Files:** `docs/desktop_signing.md`

Unsigned builds OK for internal testers with a README warning. Do not fail first RC on missing certs.

**Tests:** none (documentation).

**Commit:** `docs: add desktop code signing runbook`

### D4.06 — Size pass

**Depends on:** D4.01  
**Files:** feasibility notes

If unpacked sidecar + app **> 400 MB**, document scipy/imagehash cost. Do not strip Pillow codecs.

**Tests:** none (documentation).

**Commit:** `docs: record desktop installer size budget`

**Phase 4 acceptance:**

- [ ] CI verify green on PRs (D0.00)
- [ ] CI produces Windows installer + macOS DMG (unsigned OK)
- [ ] Signing documented
- [ ] `check:artifacts` still rejects committing binaries; icons exception remains narrow

---

## Phase 5 — Test, Docs, Stabilize (about 1 week)

**Phase goal:** Meet product plan §2.2 Definition of Done for `2.1.0-desktop`.

### D5.01 — Desktop test matrix document + commands

**Depends on:** Phase 4  
**Files:** `docs/desktop_testing.md`, package.json scripts

Matrix: start/quit/sidecar crash/port in use; path import 100 synthetic JPEGs; optional 500/2000 via `perf:api`; install/uninstall checklist; origin/CORS notes (LAN access impossible because loopback-only).

**Tests:** none (documentation) unless a new script is added, then run that script.

**Commit:** `docs: add desktop test matrix`

### D5.02 — README and user docs

**Depends on:** D5.01  
**Files:** `README.md`, `docs/desktop_user_guide.md`, `docs/v2_known_limitations.md`, `docs/v2_architecture.md` (desktop no longer deferred once shipped)

Cover: install, first launch, data location, copies not moves, reveal export folders, how to keep using the web app for development.

**Tests:** none (documentation). Run: `npm run verify` if README scripts changed.

**Commit:** `docs: add desktop install and data-dir instructions`

### D5.03 — Performance notes on desktop WebView

**Depends on:** D2.08  
**Files:** feasibility notes or `docs/v2_performance_baseline.md`

One 100-photo path-import + process RSS for sidecar and UI if GUI exists; otherwise sidecar-only and mark UI pending.

**Tests:** none (documentation).

**Commit:** `docs: record desktop performance notes`

### D5.04 — Version bump to 2.1.0-desktop (release candidate)

**Depends on:** Phases 0–4 acceptance boxes  
**Files:** `apps/api/app/core/version.py`, `pyproject.toml`, both `package.json`, FastAPI already reads `APP_VERSION`, changelog

Do not tag until `npm run verify` and desktop CI artifacts exist. Do not scatter version literals.

**Tests:** health still returns `APP_VERSION`. Run: `npm run test:api` `npm run verify`.

**Commit:** `release: 2.1.0-desktop rc`

### D5.05 — Known limitations for desktop 2.1

**Depends on:** D5.02  
**Files:** `docs/v2_known_limitations.md`

List: jobs not durable across sidecar kill; HEIC/RAW skipped; auto-update deferred; unsigned until certs; WSL may not run GUI; copy mode only; no detached preview; no concurrency knobs; tray deferred unless D3.06 shipped.

**Tests:** none (documentation).

**Commit:** `docs: document desktop 2.1 known limitations`

**Phase 5 / product DoD:**

- [ ] Windows and macOS installers exist (CI artifacts)
- [ ] App start manages Python sidecar without the user running uvicorn
- [ ] Native folder picker and drag-drop import
- [ ] Core workflow matches v2: import, process, keyboard cull, CSV/ZIP/folder export
- [ ] Originals never modified
- [ ] 500-photo API-level path import does not crash; 500 GUI documented if measured
- [ ] User + developer docs exist
- [ ] CI builds both platform installers; signing may still be pending
- [ ] Loopback bind + Host/Origin checks in place
- [ ] Custom project roots only via D2.00 registration

---

## 6. What Not To Do In This Track

- Do not implement HEIC, RAW, XMP, or local neural models.
- Do not add a cloud updater.
- Do not replace SQLite or move scoring into Rust.
- Do not delete the Next.js app or break Playwright.
- Do not switch to Electron unless D0.09 writes that Tauri failed.
- Do not listen on `0.0.0.0`.
- Do not use multipart upload as the desktop primary import for large batches.
- Do not set `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` to `$HOME`, `/`, or a drive root.
- Do not widen the artifact-check script beyond D0.07a.
- Do not add version literals outside `apps/api/app/core/version.py`.

---

## 7. Suggested Commit Cadence

One task id = one commit (D1.01 may stack 2–3). Do not batch a whole phase.

---

## 8. Stop Conditions

Stop and summarize if:

- All Phase 5 DoD boxes are checked, or
- D0.09 requires a product decision and notes are committed, or
- Missing OS / signing / WebView makes GUI work impossible and remaining work is docs/CI-only, or
- Tests cannot be made green after focused debugging, or
- Session budget hit (5 tasks or one phase).

Final summary: branch, commits, completed task ids, checks run, remaining ids, risks, next Goal prompt.

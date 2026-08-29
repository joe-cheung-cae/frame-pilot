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

- [~] D3.01 原生菜单栏 — `npm run test:web` 于 2026-08-23 通过；GUI/`cargo test` 未验证（`rustc` 1.85 无法编译当前 Tauri lockfile）。见 `docs/desktop_feasibility_notes.zh.md`。
- [~] D3.02 状态栏 — `npm run test:web` 于 2026-08-26 通过；GUI/`cargo test` 未验证（与 D3.01 相同的 rustc 1.85 阻碍）。见 `docs/desktop_feasibility_notes.zh.md`。
- [~] D3.03 设置中的数据目录（`GET /api/meta`） — API + Settings 测试已在 `main`；GUI/`cargo test` 未验证（与 D3.01 相同阻碍）。见 `docs/desktop_feasibility_notes.zh.md`。
- [x] D3.04 跟随系统主题 — CSS `[x]`。视觉 GUI `[~]` 2026-08-28（与 D3.01 相同的 rustc/cargo 阻碍）。见 `docs/desktop_feasibility_notes.zh.md`。
- [x] D3.05 空状态与错误文案
- [-] D3.06 可选托盘 — 已推迟 2026-08-28T17:24:26+08:00。不是 DoD 要求。D5.05 将记录此次推迟。未添加 `fs:` 或 `shell:` capabilities。
- [x] D3.07 快捷键与菜单加速键核对 — Help 记录 CmdOrCtrl+N/W/Q；`menu.rs` 无裸 culling 加速键；`reviewShortcutCommandFromEvent` 忽略修饰键组合（`npm run test:web` 2026-08-28）。

Phase 4

- [x] D4.01 把 sidecar 打进 Tauri resources
- [x] D4.02 NSIS 与 DMG 配置
- [-] D4.03 已迁移到 D0.00
- [x] D4.04 桌面 CI 矩阵
- [x] D4.05 签名手册
- [x] D4.06 体积核对

Phase 5

- [x] D5.01 桌面测试矩阵 — `docs/desktop_testing.md`（+ zh）；文档化现有脚本；无新别名（2026-08-29）
- [x] D5.02 README 与用户文档 — `docs/desktop_user_guide.md`（+ zh）；README + 架构 + 桌面 README 更新（2026-08-29）
- [x] D5.03 桌面性能说明 — multipart `perf:api` RSS 120.24 MB（#96）**以及** `from-paths` RSS 119.77 MB（#97）于 WSL2；UI pending（2026-08-29）
- [x] D5.04 版本升到 2.1.0-desktop — `APP_VERSION`/`package.json`/`Tauri` = `2.1.0-desktop`；`pyproject.toml` = `2.1.0+desktop`（PEP 440）；双语 CHANGELOG；未打 git tag（2026-08-29）
- [x] D5.05 已知限制 — `docs/v2_known_limitations.md`（+ zh）Desktop 2.1 节；记录 D3.06 托盘延期（2026-08-29）

---

## Phase 0 — 可行性与桌面关键 API（约 3–5 天）

**阶段目标：** 证明 sidecar 可以打包并托管；落地桌面壳离不开的 API。

**阶段退出：** 按锁定决策 13，§5.1 的 Phase 0 框为 `[x]` 或 `[~]`。`docs/desktop_feasibility_notes.md` 记录基线与 go/no-go。

### D0.00 — CI verify 工作流（web/api，无 GUI）

**Depends on:** none — 先实现本任务  
**Files:**

- Create: `.github/workflows/verify.yml`

**Implement:**

- 触发器：`pull_request`，以及对 `main` 和 `feature/desktop-packaging` 的 `push`。
- `ubuntu-latest` 上单个 job：checkout、Python 3.11、Node 22。
- 步骤：`npm run install:all`，然后 `npm run verify`。
- 不要安装 Rust。这里不要跑 Playwright。
- 每个 ref 一个 concurrency group，且 `cancel-in-progress: true`。

**Tests:** none（CI 配置）。提交前本地运行：`npm run verify`

**Commit:** `ci: run npm verify on pull requests`

### D0.01 — Sidecar CLI 启动器

**Depends on:** none  
**Files:**

- Create: `apps/api/app/sidecar_main.py`
- Create: `docs/desktop_feasibility_notes.md`（stub：Blockers + Baselines）
- Modify: `apps/api/pyproject.toml`（`[project.scripts] framepilot-api = "app.sidecar_main:main"`）
- Test: `apps/api/tests/test_sidecar_cli.py`

**Implement:**

- argparse：`--host`（默认 `127.0.0.1`），`--port`（默认 `8000`，`0` = 临时端口），`--data-dir`（**必填**），`--log-level`（默认 `info`）。
- 若 `--host` 不是 `127.0.0.1` 或 `localhost`，退出码 2。
- 若 `--data-dir` 缺失或不是绝对路径，退出码 2。永不回退到相对 CWD 的 `.framepilot-data`。
- 在第一次 `import app.main` **之前**设置 `os.environ["FRAMEPILOT_DATA_DIR"]`。`app.main` 在 import 时构建应用（`main.py:76`），因此 import 必须发生在 `main()` 内、argparse 之后。
- 端口发现：自己 bind 一个 `socket`，读 `getsockname()[1]`，打印 ready 行，然后 `uvicorn.Server(config).run(sockets=[sock])`。POSIX 上设置 `SO_REUSEADDR`；Windows 上不要设置（端口劫持）。
- bind 之后、serve 之前恰好打印一行 stdout，`flush=True`：`FRAMEPILOT_API ready host=127.0.0.1 port=<actual> data_dir=<path>`。`<actual>` 来自 `getsockname()`，永不来自解析后的参数。
- 把 FastAPI **对象**传给 uvicorn，而不是字符串 `"app.main:app"`。
- 所有日志走 stderr。stdout 上不要再打印任何别的内容。

**Tests (write first):**

- `parse_args` 拒绝 `--host 0.0.0.0` 和 `--host 192.168.1.5`（退出码 2）。
- `parse_args` 拒绝缺失或相对的 `--data-dir`。
- `bind_listen_socket("127.0.0.1", 0)` 返回端口非零、地址为 `127.0.0.1` 的套接字；测试中关闭它。
- `ready_line(...)` 渲染出精确期望字符串。
- `--data-dir` 在 settings 加载之前生效。
- `--help` 退出码 0。
- 不要启动真实服务器；monkeypatch `uvicorn.Server.run`。

**Commit:** `api: add localhost-only sidecar CLI`

### D0.02 — 供桌面探测的 health 负载

**Depends on:** D0.01  
**Files:**

- Create: `apps/api/app/core/version.py`（`APP_VERSION = "2.0.0-rc2"`）
- Modify: `apps/api/app/main.py`（`FastAPI(version=APP_VERSION)`，`/health`）
- Modify: `apps/api/app/api/routes.py`（`/api/health`）
- Modify: `docs/api.md`
- Test: `apps/api/tests/test_projects_api.py`（断言当前在第 19 行为 `== {"status": "ok"}`）

**Implement:** `/health` 与 `/api/health` 都返回：

```json
{ "status": "ok", "version": "2.0.0-rc2", "service": "framepilot-api" }
```

`version` 是 `APP_VERSION`。不要在 `main.py`、`routes.py` 或测试中再写额外的版本字面量。保持 `status` 为 `"ok"`（`playwright.config.ts:23`）。

**Tests:**

- `test_api_health_returns_ok` 断言 `status`、`service`，以及 `version == APP_VERSION`。
- 无前缀的 `/health` 同样如此。
- `create_app().version == APP_VERSION`。

**Commit:** `api: extend health payload with version`

### D0.03 — 桌面 Origin 与 Host 策略，且不削弱本地 Web

**Depends on:** none（可与 D0.01 并行）  
**Files:**

- Create: `apps/api/app/core/origins.py`
- Modify: `apps/api/app/main.py`（allowlist、CORS、写请求守卫）
- Test: `apps/api/tests/test_desktop_origins.py`

**Implement:**

- `allowed_origins()`：始终包含当前四个 web origin（3000 与 3100）。当 `FRAMEPILOT_DESKTOP=1` 时，再加上 `http://localhost:1420`、`http://127.0.0.1:1420`、`http://tauri.localhost`、`https://tauri.localhost`、`tauri://localhost`。
- 在 **`create_app()` 内部**计算该集合。同时喂给 `CORSMiddleware` 和写请求 origin 守卫。`allow_credentials=True` 保留；禁止通配符。
- 对**所有**方法做 Host 检查：hostname 不是 `127.0.0.1`、`localhost`、`::1` 或 `tauri.localhost` 则 403。缺失 Host 则拒绝。这关闭针对 GET `/api/projects`、`/api/assets/...` 和导出下载的 DNS rebinding。
- 不要全局关闭 origin 守卫。

**Tests:**

- POST `/api/projects` Origin `http://localhost:3000` → 201。
- POST Origin `https://evil.example` → 403，detail 与现有一致。
- POST Origin `tauri://localhost` → 除非 `FRAMEPILOT_DESKTOP=1`，否则 403。
- **没有** Origin 的 POST → 201（Host 检查使这是安全的）。
- GET `/api/projects` `Host: attacker.example` → 403；`Host: 127.0.0.1:8000` → 200。
- 桌面模式下针对 `tauri://localhost` 的 CORS preflight。

**Commit:** `api: allow Tauri origins and reject non-loopback hosts in desktop mode`

### D0.04a — 导入路径展开辅助函数（纯逻辑，无 HTTP）

**Depends on:** none  
**Files:**

- Modify: `apps/api/app/services/importing.py`
- Test: `apps/api/tests/test_import_path_expansion.py`

**Implement:** 紧挨 `IMPORT_MAX_FILES_PER_REQUEST` 添加：

```python
PATH_IMPORT_MAX_INPUT_ENTRIES = 5000
PATH_IMPORT_MAX_EXPANDED_FILES = 20000
```

`expand_import_paths(paths, project_root) -> ExpandedImportPaths`，带 `files` 与 `skipped`。

规则：

- 空列表、输入条目过多、任何非绝对路径、路径缺失或展开超过上限时抛 `ValueError`。
- 目录：`os.walk(followlinks=False)`；丢弃 `resolve()` 不在被 walk 根之下的条目。
- 仅普通文件（`stat.S_ISREG`）。跳过 FIFO/设备（`mkfifo photo.jpg` 会让 `_copy_file_to_path` 永久阻塞）。
- 扩展名过滤复用现有 supported/unsupported 辅助函数（HEIC/RAW 跳过原因与上传一致）。
- 跳过 `project_root.resolve()` 之下的源（`"Source is inside the project folder"`）。
- 按解析后的路径去重；排序以保证确定性。

**Tests:** 嵌套 JPEG + txt + heic；相对 / 缺失 / 空错误；不跟随指向外部的 symlink（POSIX）；跳过 FIFO（POSIX）；项目 originals 内的文件被跳过；确定性顺序。

**Commit:** `api: add import path expansion helper`

### D0.04b — 基于路径的导入端点

**Depends on:** D0.04a  
**Files:**

- Modify: `apps/api/app/schemas/api.py`，`apps/api/app/api/routes.py`
- Test: `apps/api/tests/test_import_from_paths.py`
- Docs: `docs/api.md`

**Implement:**

```
POST /api/projects/{project_id}/imports/from-paths
{"paths": ["/abs/folder", "/abs/file.jpg"], "job_id": null, "expected_total": null, "finalize": true}
```

- 展开；`ValueError` → 422。
- 最多消费 100 个展开后的文件。返回 `remaining_paths` + `expanded_total`。客户端用同一个 `job_id` 把剩余部分再 POST；仅在最后一片使用 `finalize: true`。
- 复用 multipart 控制流（进行中导入 409、stale-job、expected_total）。
- 每个文件：`source.open("rb")`，然后走现有 `register_import_file`。不要增加第二条复制路径。
- 按与 multipart 相同的 `finalize` 条件排队衍生任务。
- 当 finalize、只给了一个输入目录、且 `source_root_path` 为空时，把它记为只读元数据。不要再扫描。
- multipart 的 `ImportResult` 增加 `remaining_paths: []` 与 `expanded_total`，以便浏览器客户端保持兼容。

**Tests:** 两张 JPEG；250 个文件、三次请求、一个 job 的循环；相对 / 空 422；并发 409；目标位于 `originals/` 下；不支持的跳过原因；`docs/api.md` 记录该循环。

**Commit:** `api: add path-based local import`

### D0.04c — 路径导入的原图不可变

**Depends on:** D0.04b  
**Files:**

- Test: `apps/api/tests/test_import_from_paths_immutability.py`

**Implement:** 预期无需改生产代码。若测试失败，修服务，不要修测试。

**Tests:** 源文件 `st_size` / `st_mtime_ns` / SHA-256 不变；目录条目数不变；不是副本的硬链接（POSIX）；只读源目录仍可导入（POSIX，以 root 运行时跳过）；导入中途取消时源文件未被触碰。

**Commit:** `test: assert path import never mutates source files`

### D0.05 — PyInstaller spec 与 Linux sidecar smoke

**Depends on:** D0.01, D0.02  
**Files:**

- Create: `packaging/pyinstaller/framepilot-api.spec`、`packaging/pyinstaller/build.sh`、必要时 `packaging/pyinstaller/hooks/hook-app.py`
- Create: `scripts/sidecar-smoke.sh`（不是仓库根 `tests/desktop/` 下的 pytest 文件 — `npm run test:api` 只收集 `apps/api/tests`）
- Modify: 根 `package.json`（`packaging:sidecar`、`test:sidecar`）

**Implement:**

- 名为 `framepilot-api` 的 one-dir 构建。
- Hiddenimports：`app.main`、`app.sidecar_main`、`uvicorn.loops.auto`、`uvicorn.protocols.http.auto`、`uvicorn.protocols.websockets.auto`、`uvicorn.lifespan.on`、`uvicorn.lifespan.off`、`httptools`、`sqlalchemy.dialects.sqlite`、`PIL.JpegImagePlugin`、`PIL.PngImagePlugin`、`PIL.WebPImagePlugin`、`imagehash`、`numpy`，以及 imagehash 拉入的 scipy 子模块。
- 传递 FastAPI 对象，而不是 `"app.main:app"`。
- Windows：若没有 uvloop，文档说明 `--loop asyncio`。
- 启动后 `/health` 不是 OK 则 `build.sh` 必须失败。
- 不要提交 `dist/`（`dist/` 与 `build/` 已经在 gitignore 中）。

**Tests:** `bash scripts/sidecar-smoke.sh` — 临时 `--data-dir`、`--port 0`、解析 ready 行、curl `/health` 取 `version`、SIGTERM、5 秒内退出、无残留子进程。

**Commit:** `desktop: add PyInstaller sidecar spec and smoke`

### D0.06 — Next.js static export 试探（仅文档）

**Depends on:** none  
**Files:** `docs/desktop_feasibility_notes.md`

**Implement:** 在一次性改动中尝试 `output: 'export'`。记录 `next build` 是否成功、`projects/[projectId]` 路由会怎样、以及 `useSearchParams` 的 Suspense 警告。回滚任何会弄坏 `npm run test:web` 的 Next 配置。锁定的后续方案是 Vite SPA。

**Tests:** none（文档）。回滚后：若动过任何 Next 配置则运行 `npm run test:web`。

**Commit:** `docs: record Next static export spike`

### D0.07a — 有 Tauri 资源时仍保持 `npm run verify` 全绿

**Depends on:** D0.00  
**Files:**

- Modify: `scripts/check-release-artifacts.sh`、`.gitignore`
- Test: `scripts/test-release-checks.sh`

**Implement:**

- 在 blocked-pattern 匹配之后恰好增加一个例外：

```bash
allowed_pattern='^apps/desktop/src-tauri/icons/[^/]+\.(png|ico|icns)$'
```

- 不要放宽 `blocked_pattern`。不要增加任何其他例外。
- `.gitignore`：加入 `target/` 与 `.framepilot-desktop-dev/`。

**Tests:** 被跟踪的 `apps/desktop/src-tauri/icons/128x128.png` 通过；被跟踪的 `apps/desktop/other.png` 仍然失败。

**Commit:** `desktop: allow tauri icons in the release artifact check`

### D0.07 — 最小 Tauri 2 hello + 拉起 sidecar

**Depends on:** D0.01, D0.03, D0.05, D0.07a  
**Files:**

- Create: `apps/desktop/**` 骨架，加上 `apps/desktop/src-tauri/icons/`（32x32.png、128x128.png、128x128@2x.png、icon.icns、icon.ico）
- Modify: 根 `package.json`（`dev:desktop`）

**Implement:**

- Tauri 2 空白窗口。
- 拉起 sidecar（开发：经 sidecar CLI 的 venv uvicorn；生产稍后）并传入 `--host 127.0.0.1 --port <free> --data-dir <app-support>`。
- 设置 `FRAMEPILOT_DESKTOP=1`。
- 轮询 `/health`（15 秒超时）。显示 “API ready” 或错误。
- 退出时：SIGTERM，然后 5 秒后 kill。
- 锁定的 CSP（`app.security.csp`）：

```text
default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';
img-src 'self' data: blob: http://127.0.0.1:* http://localhost:*;
connect-src 'self' http://127.0.0.1:* http://localhost:* ipc: http://ipc.localhost;
font-src 'self' data:; object-src 'none'; frame-ancestors 'none'
```

`assetUrl` 返回用于 `<img src>` 的绝对地址 `http://127.0.0.1:PORT/...`（`ImportPanel.tsx`、`CullingWorkspace.tsx`）。缺少 `img-src` 看起来会像后端 bug。

若 WSL 无法打开 WebView：保留 Rust 拉起 / 健康检查代码，无 GUI 跑 sidecar smoke，标 `[~]`。

**Tests:** none（Rust/配置）。运行：`npm run verify`、`bash scripts/sidecar-smoke.sh`。把 WebView 结果或 WSL 错误记入可行性说明。

**Commit:** `desktop: add minimal Tauri shell with sidecar health`

### D0.08 — 测量基线

**Depends on:** D0.05, D0.07  
**Files:** `docs/desktop_feasibility_notes.md`

即使只有 Linux sidecar 也要记录：dist 体积、`/health` 之后的 RSS、到 `/health` 的时间、Tauri hello 的 RSS 或 “blocked on WSL”、scipy/pywavelets 是否存在。

**Tests:** none（文档）。

**Commit:** `docs: record desktop feasibility baselines`

### D0.09 — Go / no-go

**Depends on:** D0.06, D0.08  
**Files:** `docs/desktop_feasibility_notes.md`

写明：壳用 Tauri 2（仅当 Tauri 无法拉起 sidecar / WebView 无法到达回环时才用 Electron）。前端 Vite SPA。除非未打包 sidecar **>250 MB**，否则保留 imagehash/scipy。

**Tests:** none（文档）。运行：`npm run test:api`

**Phase 0 验收**（已于 2026-08-19 勾选 `上线`；GUI 仍为 `[~]`）：

- [x] Sidecar 启动、应答 `/health`、收到 SIGTERM 后退出
- [x] Origin + Host 策略拒绝随机站点与攻击者 Host 头
- [x] 基于路径的导入存在，按 100 分块，不修改源文件
- [x] 可行性说明已提交
- [x] `npm run test:api` 与 `npm run verify` 全绿
- [x] 浏览器 Web 应用仍可运行
- [~] GUI 壳为 `[x]` 或带有记录命令 / 错误的 `[~]` — 2026-08-19 `cargo --version` / `rustc --version`: command not found (exit 127)；见 `docs/desktop_feasibility_notes.md`

---

## Phase 1 — 桌面壳与 Sidecar 生命周期（约 1.5–2 周）

**阶段目标：** `npm run dev:desktop` 打开能通过 sidecar 列出项目的 FramePilot UI（或在 WSL 上以 Vite/HTTP 等价物标 `[~]`）。

### D1.01 — 导航适配层（保持 Next 可用）

**Depends on:** Phase 0 退出  
**Files:**

- Create: `apps/web/src/lib/navigation.ts`，`apps/web/src/lib/navigation.next.tsx`
- Modify（已 grep 核实）：`Shell.tsx`、`ProjectList.tsx`、`ProjectDashboard.tsx`、`ProcessingPanel.tsx`、`ImportPanel.tsx`、`ProjectCreator.tsx`、`CullingWorkspace.tsx`
- Modify mocks：`CullingWorkspace.test.tsx`、`ProcessingPanel.test.tsx`、`ImportExportPanels.test.tsx`
- Test: `apps/web/src/lib/navigation.test.tsx`（不是 `.test.ts` — node `--test` 没有 JSX；vitest 只收集 `*.test.tsx`）

**Implement:**

- 仅类型 + 再导出点。Web 构建中 `Link`、`useNavigator`、`useQueryParams` 来自 `./navigation.next`。
- 桌面 Vite 在 D1.03a 把该模块 alias 到 `apps/desktop/src/navigation.router.tsx`。一个再导出 `next/link` 的 barrel 会把 Next 拉进 Vite。
- `useQueryParams(): URLSearchParams` 隐藏 Next 与 React Router 的形态差异。`CullingWorkspace.tsx` 必须只消费该包装。
- 共享组件只 import `@/lib/navigation`。`apps/web/src/components/` 下不要有 `next/link` 或 `next/navigation`。
- 在同一次提交中把现有 mock 改指 `@/lib/navigation`。

**Tests:** Link 渲染 `<a href>`；`push` 以期望 href 被调用；`useQueryParams` 读到一个值；守卫组件不 import `next/link` 或 `next/navigation`；现有组件测试通过。运行：`npm run typecheck && npm run test:web`

允许拆分：(a) 适配层 + 测试，(b) Shell/list/dashboard/processing，(c) import/creator/culling + mocks。在 D1.03a 之前完成全部三块。

**Commit:** `web: isolate Next navigation behind an adapter`

### D1.02 — 运行时 API base（停止写死 :8000）

**Depends on:** D1.01  
**Files:**

- Create: `apps/web/src/lib/apiBase.ts`，`apps/web/src/types/globals.d.ts`
- Modify: `apps/web/src/lib/api.ts`（`API_BASE`、`request`、`exportDownloadUrl`、`assetUrl`）
- Test: `apps/web/src/lib/apiBase.test.ts`，`apps/web/src/lib/api.test.ts`

**Implement:**

- `resolveApiBase()`：`window.__FRAMEPILOT_API_BASE__`，然后 `NEXT_PUBLIC_API_BASE_URL`，然后 `http://127.0.0.1:8000`。`window` 未定义时安全（`next build`）。
- 继续导出 `API_BASE`，但在 `request` / URL 辅助函数内部**调用时**读取 `resolveApiBase()`。冻结的模块级常量看不到加载之后注入的端口。
- 去掉尾部斜杠。在 `globals.d.ts` 中声明 Window 扩展。

**Tests:** window 优先；env 其次；默认第三；去掉尾部斜杠；没有 window 时不抛；注入 base 后 `assetUrl` 与 `exportDownloadUrl` 使用该 host；现有编码断言在默认值下仍成立。

**Commit:** `web: resolve API base at runtime for desktop`

### D1.02a — `window.__FRAMEPILOT_DESKTOP__` 壳标志

**Depends on:** D1.02  
**Files:**

- Create: `apps/web/src/lib/shell.ts`
- Test: `apps/web/src/lib/shell.test.ts`（若需要 DOM 则加 `.test.tsx`）

**Implement:** `isDesktopShell()` 仅对字面量 `true` 为真。`applyShellDataset()` 设置 `document.documentElement.dataset.shell`。从桌面入口（D1.03b）和 `Providers.tsx`（浏览器 → `"browser"`）调用。D3.02/D3.04 消费该辅助函数 / `[data-shell="desktop"]`，不要内联 `window` 检查。

**Tests:** 仅 `true` 为真；undefined/`"1"`/`0` 为假；没有 window 时不抛。

**Commit:** `web: add desktop shell detection helper`

### D1.03a — 带共享别名与 Tailwind 的 Vite 桌面构建

**Depends on:** D1.01, D1.02  
**Files:**

- Create: `apps/desktop/package.json`、`index.html`、`vite.config.ts`、`tsconfig.json`、`tailwind.config.ts`、`postcss.config.js`、`src/main.tsx`、`src/styles.css`
- Modify: 根 `package.json`（`install:all`、`typecheck:desktop`、`lint:desktop`；把后两者加入 `verify`，**不要**要求 Rust）

**Implement:**

- 依赖镜像 web：react、react-dom、tanstack query/virtual、zustand、lucide-react，外加 `react-router-dom`。Dev：vite、plugin-react、typescript、tailwindcss ^3.4、postcss、autoprefixer、`@tauri-apps/cli`。
- Vite alias `"@"` → `../web/src`（共享文件 import `@/lib/...`）。Alias `./navigation.next` → `./src/navigation.router.tsx`（该文件在 D1.03b 之前可以是 stub）。
- `server.fs.allow` 包含 `../web`。端口 **1420**，`strictPort: true`。
- Tailwind content 包含 `../web/src/**/*.{ts,tsx}`，以及与 `apps/web/tailwind.config.ts` **相同**的主题 token（import 共享对象；不要复制 hex）。
- `src/styles.css`：`@import "../../web/src/app/globals.css";` — 不要分叉 CSS。

**Tests:** `npm --prefix apps/desktop run build` 成功且 CSS 非平凡；`npm run typecheck:desktop`；`npm run verify` 仍不要求 Rust。

**Commit:** `desktop: add Vite build with shared aliases and Tailwind`

### D1.03b — 复用共享页面组件的桌面路由器

**Depends on:** D1.03a, D1.02a  
**Files:**

- Create: `apps/desktop/src/router.tsx`、`navigation.router.tsx`、`App.tsx`
- Modify: `apps/desktop/src/main.tsx`

**Implement:** React Router 实现 D1.01 约定（`href` → `to`，去掉 `prefetch`）。路由精确匹配 `apps/web/src/app`，外加 catch-all 回首页。与 `Providers.tsx` 相同的 providers。调用 `applyShellDataset()`。共享文件中保留 `"use client"` 指令。

**Tests:** `npm run typecheck:desktop` 与桌面构建；`npm run test:web` 不受影响。

**Commit:** `desktop: add router reusing web page components`

### D1.04 — Rust 中的 sidecar 生命周期

**Depends on:** D0.07, D1.03b  
**Files:** `apps/desktop/src-tauri/src/`（`sidecar.rs`、`lib.rs`）

**Implement:**

- 在 Rust 中分配端口（`TcpListener::bind("127.0.0.1:0")`，读地址，丢掉 listener，传入 `--port <n>`）。发布路径上永不传 `--port 0`。
- 始终传入 `--data-dir`。环境变量 `FRAMEPILOT_DESKTOP=1`。
- 在前端加载前注入两个全局：`__FRAMEPILOT_API_BASE__` 与 `__FRAMEPILOT_DESKTOP__ = true`。
- 解析 stdout ready 行；报告端口不一致则快速失败。
- 崩溃策略：自动重启一次；若 health 失败两次，阻塞错误页。
- 关闭：SIGTERM，等待 5 秒，然后 kill。Windows：job object 或 `GenerateConsoleCtrlEvent` — 在可行性说明中记录用了哪一种。
- 把 sidecar stderr 记到 `{data_dir}/logs/sidecar.log`。

**Tests:** 针对 `allocate_loopback_port()` 与 `parse_ready_line()` 的 Rust 单元测试。运行：在 `src-tauri` 中 `cargo test`，以及 `npm run verify`。仅 GUI 部分必要时标 `[~]`。

**Commit:** `desktop: manage sidecar lifecycle and API base injection`

### D1.05 — 应用支持数据目录

**Depends on:** D1.04  
**Files:** 仅 Rust 路径辅助（不要在 TS 中复制）

**Implement:** 默认目录见锁定决策 8。首次启动时创建。打包运行永不使用仓库 `.framepilot-data`。开发可用 `.framepilot-desktop-dev`（D0.07a 已 gitignore）。

**Tests:** 针对 macOS/Windows/Linux 前缀的表驱动 Rust 测试。运行：`cargo test`。

**Commit:** `desktop: use OS app-support data directory`

### D1.06 — 窗口基础与单实例

**Depends on:** D1.04  
**Files:** `tauri.conf.json`、Rust setup

**Implement:** 标题 `FramePilot`；最小尺寸约 1100×720；记住位置/大小；单实例聚焦第一个窗口；关闭窗口停止 sidecar。

**Tests:** none（壳）。运行：`cargo check`。记录 GUI 或 `[~]`。

**Commit:** `desktop: add window state and single-instance lock`

### D1.07 — 开发脚本与 verify 接线

**Depends on:** D1.03a, D1.04  
**Files:** 根 `package.json`、`apps/desktop/package.json`、简短 README 小节

**Implement:** `npm run dev:desktop` → tauri dev + Vite + sidecar。`build:desktop` 可以等到 Phase 4。`verify` 必须**不**要求 Rust。`install:all` 已从 D1.03a 起安装 desktop。

**Tests:** none（脚本）。运行：`npm run verify`。

**Commit:** `desktop: add tauri dev scripts`

### D1.08 — 桌面 smoke：health + 项目列表

**Depends on:** D1.04, D1.05, D1.07  
**Files:** `tests/desktop/smoke.sh` 或针对 Vite `:1420` 的 Playwright

**Acceptance:** UI（或 Vite 页面）能调用 `GET /api/projects` 并渲染首页列表（空列表 OK）。失败必须可见，不能是静默 CORS 403。在 WSL 上，对 sidecar + Vite 的 HTTP 级 smoke 足以把非 GUI 部分标 `[x]`；若需要，WebView 渲染保持 `[~]` — 在跟踪表备注中拆开写，不要把整个 id 留成 `[ ]`。

**Tests:** 脚本断言注入的 base 上 `/health` 与 `/api/projects` 为 200。运行：`npm run test:desktop:smoke`（仅 WebView 一半可用明确消息跳过）。

**Commit:** `test: add desktop project-list smoke`

### D1.09 — 有运行中任务时的优雅退出

**Depends on:** D1.04, D1.06  
**Files:**

- Modify: sidecar/窗口关闭处理；复用现有 cancel 路由
- Test: `apps/api/tests/test_job_reliability.py`；Rust 关闭状态机
- Docs: 若仍有缺口则改 `docs/v2_known_limitations.md`

**Implement:** 关闭时若有导入/处理任务在运行：确认 — 取消退出 / 退出并取消任务 / 仍然退出。取消：现有 POST cancel，最多等 10 秒，然后 SIGTERM。仍然退出：SIGTERM，然后 5 秒后 kill。下次启动：现有启动扫描；UI 必须显示恢复消息（`importLoadRecoveryMessage`），而不是光秃秃的 “failed”。

**Tests:** 取消后再重启的导入不在 `processing` 中留下照片；任务终态为 `cancelled` 不是 `failed`；被 kill 的 worker 仍可重试；Rust 状态机在宽限期后返回 Kill。

**Commit:** `desktop: cancel or drain jobs before quitting`

**Phase 1 验收**（已于 2026-08-19 勾选 `上线`；Phase 2 未开始）：

- [x] 首页 UI 或 HTTP smoke 能列出项目 — 来自 `test:desktop:smoke`、活 sidecar、桌面 sidecar `:54451` 以及浏览器 API `:8000` 的 `GET /api/projects` `[]`
- [x] Sidecar health OK — `GET /health` `{"status":"ok","version":"2.0.0-rc2","service":"framepilot-api"}`
- [x] 无 Tauri 时 `npm run verify` 全绿 — 退出码 0；fail-if-invoked 的 `rustc`/`cargo`/`tauri` 包装器未被 verify 调用
- [x] 浏览器 `npm run dev` 在 :3000/:8000 仍可用 — 2026-08-19T18:59:32+08:00 `npm run dev`：`:8000/health` 200，`:8000/api/projects` `[]`，`:3000/` 200 标题 `FramePilot`

---

## Phase 2 — 原生文件系统与核心工作流（约 1.5–2 周）

**阶段目标：** 使用原生文件夹选择器完成 导入 → 处理 → 筛选 → 导出。原图保持不可变。

### D2.00 — 为桌面文件夹选择器注册项目根

**Depends on:** D0.03  
**Files:**

- Create: `apps/api/app/core/project_roots.py`
- Modify: `apps/api/app/services/projects.py`（允许的根），`apps/api/app/api/routes.py`
- Docs: `docs/api.md`（`root_path` 目前省略了 allowlist）
- Test: `apps/api/tests/test_desktop_project_roots.py`

**Implement:**

- 问题：allowlist 经 `lru_cache` 只读一次；用户是在进程拉起**之后**选文件夹。把 `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST=$HOME` 会废掉该控制。
- 进程级注册表**不**放在 `Settings` 内（改 settings 会重置 DB engine）。持久化 `{data_dir}/desktop_project_roots.json`，上限 50。
- `register_root`：绝对路径、存在、是目录、已 resolve；拒绝 `BLOCKED_ROOT_NAMES`、文件系统锚点、数据目录及其父目录。
- `create_project` 允许的根 = `[projects_root, *allowlist, *registered_roots()]`。不要改错误消息。
- 端点**仅当 `FRAMEPILOT_DESKTOP=1`**（否则 404）：`POST /api/desktop/project-roots` `{"path"}`，`GET` 相同。
- 桌面流程：选择 → POST 注册 → 带 `root_path` 的 POST `/api/projects`。

**Tests:** 现有 allowlist 测试仍原样通过；根在注册前在外则为 422；`/`、`/etc`、`C:\Windows`、数据目录为 422；相对路径 / 文件为 422；未设置桌面环境时端点 404；根在 `create_app()` 重启后仍在；fixture 中有 `clear_registered_roots()`。

**Commit:** `api: register desktop project roots before use`

### D2.01 — 桌面能力：选择文件与目录

**Depends on:** Phase 1  
**Files:** `apps/desktop/src/lib/nativeFs.ts`、Tauri dialog plugin、capabilities JSON

**Implement:** `pickDirectory()`、`pickImageFiles()`、`revealInFileManager()`。Web 构建不得 import Tauri 插件。浏览器中 `getNativeFs()` 返回 `null`。

**Tests:** 单测浏览器 null 分支；桌面包装被 mock。

**Commit:** `desktop: add native file dialog adapters`

### D2.02 — 用原生目录选择器创建 / 打开项目

**Depends on:** D2.00, D2.01  
**Files:** `ProjectCreator.tsx`、`apps/web/src/lib/api.ts`、`apps/web/src/lib/projectCreation.ts`

**Implement:** 若存在原生 FS，Browse 在 `POST /api/desktop/project-roots` 之后填入 `root_path`。原样展示 422。给 `createProject` 增加 `acknowledgeNonempty`。确认文案：“This folder already contains files. FramePilot will create its project folders inside it and will not modify existing files. Continue?” 浏览器：文本框保留；未确认则不加 acknowledge 标志。

**Tests:** `projectCreation.test.ts` — 仅在确认后才有 `acknowledgeNonempty`。API：已注册的非空根无该标志失败、有该标志成功；现有文件仍在。

**Commit:** `web: use native directory picker when desktop APIs exist`

### D2.03 — 导入面板在桌面上使用路径导入

**Depends on:** D0.04b, D2.01  
**Files:** `ImportPanel.tsx`、`apps/web/src/lib/api.ts`、`apps/web/src/lib/importWorkflow.ts`

**Implement:**

- 桌面：选择文件夹/文件 → `importPhotosFromPaths`，用同一个 `job_id` 循环 `remaining_paths`，仅最后一片 `finalize: true`。进度使用 `expanded_total`。
- 浏览器：现有 multipart。
- **不变量：** 当 `isDesktopShell()` 为 false 时，两个 `<input type="file">` 元素（`ImportPanel.tsx` 约 234 与约 253，含 `webkitdirectory`）保持当前 DOM 位置、标签与 disabled 语义。`tests/e2e/local-workflow.spec.ts` 依赖它们。

**Tests:** `importWorkflow.test.ts` 分支 + remaining-paths 循环。关闭 Phase 2 前运行 `npm run test:e2e`。

**Commit:** `web: import from local paths in desktop mode`

### D2.04 — 把文件夹 / 文件拖放到导入视图

**Depends on:** D2.03  
**Files:** `ImportPanel.tsx`；若 WebView 拖放不够再用 Tauri drag-drop

**Implement:** 放下的路径喂给 `from-paths`。除非正在拖拽，否则 overlay `pointer-events: none`（不得挡住 Playwright 文件输入）。不要在导入页之外的 drop 上开始导入。

**Tests:** `collectDroppedPaths(event)` 单元测试。运行 `npm run test:web`，并在 Phase 2 收尾记录 E2E。

**Commit:** `desktop: add import drag-and-drop`

### D2.05 — 在文件管理器中显示项目、originals 与导出文件夹

**Depends on:** D2.01  
**Files:** `ProjectDashboard.tsx`、`ExportPanel.tsx`

**Implement:** 经 `revealInFileManager` 提供 “Open project folder”、“Open export folder”。文件夹导出已经返回 `output_path`。

**Tests:** 一个辅助测试：reveal 回调以 `output_path` 被调用。运行：`npm run test:web`。

**Commit:** `desktop: reveal project and export paths in the OS file manager`

### D2.06 — 最近项目（桌面）

**Depends on:** D1.05  
**Files:** 辅助函数 + `ProjectList.tsx`

**Implement:** 上次打开的项目 id 存在 localStorage。不要发明第二个数据库。`GET /api/projects` 仍是列表。

**Tests:** `recentProjects.test.ts`（或 `.test.tsx`）。运行：`npm run test:web`。

**Commit:** `desktop: remember last opened project`

### D2.07 — 跨平台路径加固

**Depends on:** D0.04a  
**Files:** `importing.py`、`projects.py`、测试

**Implement / test:** Windows 盘符、空格、非 ASCII、尾部分隔符、拒绝 NUL；保持 `os.pathsep` allowlist 解析。POSIX 上跳过仅 Win32 的现场用例。

**Commit:** `api: harden desktop import paths`

### D2.08 — 完整工作流验证

**Depends on:** D2.03, D2.05  
**Files:** `tests/desktop/workflow.md` + 使用 `from-paths` 然后 process + export 的 pytest

**Automated:** 创建项目，经 from-paths 导入合成 JPEG，处理，标记 Pick，CSV/ZIP/文件夹导出，原图不变。

**Manual checklist** 在 GUI 存在时：选择文件夹、用键盘筛选、导出、显示文件夹。

**Tests:** 上述 pytest。运行：`npm run test:api`，若改了 ImportPanel 再跑 `npm run test:e2e`。

**Commit:** `test: cover path-import process export workflow`

### D2.09 — 桌面上显示导出产物而不是下载

**Depends on:** D2.01, D2.05  
**Files:** `ExportPanel.tsx`（约 241 与 308 行的 `<a download>`）；`ImportExportPanels.test.tsx`

**Implement:** 在桌面上，用基于 `output_path` 的 “Show in folder” 替换下载锚点。浏览器保留锚点。按 `isDesktopShell()` 分支。若 macOS WKWebView 挡住回环 HTTP 图片，记录下来 — 不要在这里重做资源管线。

**Tests:** `__FRAMEPILOT_DESKTOP__ = true` 时有 reveal 按钮且无 `<a download>`；标志未设置 → 当前 href。

**Commit:** `desktop: reveal export artifacts instead of downloading them`

**Phase 2 验收：**

- [x] 桌面（或 API 等价物）完成 导入 → 处理 → 筛选 → 导出 — API pytest `test_path_import_process_pick_and_export_leaves_originals_unchanged` 加上浏览器 e2e smoke（`npm run test:e2e`，45 passed，2026-08-21T08:36:30+08:00）
- [x] 源文件未被修改 — D2.08 pytest 断言源 `st_size` / `st_mtime_ns` / SHA-256 不变；`test_import_from_paths_immutability.py` 全绿
- [x] multipart 浏览器导入与 E2E 文件输入仍可用 — `ImportExportPanels.test.tsx` `webkitdirectory` 输入；e2e `Choose image files` smoke
- [x] `npm run verify` 全绿 — 无 rust 包装器，退出码 0，2026-08-21T08:36:30+08:00

---

## Phase 3 — 桌面 UI 与原生窗口装饰（约 2 周）

**阶段目标：** 感觉像桌面产品。不要重写筛选工作区。分离预览 / 并发旋钮 / 更新器 **不在 2.1 范围内**。

### D3.01 — 原生菜单栏

**Depends on:** Phase 2  
**Files:** Rust 菜单 `apps/desktop/src-tauri/src/menu.rs` 拥有原生动作（Edit / About / Close / Quit / Fullscreen / Open-data-folder）。JS `apps/web/src/lib/menuRoutes.ts` 只解析可导航命令（`new`、`shortcuts`、`import`、`export`、`process`、`cull`）为 href 或 ignore。Help 只列出 `CmdOrCtrl+N/W/Q`，不复制一份原生菜单树。

菜单：File（New、Open data folder、Import、Export、Close、Quit）；Edit（操作系统默认）；View（Fullscreen）；Project（Process、Culling）；Help（Shortcuts、仅 About 对话框 — 无更新器）。

保留 P/M/X/U/1–5/0/Space/Z/C/G/F/E。**任何原生菜单项都不得对这些键使用裸键加速键**。

**Tests:** `menuRoutes.test.ts`（仅可导航 id；原生拥有的 id 返回 ignore）。运行：`npm --prefix apps/web run test:unit`。记录 GUI 或 `[~]`。

**Commit:** `desktop: add native application menu`

### D3.02 — 状态栏与处理可见性

**Depends on:** D3.01, D1.02a  
**Files:** 仅桌面的状态栏，或由 `isDesktopShell()` 门控的 `Shell.tsx`

显示 sidecar 已连接、项目名、任务步骤/百分比。复用 `processingProgress.ts` 中的 `firstActiveJob` / `hasActiveProcessingJob`。`Shell` 把 `usePathname()` 传入状态栏；状态栏不读 `window.location`，也不 import `menuRoutes`。jobs query key 仍是 `["jobs", projectId]`，空闲时慢轮询，以便新开始的导入可见。

**Tests:** `processingProgress.test.ts` / `statusBarModel.test.ts`。运行：`npm --prefix apps/web run test:unit`。

**Commit:** `desktop: add status bar for sidecar and jobs`

### D3.03 — 设置：数据目录显示

**Depends on:** D1.05  
**Files:** `SettingsPanel.tsx`；新增 `GET /api/meta`（**不要**扩展 `/health`）

**Implement:** `GET /api/meta` → `{version, service, data_dir, desktop_mode}`。设置：只读数据目录 + 桌面上的 “Open data folder”。更改数据目录不在 2.1 范围内。

**Tests:** `/api/meta` 返回被 monkeypatch 的 `FRAMEPILOT_DATA_DIR`；`desktop_mode` 跟随环境变量。组件显示该值。

**Commit:** `desktop: show data directory in settings`

### D3.04 — 跟随系统主题（浅色 / 深色）

**Depends on:** D3.02  
**Files:** `ink` / `mist` / `line` / `surface` / `muted` 的 CSS 变量（`apps/web/src/app/globals.css` 中 `--fp-*` 浅色默认；`apps/desktop/src/styles.css` 在 `html[data-shell="desktop"]` 且 `prefers-color-scheme: dark` 时交换）。两边 Tailwind 配置都消费 `apps/web/src/theme/tokens.ts`。不要 Tailwind `darkMode`，不要 `dark:` 补丁，不要重映射 `.bg-white`。主按钮 `bg-ink` 使用 `text-mist`。浏览器保持仅浅色。

**Tests:** `apps/web/src/lib/desktopTheme.test.ts`。运行：`npm --prefix apps/web run test:unit`。没有桌面 WebView 记录时视觉 GUI 仍为 `[~]`。

**Commit:** `desktop: follow system light/dark theme`

### D3.05 — 窗口装饰与空状态 / 错误文案

**Depends on:** D3.02  
**Files:** 列表、导入、筛选、导出上的空状态

桌面文案：“Choose a folder”，不是 “Choose files in your browser”。UI 一次选择 `copyForShell(isDesktopShell())`。`importWorkflow` / `exportSelection` 辅助函数不接收 `desktop` 参数，也不调用 shell copy。ImportPanel 文件夹标签来自 `copy.chooseFolder`。保持 Help 快捷键准确。

**Tests:** `shellCopy.test.ts`（`copyForShell` 记录；ImportPanel 使用 `copy.chooseFolder`）。运行：`npm --prefix apps/web run test:unit`。

**Commit:** `desktop: adapt empty and error copy for native folders`

### D3.06 — 可选托盘（若时间不够则推迟）

**Depends on:** D3.02  
**除非 Phase 3 进度超前，否则跳过。** 不是 DoD 要求。若跳过：标 `[-]` 并在 D5.05 注明。

**Tests:** 若推迟则为 none（`docs` 提交）。若实现：smoke 托盘菜单有 Show + Quit。

**Commit:** `desktop: add optional tray status` **或** `docs: defer desktop tray to a later release`

### D3.07 — 键盘与原生菜单冲突核对

**Depends on:** D3.01  
**Files:** `CullingWorkspace.tsx` keydown、菜单加速键、Help 页

不要抢走 P/M/X。在 Help 上记录加速键。

**Tests:** `reviewShortcutCommandFromEvent` 仍忽略带修饰键的组合。运行：`npm run test:web`。

**Commit:** `desktop: reconcile shortcuts with native menus`

**Phase 3 验收：**

- [x] 菜单动作到达真实路由
- [x] 键盘筛选仍与 Help 一致
- [x] 设置显示数据目录
- [x] 桌面导入不要求浏览器文件输入
- [x] `npm run verify` 全绿 — 2026-08-28T17:28:00+08:00（无 rust；D3.01–D3.03 GUI 仍为 `[~]`）

---

## Phase 4 — 安装包、CI、签名准备（约 1–1.5 周）

**阶段目标：** 从 CI 产出未签名（然后可选签名）的 Windows NSIS 与 macOS DMG。

### D4.01 — 把 sidecar 打进 Tauri resources

**Depends on:** D0.05, Phase 1  
**Files:** `tauri.conf.json` 的 `externalBin` / `resources`，`packaging/scripts/stage-sidecar.sh`

开发用 venv；发布用 PyInstaller 输出。

**Tests:** none（构建配置）。运行：`npm run verify`。记录 GUI 或 `[~]`。

**Commit:** `desktop: bundle PyInstaller sidecar in Tauri resources`

### D4.02 — Windows NSIS 与 macOS DMG 配置

**Depends on:** D4.01  
**Files:** `tauri.conf.json`

应用名 `FramePilot`；bundle id `com.framepilot.app`。

**Tests:** none（bundle 配置）。运行：`cargo check`。

**Commit:** `desktop: configure NSIS and DMG bundle targets`

### D4.03 — 已迁移

已迁移到 **D0.00**。不要实现两次。若 `.github/workflows/verify.yml` 已存在，则此 id 完成（§5.1 中为 `[-]`）。

**Depends on:** n/a  
**Files:** none  
**Implement:** no-op  
**Tests:** none  
**Commit:** none

### D4.04 — GitHub Actions 桌面矩阵

**Depends on:** D4.01, D4.02, D0.00  
**Files:** `.github/workflows/desktop.yml`

矩阵：`windows-latest`、`macos-latest`（可选 `ubuntu-latest` 仅 sidecar）。构建 sidecar、`tauri build`，只上传安装包产物。在证书存在之前保持未签名。永不上传照片。

**Tests:** none（CI）。合并后确认产物存在。

**Commit:** `ci: build Windows and macOS desktop artifacts`

### D4.05 — 签名与公证文档

**Depends on:** D4.04  
**Files:** `docs/desktop_signing.md`

未签名构建可供内部测试者使用，README 需有警告。不要因缺少证书让第一个 RC 失败。

**Tests:** none（文档）。

**Commit:** `docs: add desktop code signing runbook`

### D4.06 — 体积核对

**Depends on:** D4.01  
**Files:** 可行性说明

若未打包 sidecar + 应用 **> 400 MB**，记录 scipy/imagehash 成本。不要剥掉 Pillow 编解码器。

**Tests:** none（文档）。

**Commit:** `docs: record desktop installer size budget`

**Phase 4 验收：**

- [x] PR 上 CI verify 全绿（D0.00）
- [x] CI 产出 Windows 安装包 + macOS DMG（未签名 OK）— 证据 2026-08-28：[desktop.yml run 33170731977](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/33170731977)（`00e34a5`，D4.04 合入）上传了 `FramePilot-windows-nsis` + `FramePilot-macos-dmg`。可再次通过 Actions → desktop → workflow_dispatch 确认。
- [x] 签名已文档化
- [x] `check:artifacts` 仍拒绝提交二进制；图标例外保持狭窄

---

## Phase 5 — 测试、文档、稳定（约 1 周）

**阶段目标：** 满足产品计划 §2.2 对 `2.1.0-desktop` 的 Definition of Done。

### D5.01 — 桌面测试矩阵文档 + 命令

**Depends on:** Phase 4  
**Files:** `docs/desktop_testing.md`、package.json 脚本

矩阵：启动 / 退出 / sidecar 崩溃 / 端口占用；路径导入 100 张合成 JPEG；可选经 `perf:api` 的 500/2000；安装 / 卸载清单；origin/CORS 说明（因仅回环，LAN 访问不可能）。

**Tests:** none（文档），除非加了新脚本，那时运行该脚本。

**Commit:** `docs: add desktop test matrix`

### D5.02 — README 与用户文档

**Depends on:** D5.01  
**Files:** `README.md`、`docs/desktop_user_guide.md`、`docs/v2_known_limitations.md`、`docs/v2_architecture.md`（一旦发布，桌面不再是 deferred）

覆盖：安装、首次启动、数据位置、是复制不是移动、显示导出文件夹、如何继续用 Web 应用做开发。

**Tests:** none（文档）。若改了 README 脚本则运行 `npm run verify`。

**Commit:** `docs: add desktop install and data-dir instructions`

### D5.03 — 桌面 WebView 性能说明

**Depends on:** D2.08  
**Files:** 可行性说明或 `docs/v2_performance_baseline.md`

一次 100 张导入 + 处理，记录 sidecar 与 UI 的 RSS（若有 GUI）；否则仅 sidecar，并标明 UI 待测。multipart 证据已在 #96 澄清；真正的 `from-paths` RSS 已在 #97 记录（WSL2 峰值 119.77 MB，UI pending）。

**Tests:** none（文档）。

**Commit:** `docs: record desktop performance notes`

### D5.04 — 版本升到 2.1.0-desktop（发布候选）

**Depends on:** Phase 0–4 验收框  
**Files:** `apps/api/app/core/version.py`、`pyproject.toml`、两个 `package.json`、FastAPI 已读取 `APP_VERSION`、changelog

在 `npm run verify` 与桌面 CI 产物存在之前不要打 tag。不要散落版本字面量。

**Tests:** health 仍返回 `APP_VERSION`。运行：`npm run test:api` `npm run verify`。

**Commit:** `release: 2.1.0-desktop rc`

### D5.05 — 桌面 2.1 已知限制

**Depends on:** D5.02  
**Files:** `docs/v2_known_limitations.md`

列出：任务在 sidecar 被 kill 后不持久；HEIC/RAW 被跳过；自动更新推迟；在有证书前未签名；WSL 可能跑不了 GUI；仅复制模式；无分离预览；无并发旋钮；除非 D3.06 已交付否则托盘推迟。

**Tests:** none（文档）。

**Commit:** `docs: document desktop 2.1 known limitations`

**Phase 5 / 产品 DoD：**

- [x] Windows 与 macOS 安装包存在（CI 产物）— [desktop.yml run 33170731977](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/33170731977)（可经 Actions → desktop 再确认）
- [x] 应用启动管理 Python sidecar，用户无需自己跑 uvicorn — Phase 1 sidecar 生命周期已在 `main`
- [x] 原生文件夹选择器与拖放导入 — Phase 2；部分主机 live GUI 可仍为 `[~]`（见可行性笔记）
- [x] 核心工作流与 v2 一致：导入、处理、键盘筛选、CSV/ZIP/文件夹导出 — D2.08 + 共享 UI
- [x] 原图永不被修改 — 不可变测试 + 用户指南
- [x] 500 张照片的 API 级导入不崩溃；若测过则记录 500 GUI — API 经 multipart `perf:api` / 既有 smoke（非 `from-paths`）；收尾主机 **未测 500 GUI**（性能基线 / 测试矩阵已记 pending）
- [x] 用户 + 开发者文档存在 — D5.01–D5.02（`desktop_testing`、`desktop_user_guide`、README、架构）
- [x] CI 构建双平台安装包；签名仍可待定 — D4.04 + D4.05 签名手册
- [x] 回环绑定 + Host/Origin 检查已就位 — Phase 0
- [x] 自定义项目根仅经 D2.00 注册 — Phase 2

Phase 5 Dev 合入（2026-08-29）：#85 D5.01、#87 D5.02、#89 D5.03、#91 D5.04、#93 D5.05。研究/设计：#80、#83。总议题 #78。

---

## 6. 本轨道不要做什么

- 不要实现 HEIC、RAW、XMP 或本地神经网络模型。
- 不要加入云更新器。
- 不要替换 SQLite，也不要把评分搬到 Rust。
- 不要删除 Next.js 应用或弄坏 Playwright。
- 除非 D0.09 写明 Tauri 失败，否则不要切到 Electron。
- 不要监听 `0.0.0.0`。
- 不要把 multipart 上传当作大批次的桌面主导入路径。
- 不要把 `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` 设为 `$HOME`、`/` 或盘符根。
- 不要把产物检查脚本放宽到超出 D0.07a。
- 不要在 `apps/api/app/core/version.py` 之外增加版本字面量。

---

## 7. 建议的提交节奏

一个 task id = 一次提交（D1.01 可以叠 2–3 次）。不要把整个阶段打成一批。

---

## 8. 停止条件

若出现以下情况则停止并总结：

- Phase 5 全部 DoD 框已勾选，或
- D0.09 需要产品决策且说明已提交，或
- 缺少 OS / 签名 / WebView 使 GUI 工作无法进行，剩余工作仅文档 / CI，或
- 聚焦调试后测试仍无法全绿，或
- 命中会话预算（5 个任务或一个阶段）。

最终总结：分支、提交、已完成 task id、已运行检查、剩余 id、风险、下一句 Goal 提示。

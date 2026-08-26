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
| ---- | -------- |
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
- [~] D3.02 状态栏 — `npm run test:web` 于 2026-08-26 通过；GUI/`cargo test` 未验证（`rustc` 1.85 无法编译当前 Tauri lockfile）。见 `docs/desktop_feasibility_notes.zh.md`。
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
{"paths": ["/abs/folder", "/abs/file.jpg"], "form_id": null, "expected_total": null, "finalize": true}
```
# FramePilot 桌面版开发计划

> **文档版本**：1.2  
> **创建日期**：2026-08-18  
> **最近审阅**：2026-08-18 Claude Opus 5（见 `docs/plans/2026-08-18-desktop-packaging-review.md`）  
> **目标**：将当前本地 Web 应用（v2.0.0-rc2）重新设计并打包为可安装的 Windows 与 macOS 桌面应用  
> **仓库**：https://github.com/joe-cheung-cae/frame-pilot  
> **相关已有规划**：`develop_plan.md` 已将 “Local desktop packaging with Tauri or Electron” 列为 stretch goal；本文件将其正式产品化。  
> **技术细节以实施计划为准**：`docs/plans/2026-08-18-desktop-packaging.md`。本文不新增 task id。

---

## 1. 项目现状摘要

FramePilot 是一款**本地优先**的 AI 辅助照片筛选（photo culling）工具。

| 项目 | 说明 |
|------|------|
| 前端 | Next.js 15 + React 19 + TypeScript + Tailwind CSS |
| 后端 | FastAPI + SQLModel + SQLite + Pillow + imagehash + numpy |
| 运行方式 | 浏览器访问 `localhost:3000`，本地 API `localhost:8000` |
| 数据 | 全部保存在本地（默认 `.framepilot-data`），不上传原图 |
| 核心流程 | 创建项目 → 导入 JPEG/PNG/WebP → 生成预览与评分 → 分组排序 → 键盘筛选 → CSV/ZIP/文件夹导出 |
| 当前版本 | 2.0.0-rc2 |

现有架构已经是“本地进程 + 本地 HTTP”，非常适合包装成桌面应用。

---

## 2. 目标与成功标准

### 2.1 产品目标

1. 提供可直接安装的 **Windows 安装包**（.exe / NSIS 或 MSI）与 **macOS 安装包**（.dmg）。
2. 用户安装后无需手动启动后端或打开浏览器，双击即可使用。
3. 前端界面针对桌面体验重新设计（原生菜单、文件对话框、拖放、大屏布局等）。
4. 保持现有本地优先、原图不可变、隐私安全原则不变。
5. 现有核心工作流（导入 → 处理 → 筛选 → 导出）在桌面环境下完整可用。

### 2.2 Definition of Done（首个桌面版本 `2.1.0-desktop`）

- [ ] Windows 与 macOS 均可通过标准安装包安装并运行
- [ ] 应用启动时自动管理 Python sidecar，用户无感知后端进程
- [ ] 使用原生文件夹选择器与拖放导入
- [ ] 现有全部核心功能可用且行为与当前 v2 一致
- [ ] 原图安全规则与本地优先原则保持不变
- [ ] 大项目（≥500 张）不崩溃，内存占用可接受
- [ ] 提供用户安装说明与开发者构建文档
- [ ] CI 可自动构建双平台安装包（代码签名可后续完善）
- [ ] 桌面 sidecar 仅监听 127.0.0.1，且拒绝非回环 Host 与未授权 Origin
- [ ] 用户选择的项目根目录经过显式授权后才被接受（见实施计划 D2.00）

不在 `2.1.0-desktop` 范围内（见 §5.6 延后清单）：分离预览窗口、并发/缓存性能选项、自动更新、系统托盘（时间允许时可选）。

---

## 3. 技术选型

### 3.1 推荐方案：Tauri 2 + Python Sidecar

| 方案 | 安装包体积 | 内存 | 原生能力 | 迁移成本 | 推荐度 |
|------|------------|------|----------|----------|--------|
| **Tauri 2 + Python Sidecar** | 小（系统 WebView） | 低 | 强 | 中 | ★★★★★ |
| Electron + Python Sidecar | 大（内嵌 Chromium） | 高 | 强 | 较低 | ★★★☆☆ |
| 纯原生重写（Qt / Flutter） | 中 | 中 | 最强 | 极高 | ★☆☆☆☆ |

**选择 Tauri 2 的理由：**

- 安装包与运行时内存显著小于 Electron，适合照片类重资源应用。
- 安全性更高（默认最小权限，无 Node 在渲染进程）。
- 官方支持 Windows NSIS/MSI 与 macOS DMG、代码签名与公证。
- 内置 sidecar 进程管理能力，适合捆绑 FastAPI 后端。
- 原生文件对话框、菜单、拖放、单实例控制等桌面能力完善。

### 3.2 后端打包

- 使用 **PyInstaller**（或评估 Nuitka）将 `apps/api` 打成独立可执行文件。
- 依赖：fastapi、uvicorn、pillow、imagehash、numpy、sqlmodel、python-multipart 等。
- 作为 Tauri sidecar 随主程序启动、监控与退出。

### 3.3 前端适配（已锁定：双壳、单组件库）

Phase 0 的 `output: 'export'` 尝试仅作为一次性调研（实施计划 D0.06），**结论已预期为不可行**：`projects/[projectId]/...` 动态 UUID 路由无法静态预渲染。

锁定方案：

- `apps/web` 保持 Next.js，服务浏览器开发与 Playwright，**不迁移、不删除**。
- `apps/desktop` 新增 Tauri 2 + Vite + React SPA（React Router）。
- 两个壳共享 `apps/web/src/components`、`src/lib`、`src/store`；共享文件不得直接 import `next/link` 或 `next/navigation`，统一走导航适配层（D1.01）。
- Vite 侧必须自备 `@` 路径别名、PostCSS/Tailwind 配置，并复用 `globals.css`（D1.03a）。

通信方式：`http://127.0.0.1:<port>`，端口由 Tauri 分配并在前端加载前注入。Tauri IPC 仅用于对话框、路径与在文件管理器中显示。

### 3.4 数据目录

| 平台 | 默认数据目录 |
|------|----------------|
| macOS | `~/Library/Application Support/FramePilot` |
| Windows | `%APPDATA%\FramePilot` |
| Linux（仅开发，不作为发布目标） | `~/.local/share/FramePilot` |

支持通过 `FRAMEPILOT_DATA_DIR` 覆盖。桌面版 sidecar 必须显式接收 `--data-dir`：冻结后的可执行文件工作目录不可预测，禁止回退到相对当前目录的 `.framepilot-data`。

---

## 4. 目标架构

```text
FramePilot Desktop
├── Tauri Shell（Rust 主进程）
│   ├── 窗口 / 菜单 / 系统托盘（可选）
│   ├── 启动、健康检查、优雅退出 Python sidecar
│   ├── 原生文件 / 文件夹选择器
│   ├── 单实例控制
│   └── 自动更新（后续可选）
├── 前端（静态资源，系统 WebView 加载）
│   └── 现有 React 组件 + 桌面适配层
└── Python Backend Sidecar（独立可执行文件）
    ├── FastAPI（127.0.0.1 固定或动态端口）
    ├── SQLite 元数据
    └── 本地项目目录（originals / thumbnails / previews / exports / …）
```

**核心原则：**

- 不上传原图，不修改原文件。
- 前后端职责边界与现有 v2 架构保持一致。
- 进程生命周期由桌面壳统一管理。

---

## 5. 前端界面重新设计原则

现有 culling workspace 已具备良好的键盘优先设计。桌面版在此基础上强化原生体验，而不是推倒重来。

### 5.1 原生窗口与菜单

- 标准菜单栏：File / Edit / View / Project / Help
- 系统级快捷键（Cmd/Ctrl + 对应菜单项）
- 窗口状态记忆（位置、大小、最大化）

### 5.2 原生文件系统交互

- 使用 Tauri 原生对话框创建/打开项目、选择导入文件夹
- 支持从 Finder / Explorer 直接拖放整个文件夹导入
- 项目路径、导出路径可一键在系统文件管理器中打开

### 5.3 Culling Workspace 桌面优化

- 充分利用大屏幕：可调侧边栏、可选分离预览窗口
- 清晰状态栏与处理进度反馈
- 保留并强化现有键盘快捷键（方向键、P/M/X/U、1–5、0、Space、Z、C、G、F、E 等）
- 全屏预览与对比模式
- 大项目下的虚拟列表与懒加载保持现有策略

### 5.4 设置与系统集成

- 主题跟随系统（深色 / 浅色）
- 数据目录管理、性能选项（并发、缓存）
- 可选系统托盘（后台处理时显示进度）
- 关于页面、检查更新入口

### 5.5 视觉一致性

- 保持现有 Tailwind 风格
- 增加桌面应用常见的间距、层级与焦点管理，降低“网页感”

### 5.6 明确延后（不进入 `2.1.0-desktop`）

| 项目 | 原因 | 目标版本 |
|------|------|----------|
| 分离预览窗口（§5.3） | 需要第二个 WebView、跨窗口状态同步与第二套键盘焦点管理 | 2.2 |
| 性能选项：并发、缓存（§5.4） | 后端导入/处理目前为单线程顺序执行，需先有并发模型 | 2.2 |
| 自动更新与“检查更新”入口（§5.4、§6 Phase 4） | 需要托管更新清单；必须严格可选且不得阻塞启动 | 2.2 |
| 系统托盘（§5.4） | 非 DoD 项；仅在 Phase 3 提前完成时实现（D3.06） | 2.1 可选 / 2.2 |
| 更换数据目录（§5.4） | 涉及迁移与项目路径重写；2.1 仅只读展示（D3.03） | 2.2 |

以上项目若被跳过，必须写入 `docs/v2_known_limitations.md`（D5.05）。

---

## 6. 分阶段开发计划

总预估工作量（单人全职或强 AI 辅助）：**约 6–10 周**。

### Phase 0：可行性验证与桌面必需 API（约 3–5 天）

**目标**：证明 sidecar 可被打包与托管；同时落地桌面必须依赖的后端接口。

任务（权威拆分见实施计划 D0.00–D0.09）：

1. CI verify 工作流先行（D0.00），保证后续每次提交可被验证。
2. sidecar CLI：仅回环绑定、显式 `--data-dir`、可机读的 ready 行。
3. 健康检查携带版本；Origin 与 Host 白名单支持桌面模式。
4. 基于路径的导入 API（分片请求，原图只读）。
5. PyInstaller one-dir 打包与无 GUI 冒烟。
6. 最小 Tauri 窗口 + sidecar 启动与健康检查（需要可用 WebView 的宿主）。
7. 记录体积、启动时间、内存基线；写出 go/no-go。

验收（按环境区分）：

- **无 GUI 主机（如 WSL2）**：sidecar 可启动、`/health` 正常、收到 SIGTERM 后退出；路径导入不修改原文件；`npm run test:api` 与 `npm run verify` 通过；Tauri 相关任务标记为 blocked-gui 并在 `docs/desktop_feasibility_notes.md` 记录命令与错误。
- **有 GUI 主机（Windows / macOS / CI）**：至少一个平台出现空壳窗口并显示 “API ready”；双平台窗口验证可延后到 Phase 4 CI 完成。

Phase 0 不因缺少 GUI 而阻塞；但 `2.1.0-desktop` 发布前必须补齐双平台窗口证据。

---

### Phase 1：桌面壳与 Sidecar 基础（约 1.5–2 周）

**目标**：开发模式下可完整启动桌面应用。

任务：

1. 新增 `apps/desktop`（或仓库根 `src-tauri`）目录，集成 Tauri 2。
2. 实现 sidecar 生命周期管理：启动、健康检查、优雅退出、崩溃重启策略。
3. 适配数据目录到用户标准位置，支持环境变量覆盖。
4. 新增 `apps/desktop`：Vite + React SPA，复用 `apps/web/src/components`、`src/lib`、`src/store`（**不**改造 `apps/web` 为静态导出）。
5. 基本窗口创建、关闭、单实例控制。
6. 开发脚本：`tauri dev` 一键启动前端 + sidecar。

交付物：

- 可在开发机上通过 `tauri dev` 运行的桌面应用
- 目录结构与构建脚本说明

验收：

- 启动后前端能调通后端健康检查与项目列表 API

---

### Phase 2：原生文件系统与核心工作流（约 1.5–2 周）

**目标**：完整工作流在桌面环境可用。

任务：

1. 替换浏览器 File API 为原生文件/文件夹选择器。
2. 支持拖放文件夹导入。
3. 项目创建、打开、最近项目列表的桌面化。
4. 验证 Import → Process → Culling → Export 全流程。
5. 处理跨平台路径、权限、盘符差异。
6. 导出结果可在系统文件管理器中打开。

交付物：

- 功能完整的桌面版工作流

验收：

- 使用合成或真实 JPEG 完成一次完整筛选与导出
- 原图未被修改或删除

---

### Phase 3：界面重新设计与体验打磨（约 2 周）

**目标**：达到专业桌面产品观感。

任务：

1. 实现原生菜单栏与快捷键映射。
2. 优化 Culling Workspace 布局与大屏适配。
3. 状态栏、进度反馈、设置页完善。
4. 主题系统、窗口状态记忆。
5. 可选：系统托盘与后台处理通知。
6. 空状态、错误状态、加载状态的桌面化文案与交互。

交付物：

- 视觉与交互达到桌面产品水准的 UI

验收：

- 键盘主导的筛选体验流畅
- 无明显“浏览器网页”感

---

### Phase 4：安装包、签名与发布准备（约 1–1.5 周）

**目标**：产出可分发的正式安装包。

任务：

1. 配置 Windows NSIS（或 MSI）与 macOS DMG 构建。
2. 集成代码签名（Windows Authenticode、macOS Developer ID + 公证）。
3. GitHub Actions CI：自动构建双平台安装包。
4. 可选：Tauri updater 基础自动更新。
5. 安装包体积与依赖精简优化。

交付物：

- 可分发的 `.exe` / `.dmg`（及签名说明）
- CI 工作流文件

验收：

- 干净机器上安装后可正常启动完整流程

---

### Phase 5：测试、文档与稳定化（约 1 周）

**目标**：可正式发布的 v2.x Desktop。

任务：

1. 桌面专用测试矩阵：
   - 启动 / 退出 / sidecar 崩溃恢复
   - 大项目导入与处理（100 / 500 / 2000）
   - 路径权限与跨平台差异
   - 安装 / 卸载干净性
2. 更新 README、用户手册、已知限制文档。
3. 性能与内存验证。
4. 发布说明（Changelog）与版本号：首个桌面版本锁定为 `2.1.0-desktop`；`2.0.x` 继续作为本地 Web 线。不使用 `3.0.0`（无破坏性数据格式变更）。

交付物：

- 测试报告
- 更新后的文档
- 正式发布候选包

验收：

- 满足第 2.2 节全部 Definition of Done

---

## 7. 建议仓库目录结构（增量）

```text
frame-pilot/
├── apps/
│   ├── api/                 # 现有 FastAPI（保持）
│   ├── web/                 # 现有 Next.js（浏览器 + Playwright，保持）
│   └── desktop/             # 新增 Tauri 壳（可选位置）
│       ├── src-tauri/
│       │   ├── src/
│       │   ├── icons/
│       │   ├── tauri.conf.json
│       │   └── Cargo.toml
│       └── package.json
├── packaging/
│   ├── pyinstaller/         # 后端打包规格
│   │   ├── framepilot-api.spec
│   │   └── build.sh
│   └── scripts/
├── docs/
│   ├── desktop_development_plan.md   # 本文件
│   └── ...
└── ...
```

（具体目录可在 Phase 0/1 根据团队习惯微调。）

---

## 8. 主要风险与缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Python 依赖体积偏大（Pillow、numpy 等） | 安装包膨胀 | PyInstaller 精简、排除测试依赖；评估 Nuitka；按平台分别构建 |
| 系统 WebView 差异（Windows WebView2 vs macOS WebKit） | 前端兼容性 | Phase 0/1 尽早双平台测试；必要时 CSS/JS 兜底 |
| 代码签名与公证成本、流程 | 分发体验差 | 提前申请证书；CI 中集成签名；开发阶段可用未签名包自测 |
| Sidecar 进程管理（崩溃、端口冲突、僵尸进程） | 稳定性 | 健康检查 + 超时强制清理；启动前端口探测；平台特定退出逻辑 |
| Next.js 静态导出兼容性 | 开发成本 | D0.06 一次性记录；锁定 Vite 桌面壳，不迁移 `apps/web` |
| 大图解码内存压力在 WebView 中的表现 | 大项目体验 | 继续使用现有虚拟列表与有界渲染；监控桌面场景峰值内存 |

---

## 9. 测试策略（桌面增量）

在现有 `npm run verify`、API pytest、前端 unit、E2E 基础上增加：

1. **Sidecar 生命周期测试**：启动失败、端口占用、崩溃后重启。
2. **原生对话框与拖放测试**：人工 + 尽量自动化。
3. **安装包冒烟**：干净 Windows / macOS 虚拟机安装 → 完整工作流 → 卸载。
4. **性能回归**：复用现有 `perf:api` 与真实浏览器 smoke 思路，在桌面壳下记录基线。
5. **安全回归**：确认仍不上传原图、导出路径不逃逸项目根目录。

---

## 10. 版本与发布建议

| 版本 | 含义 |
|------|------|
| 2.0.x | 继续完成当前本地 Web rc 稳定 |
| 2.1.0-desktop | 首个正式桌面安装包发布（已锁定） |
| 2.2 | 分离预览窗口、性能选项、自动更新、托盘等延后项 |
| 后续 3.x | HEIC/RAW、XMP sidecar、可选本地模型等按原 develop_plan 推进 |

发布渠道建议：

- GitHub Releases（主渠道）
- 后续可考虑官网下载页

---

## 11. 工作量粗估（参考）

| 阶段 | 预估 |
|------|------|
| Phase 0 可行性验证 | 3–5 天 |
| Phase 1 桌面壳 + Sidecar | 1.5–2 周 |
| Phase 2 原生 FS + 工作流 | 1.5–2 周 |
| Phase 3 UI 桌面化打磨 | 2 周 |
| Phase 4 安装包与签名 | 1–1.5 周 |
| Phase 5 测试与文档 | 1 周 |
| **合计** | **约 6–10 周** |

实际进度取决于是否坚持 Tauri、前端是否需要 Vite 迁移、以及代码签名准备情况。

---

## 12. 建议的立即下一步

实施级任务拆分与 Goal Mode 提示词（基于 2026-08-18 仓库现状）：

- `docs/plans/2026-08-18-desktop-packaging.md` — 按 D0.00…D5.05 逐条执行的详细开发计划（含 §5.1 任务勾选表）
- `docs/desktop_goal_mode.md` — Grok Build / Codex Goal Mode 可粘贴提示词
- `docs/plans/2026-08-18-desktop-packaging-review.md` — Opus 5 审阅记录

1. **确认技术选型**：采用 Tauri 2 + Python Sidecar（本计划默认；仅在 D0.09 书面否决后回退 Electron）。
2. **创建分支** `feature/desktop-packaging`。
3. **把 `docs/desktop_goal_mode.md` 的长提示词粘贴进 Goal Mode**，从 **D0.00** 开始逐条提交。
4. **执行顺序**：先 D0.00（CI verify），再 D0.01…D0.09。任何任务完成后必须在实施计划 §5.1 勾选对应 id，并与代码同一次提交。

---

## 13. 参考文档（仓库内）

- `README.md` — 当前功能与运行方式
- `develop_plan.md` — v2 总规划（含桌面 stretch goal）
- `docs/plans/2026-08-18-desktop-packaging.md` — 桌面化逐任务实施计划（Goal Mode backlog；技术冲突以此为准）
- `docs/desktop_goal_mode.md` — 桌面化 Goal Mode 提示词
- `docs/plans/2026-08-18-desktop-packaging-review.md` — Opus 5 对产品计划与实施计划的审阅
- `docs/v2_architecture.md` — 架构（desktop packaging 在 v2.0 中仍为 deferred；桌面轨道单独推进）
- `docs/v2_product_requirements.md` — 产品边界
- `docs/v2_known_limitations.md` — 已知限制
- `docs/v2_milestones.md` — 里程碑
- `docs/architecture.md` — 实现级架构说明

---

## 14. 变更记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-08-18 | 1.0 | 首版：基于 frame-pilot v2.0.0-rc2 现状制定的桌面化（Win/macOS）完整开发计划 |
| 2026-08-18 | 1.1 | 增加实施计划与 Goal Mode 入口：`docs/plans/2026-08-18-desktop-packaging.md`、`docs/desktop_goal_mode.md` |
| 2026-08-18 | 1.2 | Opus 5 审阅后对齐：锁定 Vite 双壳、`2.1.0-desktop`、WSL 可感知的 Phase 0 验收、§5.6 延后清单 |

---

*本文档为实施蓝图，实施过程中可根据 Phase 0 实测结果微调技术细节，但应保持「本地优先、原图安全、双平台可安装」三项核心目标不变。*

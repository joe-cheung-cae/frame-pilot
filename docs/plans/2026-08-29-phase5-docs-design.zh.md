# Phase 5 文档设计（2026-08-29）

> 语言：[English](2026-08-29-phase5-docs-design.md) | **中文**

**总议题：** [#78](https://github.com/joe-cheung-cae/frame-pilot/issues/78)  
**本关：** [#81](https://github.com/joe-cheung-cae/frame-pilot/issues/81) — 仅文档设计  
**研究输入：** [2026-08-29-phase5-requirements.zh.md](2026-08-29-phase5-requirements.zh.md)  
**任务 id 真源：** [2026-08-18-desktop-packaging.zh.md](2026-08-18-desktop-packaging.zh.md) Phase 5 / §5.1

本文是 D5.01–D5.05 的**大纲与文件地图**，不是最终用户文案。Gate 3 接受本设计之前，不得落地任何 Dev PR。

---

## 1. 文件地图

| 路径 | 新建 / 修改 | 任务 | 备注 |
| ---- | ----------- | ---- | ---- |
| `docs/desktop_testing.md` + `.zh.md` | **新建** | D5.01 | Phase 5 测试矩阵（命令表） |
| 根 `package.json` | **可选修改** | D5.01 | 仅在提高可发现性时加薄别名；优先文档化现有脚本 |
| `README.md` + `README.zh.md` | **修改** | D5.02 | 简短 Desktop 小节 + 链到用户指南；贡献者仍以 web 为主 |
| `docs/desktop_user_guide.md` + `.zh.md` | **新建** | D5.02 | 终端用户：安装 / 首次启动 / 数据 / 导出揭示 |
| `docs/v2_architecture.md` + `.zh.md` | **修改** | D5.02 | Deferred 中去掉 desktop packaging；指向桌面计划 / 用户指南 |
| `apps/desktop/README.md` | **修改** | D5.02 | 修正「安装包等到 Phase 4」过时表述；链用户指南 + 签名 |
| `docs/v2_performance_baseline.md` + `.zh.md` | **修改** | D5.03 | 新增桌面 sidecar / WebView 小节与 100 张行（或仅 sidecar + UI 待测） |
| `docs/desktop_feasibility_notes.md` + `.zh.md` | **修改** | D5.03 | 测量主机 / UI `[~]` 的日期备注 |
| `apps/api/app/core/version.py` | **修改** | D5.04 | `APP_VERSION = "2.1.0-desktop"` |
| `apps/api/pyproject.toml` | **修改** | D5.04 | `version = "2.1.0-desktop"` |
| 根 / `apps/web` / `apps/desktop` `package.json` | **修改** | D5.04 | `"version": "2.1.0-desktop"` |
| `CHANGELOG.md` + `CHANGELOG.zh.md` | **新建** | D5.04 | **决定：双语配对** |
| `docs/v2_known_limitations.md` + `.zh.md` | **修改** | D5.05 | 新增「Desktop 2.1」节与必需要点 |
| `docs/plans/2026-08-18-desktop-packaging.md` + `.zh.md` | **修改** | 每个 Dev PR | 同一次提交勾选对应 §5.1 |
| 仅收尾：Phase 5 DoD | **修改** | Gate 5 | 引用证据；真实 `[~]` 保持诚实 |

**不要**重建 `docs/handoff/*`。

---

## 2. D5.01 — `docs/desktop_testing.md` 大纲

语言切换；引言：本地优先、永不改原图、无 Rust 的 `verify` vs 需 GUI 主机的命令。

### 2.1 前置条件

- OS：Windows / macOS（主安装包）；Linux/WSL（开发 / 非安装包 DoD）
- 工具：Node 22、Python 3.11 venv、可选 rustc ≥1.88
- 链接：桌面 README、签名手册、Phase 2 workflow 清单

### 2.2 矩阵 — 生命周期

| 行 | 命令 / 动作 | 通过标准 |
| -- | ----------- | -------- |
| 启动 | `npm run dev:desktop` 或已安装应用 | 窗口 `FramePilot`；sidecar 回环；`GET /health` 200 |
| HTTP 冒烟 | `npm run test:desktop:smoke` | 退出码 0 |
| 干净退出 | 无活跃任务时关闭 | sidecar 退出；无残留 uvicorn |
| 导入中退出 | 导入进行中关闭 | 对话框路径见桌面 README；原图未动 |
| Sidecar 崩溃 | UI 打开时杀 sidecar | 可见失败；重启可恢复或文档说明重试 |
| 端口占用 | 目标端口冲突 | 明确错误；不绑定 `0.0.0.0` |

### 2.3 矩阵 — 导入 / 规模

| 行 | 命令 / 动作 | 通过标准 |
| -- | ----------- | -------- |
| 100 张合成路径导入 | `generate:synthetic` → 路径导入 | 任务完成；`originals/` 有副本；源未改 |
| 可选 500 / 2000 | `perf:api` | 记录规模；GUI 可选 / 待测 |
| 安装 / 卸载 | CI NSIS + DMG（或本地 `tauri build`） | 能启动一次；卸载移除应用（数据目录可保留 — 写明） |

### 2.4 矩阵 — 安全 / 网络

| 行 | 说明 |
| -- | ---- |
| 仅回环 | Sidecar 绑定 `127.0.0.1` |
| Origin / Host | `FRAMEPILOT_DESKTOP=1` 时桌面 Origin；经 LAN IP 访问**必须失败** |
| 项目根 | 自定义根仅经 D2.00 注册 |

### 2.5 要文档化的脚本（优先不加新脚本）

文档化现有：`dev:desktop`、`test:desktop:smoke`、`generate:synthetic`、`perf:api`、`packaging:sidecar`、`test:sidecar`、`verify`。

**可选别名（仅当评审需要）：** `"test:desktop:matrix": "npm run test:desktop:smoke"` — 否则跳过。

**提交：** `docs: add desktop test matrix`  
**§5.1：** D5.01 → `[x]`

---

## 3. D5.02 — 用户文档大纲

### 3.1 `docs/desktop_user_guide.md`

1. 桌面版是什么（本地优先；托管 sidecar）
2. 安装（NSIS / DMG；未签名警告 → 签名文档）
3. 首次启动（窗口标题；各 OS 数据目录；Settings 经 `/api/meta` 显示）
4. 创建项目 + 原生文件夹选择
5. 导入（路径导入；只复制不移动；每请求最多 100 文件）
6. 处理 → 筛选 → 导出；**打开导出文件夹** / reveal
7. 有任务时退出（摘要；对话框细节链桌面 README）
8. 开发继续用 **web**（`npm run dev`）vs 桌面壳
9. 链接：测试矩阵、已知限制、架构、Phase 2 workflow

### 3.2 README 修改

- 「Run Locally」后增加 **Desktop app** 小节：一段话 + 链到用户指南
- 贡献者 web 路径不变
- 保留未签名 CI 警告；链签名 + 用户指南

### 3.3 架构 / 桌面 README

- 架构：Deferred 去掉 desktop packaging；短注「Desktop shell」
- `apps/desktop/README.md`：安装包已由 CI 产出；指向用户指南

**提交：** `docs: add desktop install and data-dir instructions`  
**§5.1：** D5.02 → `[x]`

---

## 4. D5.03 — 性能说明大纲

在 `docs/v2_performance_baseline.md`（+ zh）增加 **Desktop path-import performance**：

| 字段 | 内容 |
| ---- | ---- |
| 主机 / 日期 | Dev 时填写 |
| 方法 | 100 张路径导入 + 处理；记 sidecar RSS（有 GUI 则记 UI） |
| 表列 | Count、Import s、Process s、Sidecar peak RSS MB、UI RSS 或 `pending` |
| 注意 | 无 WebView → UI `pending`；合成 JPEG ≠ 相机多样性 |

若 UI 为 `[~]`，在可行性笔记追加带日期条目。

**提交：** `docs: record desktop performance notes`  
**§5.1：** D5.03 → `[x]`（正文可写 UI pending，符合锁定决策 13）

---

## 5. D5.04 — 版本升级清单

1. `version.py` 中 `APP_VERSION = "2.1.0-desktop"` 作为 API 载荷真源  
2. 同步：`pyproject.toml`、根与 web/desktop `package.json`  
3. 新建双语 `CHANGELOG`：`2.1.0-desktop` RC；简述 `2.0.0-rc2` web 线  
4. 本 PR **不**打 `git tag`  
5. 测试：`test:api`、`verify`

**提交：** `release: 2.1.0-desktop rc`  
**§5.1：** D5.04 → `[x]`

---

## 6. D5.05 — 已知限制大纲

在已知限制文档新增 **Desktop 2.1** 节，打包计划必需要点：

- Sidecar 被杀 / 进程退出后任务不持久  
- 跳过 HEIC / RAW  
- 自动更新延期  
- 证书前安装包未签名（链签名手册）  
- WSL 可能无 GUI  
- 仅复制模式  
- 无独立预览窗  
- 无并发旋钮  
- 可选托盘延期（D3.06）

交叉链接用户指南与测试矩阵。

**提交：** `docs: document desktop 2.1 known limitations`  
**§5.1：** D5.05 → `[x]`

---

## 7. 设计章节 → 任务 → 提交对照

| 设计 § | 任务 | 提交 |
| ------ | ---- | ---- |
| §2 | D5.01 | `docs: add desktop test matrix` |
| §3 | D5.02 | `docs: add desktop install and data-dir instructions` |
| §4 | D5.03 | `docs: record desktop performance notes` |
| §5 | D5.04 | `release: 2.1.0-desktop rc` |
| §6 | D5.05 | `docs: document desktop 2.1 known limitations` |

Dev 顺序：D5.01 → D5.02 → D5.03 → D5.04 → D5.05（各一 issue + PR）。

---

## 8. Gate 3 —「可接受」检查清单

合并本设计并开始任何 Dev PR 之前，评审须确认：

- [ ] 范围符合打包 Phase 5（无 HEIC/RAW/XMP/托盘/更新器/Electron）
- [ ] 每个 D5.0x 有清晰文件列表与提交说明  
- [ ] 所有新建活文档有双语配对计划  
- [ ] 版本升级保持单一来源；不提前打 tag  
- [ ] D5.03 允许无 GUI 主机仅 sidecar + UI pending  
- [ ] DoD 全勾留给 Gate 5（设计不声称完成）  
- [ ] 设计 PR 本身不勾选 §5.1 的 D5.0x  

**接受记录：** 设计 PR 的 GitHub approval，**或**在 #81 / 评审议题上明确评论：`design accepted`。

---

## 9. 非目标（重复）

同研究 §5：无算法工作、不实现托盘、无 GUI 证据不把 D3.01–D3.03 升为 `[x]`、不在 D5.04 规定面外散落版本字面量。

# Phase 5 需求盘点（2026-08-29）

> Language: [English](2026-08-29-phase5-requirements.md) | **中文**

**总议题：** [#78](https://github.com/joe-cheung-cae/frame-pilot/issues/78)  
**本关：** [#79](https://github.com/joe-cheung-cae/frame-pilot/issues/79) — 仅需求研究  
**任务 id 真源：** [2026-08-18-desktop-packaging.zh.md](2026-08-18-desktop-packaging.zh.md) Phase 5 / §5.1

本文盘点 Phase 5 必须交付的内容。**不**撰写最终用户文档、**不**升版本、**不**勾选 D5.01–D5.05。

---

## 1. D5.01–D5.05 验收意图（来自打包计划）

| Id | 意图 | 依赖 | 计划主文件 | 提交说明 |
| ---- | ---- | ---- | ---------- | -------- |
| **D5.01** | 桌面测试矩阵文档 + 命令：启动/退出/sidecar 崩溃/端口占用；100 张合成 JPEG 路径导入；可选 500/2000（`perf:api`）；安装/卸载清单；Origin/CORS 说明（仅回环，LAN 不可达） | Phase 4 | `docs/desktop_testing.md`（+ zh），根 `package.json` 脚本（如需要） | `docs: add desktop test matrix` |
| **D5.02** | README + 用户文档：安装、首次启动、数据目录、只复制不移动、揭示导出文件夹、开发仍可用 web；架构文档在交付后不再把桌面标为延期 | D5.01 | `README.md`（+ zh）、`docs/desktop_user_guide.md`（+ zh）、已知限制/架构交叉引用 | `docs: add desktop install and data-dir instructions` |
| **D5.03** | 一次 100 张路径导入 + 处理的 sidecar（及若有 GUI 则 UI）RSS；无 GUI 则仅 sidecar 并标注 UI 待测 | D2.08（已完成） | 可行性笔记和/或 `docs/v2_performance_baseline.md`（+ zh） | `docs: record desktop performance notes` |
| **D5.04** | 版本升到 `2.1.0-desktop` RC；单一来源 `apps/api/app/core/version.py`；更新 `pyproject.toml` 与两个 `package.json`；changelog；在 verify + 桌面 CI 产物存在前不打 tag | Phase 0–4 验收 | `version.py`、`apps/api/pyproject.toml`、根与 web/desktop `package.json`、changelog | `release: 2.1.0-desktop rc` |
| **D5.05** | 桌面 2.1 已知限制：sidecar 被杀后任务不持久；跳过 HEIC/RAW；自动更新延期；未签名直至证书；WSL 可能无 GUI；仅复制模式；无独立预览窗；无并发旋钮；托盘延期（D3.06） | D5.02 | `docs/v2_known_limitations.md`（+ zh） | `docs: document desktop 2.1 known limitations` |

Phase 5 / 产品 DoD 勾选框见下文 §3。

---

## 2. 现有资产盘点

### 脚本（根 `package.json`）

| 脚本 | 对 Phase 5 的作用 |
| ---- | ----------------- |
| `dev:desktop` | 启动 Tauri + sidecar（主机需 rustc ≥1.88） |
| `test:desktop:smoke` | HTTP 冒烟：sidecar health + 项目列表 |
| `perf:api` | API 性能冒烟；可含 100/500/2000 |
| `generate:synthetic` | 合成 JPEG，供路径导入矩阵行 |
| `packaging:sidecar` / `test:sidecar` | PyInstaller 构建 + sidecar 冒烟 |
| `verify` | 无 Rust 门槛 |
| `check:markdown-links` | 双语活文档与相对链接检查 |
| `check:pretag` | verify + 验证决策（web 发布线） |

尚无 `docs/desktop_testing.md` 或 `docs/desktop_user_guide.md`。

### 已有文档

| 路径 | 相对 Phase 5 的缺口 |
| ---- | ------------------- |
| [tests/desktop/workflow.md](../../tests/desktop/workflow.md) | Phase 2 GUI 清单；仍写 `2.0.0-rc2`；不是完整 Phase 5 矩阵 |
| [apps/desktop/README.md](../../apps/desktop/README.md) | 开发壳/数据目录/退出语义；仍写安装包等到 Phase 4（相对已完成的 Phase 4 过时） |
| [docs/desktop_signing.md](../desktop_signing.md) | 首个 RC 可用未签名 CI；签名为后续 |
| [docs/desktop_feasibility_notes.md](../desktop_feasibility_notes.md) | Phase 0–4 测量；无 rustc 1.88 的 WSL 上 GUI/`cargo` 为 `[~]` |
| [docs/v2_performance_baseline.md](../v2_performance_baseline.md) | Web/API 基线；**尚无桌面 WebView / sidecar 路径导入 RSS 行** |
| [docs/v2_known_limitations.md](../v2_known_limitations.md) | 偏 v2.0 web；**缺 D5.05 桌面 2.1 条目清单** |
| [docs/v2_architecture.md](../v2_architecture.md) | Deferred 中仍列 **desktop packaging** |
| [README.md](../../README.md) | 以 web 为主；有未签名安装包提示；**无安装/首次启动/桌面数据目录用户指南** |
| Changelog | 仓库中**尚无**；D5.04 需按计划新增 |

### 版本面（当前）

- 真源：`apps/api/app/core/version.py` → `APP_VERSION = "2.0.0-rc2"`
- 根 `package.json` 亦为 `2.0.0-rc2`；打包计划要求仅在 D5.04 同步 `pyproject.toml` 与两个应用 `package.json`
- 锁定决策 15：不散落版本字面量

### 已在 `main` 上的 CI 证据

- `.github/workflows/desktop.yml` 构建 Windows NSIS + macOS DMG（未签名）
- Phase 4 验收引用 [desktop.yml run 33170731977](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/33170731977)

---

## 3. Phase 5 DoD 相对当前 `main`

| DoD 项 | `main` 上状态 | Phase 5 仍需 |
| ------ | ------------- | ------------ |
| Windows / macOS 安装包存在 | **已有**（桌面 CI） | 收尾时在跟踪表引用 Actions 运行 |
| 应用启动管理 sidecar，无需自跑 uvicorn | **已有** | 写入用户指南 / 矩阵 |
| 原生文件夹选择与拖放导入 | **已实现**；部分主机 live GUI 可能 `[~]` | 文档化；未验证处保持诚实 |
| 核心工作流与 v2 一致 | API / 共享 UI **已有**（D2.08） | 矩阵与用户指南交叉链接 |
| 原图永不修改 | **已有** | 用户文档重申 |
| 500 张 API 路径导入；若测过则记 500 GUI | API 侧有覆盖；**500 GUI 常未测** | 矩阵可选 `perf:api`；GUI 行可待定 |
| 用户 + 开发者文档存在 | **部分** | **缺口在 D5.01–D5.02** |
| CI 双平台安装包；签名可待定 | **已有** / 签名按设计延期 | D5.05 + 签名手册 |
| 回环 + Host/Origin | **已有** | 矩阵 CORS/LAN 说明 |
| 自定义项目根仅经 D2.00 | **已有** | 用户指南 / 限制 |

---

## 4. D5.03 的 GUI / 主机限制

锁定决策 13：无法跑 WebView/GUI 时标 `[~]`。

无 rustc ≥1.88 / 无显示的主机（常见 WSL agent）：

- D5.03 可只记录 **sidecar** 在 100 张路径导入 + 处理下的 RSS
- **UI / WebView RSS 标为待测**，在可行性或性能基线写日期备注
- **不得编造** GUI 数字

D3.01–D3.03 的 live GUI 仍为 `[~]`；Phase 5 不得假装已是 `[x]`。

---

## 5. 非目标（Phase 5）

- HEIC / RAW 解码、XMP、本地神经网络模型
- 云更新 / 自动更新上线
- 改用 Electron
- 实现可选托盘（D3.06 保持延期；由 D5.05 记录）
- 无真实 GUI/`cargo` 运行就把 D3.01–D3.03 从 `[~]` 升为 `[x]`
- 在 D5.04 规定面之外散落 `2.1.0-desktop` 字面量
- 重开已关闭的 PR #27 / #67–#76 后续工作

---

## 6. 建议关卡顺序（提醒）

1. 本研究（Gate 1）→ 合并  
2. 文档设计（Gate 2）→ 评审循环（Gate 3）直至接受  
3. Dev PR：D5.01 → D5.02 → D5.03 → D5.04 → D5.05  
4. 收尾：勾选 DoD + 关闭总议题 #78  

**硬门禁：** 文档设计被明确接受并合并前，不实施任何 D5.0x。

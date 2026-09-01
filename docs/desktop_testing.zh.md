# 桌面测试矩阵

> 语言：[English](desktop_testing.md) | **中文**

FramePilot 桌面（`2.1.0-desktop` 轨道）的手工与命令检查清单。本地优先：永不修改或删除相机原图。优先使用 `{root_path}/originals` 下的项目副本。

`npm run verify` 是无 Rust 的 CI 门槛（lint、typecheck、测试、产物检查、验证决策）。它**不会**打开 WebView，也不会跑 `cargo`/`tauri`。GitHub Actions（`.github/workflows/verify.yml`）另有独立的 **Playwright E2E** 作业（`npm run test:e2e`：mocked E2E 加上 `tests/e2e/real-local-smoke.spec.ts`）、独立的 **100 张真实浏览器** 作业（`npm run test:e2e:real-browser`；不含 `test:e2e:real-browser:large`），以及独立的**冻结 sidecar `/health`** 作业：先 `npm run packaging:sidecar`，再 `npm run test:sidecar`。冻结冒烟会 `unset PYTHONPATH`（与打包后的 Tauri spawn 一致）。`.github/workflows/desktop.yml` 在 PyInstaller 之后跑同一冒烟，且**不**启动打包 GUI。workflow YAML 不需要单独的 `check:pretag` 作业；`npm run verify` 已包含 `check:validation-decision`。GUI 行需要 rustc ≥1.88（以及显示环境）。未验证的 GUI 行标为带日期的 `[~]`，并写主机说明——**不要编造**通过结果。

**相关：** [桌面壳 README](../apps/desktop/README.md) · [签名手册](desktop_signing.zh.md) · [Phase 2 工作流清单](../tests/desktop/workflow.md) · [Phase 5 设计](plans/2026-08-29-phase5-docs-design.zh.md)

---

## 前置条件

| 项 | 说明 |
| -- | ---- |
| OS | **Windows / macOS** — 主安装包目标（NSIS / DMG，见 `.github/workflows/desktop.yml`）。**Linux / WSL** — 适合 API/sidecar/开发；安装包 DoD 不要求 Linux 包。 |
| Node | 22.x（见仓库 CI） |
| Python | 3.11 venv（`npm run install:all`） |
| Rust（仅 GUI） | rustc / cargo ≥1.88 才能 `npm run dev:desktop` / `tauri build`。缺工具链 → 跳过 GUI 行；保留 HTTP 冒烟。 |
| 数据 | 源照片使用应用数据目录**之外**的临时文件夹。 |

---

## 常用命令

| 脚本 | 用途 |
| ---- | ---- |
| `npm run dev:desktop` | Tauri + Vite + sidecar（需 Rust） |
| `npm run test:desktop:smoke` | HTTP 冒烟：sidecar health + `/api/projects` |
| `npm run generate:synthetic -- --output <dir> --count <n>` | 合成 JPEG，供路径导入行 |
| `npm run perf:api -- --output <dir> --counts 100 500 2000` | 可选 API 规模 multipart 导入/处理冒烟（非 `from-paths`） |
| `npm run packaging:sidecar` | PyInstaller one-dir sidecar（CI 冻结 `/health` 作业先构建此项） |
| `npm run test:sidecar` | Sidecar ready-line 冒烟；冻结二进制会 `unset PYTHONPATH` |
| `npm run test:e2e` | Playwright mocked E2E 加上 real-local-smoke（CI 默认门禁；不含大规模真实浏览器） |
| `npm run test:e2e:real-browser` | 100 张生成 JPEG 走 Chromium + 真实后端（CI 默认门禁；不含大规模） |
| `npm run verify` | 无 Rust 全量校验（含产物检查 + 验证决策） |

本矩阵**不需要**额外 npm 别名；直接使用上表脚本。

---

## 矩阵 — 生命周期

| 行 | 命令 / 动作 | 通过标准 | 可自动化？ |
| -- | ----------- | -------- | ---------- |
| 启动（开发） | `npm run dev:desktop` | 窗口标题 `FramePilot`；sidecar 回环；`GET /health` → 200 且含 `version` + `service` | 手工 GUI |
| 启动（安装包） | 启动 CI 或本地 `tauri build` 的 NSIS/DMG | 同上，且无需自跑 uvicorn | 手工 |
| HTTP 冒烟 | `npm run test:desktop:smoke` | 退出码 0 | 是 |
| 冻结 sidecar `/health` | 先 `npm run packaging:sidecar`，再 `npm run test:sidecar` | 退出码 0；冻结 `GET /health` 且 `unset PYTHONPATH` | 是（CI） |
| Playwright E2E | `npm run test:e2e` | 退出码 0；mocked E2E 加上 `real-local-smoke` | 是（CI） |
| Playwright 真实浏览器（100 张） | `npm run test:e2e:real-browser` | 退出码 0；100 张生成 JPEG，Chromium | 是（CI） |
| 干净退出 | 无活跃导入/处理任务时关窗 | sidecar 退出；该端口无残留 uvicorn | 手工 GUI |
| 导入中退出 | 活跃导入时关闭 | 对话框见 [apps/desktop/README.md](../apps/desktop/README.md)；源原图未改 | 手工 GUI |
| Sidecar 崩溃 | UI 打开时杀 sidecar | UI 显示失败/不可达；重启可恢复或文档说明重试；原图未动 | 手工 |
| 端口占用 | 目标回环端口冲突 | 明确错误；**不得**监听 `0.0.0.0` | 手工 / 备注 |

---

## 矩阵 — 导入 / 规模

| 行 | 命令 / 动作 | 通过标准 | 可自动化？ |
| -- | ----------- | -------- | ---------- |
| 100 张合成路径导入 | `npm run generate:synthetic -- --output /tmp/fp-synth-100 --count 100`，再经桌面「选择文件夹」或 `POST .../imports/from-paths`（每片 ≤100，同一 `job_id`，最后一片 `finalize`） | 任务 `complete`（或仅因不支持格式 `complete_with_errors`）；`{root_path}/originals` 有副本；源 size/mtime/字节不变 | 部分（API 覆盖不可变；GUI 选择器可为 `[~]`） |
| 100 张 from-paths RSS | `npm run perf:api -- --output /tmp/fp-from-paths-100 --count 100 --import-mode from-paths` | 记入性能基线；不崩溃；原图不变 | 是（API） |
| 可选 500 | `npm run perf:api -- --output /tmp/fp-perf --counts 500` | 跑过后写入性能说明；不崩溃。multipart `/import`（规模）或加 `--import-mode from-paths` | 是（API） |
| 可选 2000 | `npm run perf:api -- --output /tmp/fp-perf --counts 2000` | 同上；默认**不要求** 2000 GUI 审片 | 是（API） |
| 完整筛选工作流 | 按 [tests/desktop/workflow.md](../tests/desktop/workflow.md) | 导入 → 处理 → 键盘筛选 → CSV/ZIP/文件夹导出 + reveal | 手工 / API pytest |
| 安装 / 卸载 | 安装 CI 的 Windows NSIS 或 macOS DMG；启动一次；卸载 | 应用二进制已移除；**数据目录可保留**（需告知用户）— 路径见 [apps/desktop/README.md](../apps/desktop/README.md) | 手工 |

---

## 矩阵 — 安全 / 网络

| 行 | 说明 | 通过标准 |
| -- | ---- | -------- |
| 仅回环 | Sidecar 绑定 `127.0.0.1` | 不在 LAN / `0.0.0.0` 上监听 |
| Origin / Host | `FRAMEPILOT_DESKTOP=1` 启用 Tauri Origin；Host 拒绝非回环 | 从其他设备访问 `http://<LAN-IP>:<port>` **失败**；本机桌面 UI 可用 |
| CORS / LAN | 桌面不是局域网相册服务 | 文档写明 LAN 访问按设计不可用 |
| 项目根 | 自定义项目文件夹仅经 D2.00（`POST /api/desktop/project-roots`） | 白名单外路径被拒；不允许把 `$HOME` / 盘符根设为白名单 |

---

## 建议记录模板

跑 GUI 或安装包时记录：

- 日期 / OS / `APP_VERSION`（来自 `GET /health`）
- 哪些行为 `[x]`，哪些为带日期的 `[~]`
- 若用安装包，记下 CI 产物运行 URL（Actions → `desktop`）
- 确认源原图未被修改

不要提交照片、数据库或导出目录。

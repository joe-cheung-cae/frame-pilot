# 更新日志

> 语言：[English](CHANGELOG.md) | **中文**

此处列出 FramePilot 的重要版本。API 版本字符串来自 `apps/api/app/core/version.py`（`APP_VERSION`）。`apps/api/pyproject.toml` 中的 Python 包版本使用 PEP 440 本地形式 `2.1.0+desktop`，以便可编辑安装合法。

## 未发布

### CI — 冻结 sidecar `/health` 门槛

- `.github/workflows/verify.yml` 在 pull request 与 `main` 上跑独立作业：先 `npm run packaging:sidecar`，再 `npm run test:sidecar`（冻结 `GET /health`，且 `unset PYTHONPATH`）
- `.github/workflows/desktop.yml` 在 PyInstaller 之后跑同一冒烟，仍不启动打包 GUI、也不签名安装包
- `scripts/sidecar-smoke.sh` 的残留进程检查只标记 sidecar/uvicorn（Linux 上 `pgrep -P $$` 会把自己也列进去）

### 第 6.1 阶段 — 作业回收默认开启

- `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP` 现在默认**开启**；设为 `0`/`false`/`no`/`off` 可退回失败并重试的启动行为
- 桌面退出文案更新，反映回收为默认行为，并为显式关闭的场景提供文案

### 第六阶段 — 持久本地作业回收（可选）

- 通过 `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=1` 可选启动回收（默认曾为失败并重试；已在上方第 6.1 阶段翻转）
- `JobRead` 上的检查点/租约字段；可回收残留使用状态 `interrupted`
- 本地 worker 入口：`npm run worker` / `python -m app.worker`
- 桌面退出文案与回收 vs 失败并重试对齐

## 2.1.0-desktop（RC）

桌面打包轨道的发布候选。

- Tauri 2 桌面壳 + 本机回环 Python sidecar（终端用户无需自跑 uvicorn）
- 原生文件夹/文件选择与路径导入（复制到项目 `originals/`；永不修改原图）
- 经 CI 产出 Windows NSIS 与 macOS DMG（内部测试可为**未签名**；见 [docs/desktop_signing.zh.md](docs/desktop_signing.zh.md)）
- `docs/` 下的桌面用户指南、测试矩阵与性能说明
- 贡献者 web 工作流（`npm run dev`）不变

在配置证书之前，不要把本 RC 当作已签名的商店级公开发布。

## 2.0.0-rc2

本地 web MVP-plus 基础：基于任务的导入/处理、筛选工作区、CSV/ZIP/文件夹导出，以及 Tier B 真实世界验证证据。桌面打包推迟到 2.1.0-desktop 轨道。

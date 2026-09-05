# 更新日志

> 语言：[English](CHANGELOG.md) | **中文**

此处列出 FramePilot 的重要版本。API 版本字符串来自 `apps/api/app/core/version.py`（`APP_VERSION`）。`apps/api/pyproject.toml` 中的 Python 包版本使用 PEP 440 本地形式 `2.1.0+desktop`，以便可编辑安装合法。

## 未发布

### 第九阶段 — S9.01 导出作业取消

- 现有 `POST /api/projects/{project_id}/jobs/{job_id}/cancel` 路由上的协作式导出取消（queued/running 持久化 `cancellation_requested` 并返回 202；终态 200 空操作；interrupted 终态 `cancelled`）
- 创建导出同时持久化 `job_type="export"` 的 `ProcessingJob`，id 与 `ExportRecord` 相同
- 检查点中止 CSV/ZIP/文件夹写入；项目导出根下的不完整产物走 fail-and-cleanup；永不修改或删除原片
- 桌面退出可 **退出并取消导出**（POST cancel，最多等 10 秒，再 SIGTERM）
- 导出作业启动时仍不回收；进行中分组的暂停/恢复未实现
- 不改 `APP_VERSION`、不签名、不打包 GUI

### 文档 — 排期剩余 stretch（S9.00）

- 在 `develop_plan.zh.md` §1.1 点名第九阶段剩余 stretch 收口（每次运行一个 GitHub issue；不要发明第十阶段）
- 活计划：`docs/plans/2026-09-04-remaining-stretch.zh.md`；总览 [#160](https://github.com/joe-cheung-cae/frame-pilot/issues/160)；下一个产品 issue 是 S9.01 导出取消（[#164](https://github.com/joe-cheung-cae/frame-pilot/issues/164)）
- S9.00 不改 `APP_VERSION`、不签名、不改产品行为

### 文档 — 桌面壳双语页

- 为 `apps/desktop/README.md` 和 `tests/desktop/workflow.md` 补中文对应页
- markdown 链接检查现在会扫这些活页

### 第八阶段 — HEIC 预览

- 本地 HEIC/HEIF 静帧导入，用 `pillow-heif` 解码，WebP 缩略图/预览，在解码 RGB 上评分/分组
- 原始 HEIC 字节拷进 `originals/` 并导出（ZIP 使用 `ZIP_STORED`）；永不修改源文件
- 垃圾 HEIC 在拷贝后只让该文件失败；RAW、AVIF、Live Photo `.mov`、HDR gain-map 色调映射和 XMP 不在本切片
- 冻结 sidecar 收集 `pillow_heif` / libheif；wheel 带 LGPL libheif（写在已知限制里）
- 不升 `APP_VERSION`、不签名、不跑打包 GUI

### 第七阶段 — 处理作业取消

- 现有 `POST /api/projects/{project_id}/jobs/{job_id}/cancel` 路由上的协作式处理取消（queued/running 持久化 `cancellation_requested` 并返回 202；终态 200 空操作；interrupted 终态 `cancelled` 并清分组）
- worker 在检查点终态化后清分组：照片回到 `imported`；保留 `user_status` / `star_rating` 与导入衍生件；永不修改或删除原图
- 处理 UI 可请求 **Cancel Grouping and Ranking** 并显示检查点文案
- 桌面退出可 **Quit and cancel processing**（POST cancel，最多等 10 秒，再 SIGTERM）
- 回收尊重已请求的处理取消，不重新入队
- 导出取消仍为 422；进行中分组的暂停/恢复未实现
- 不升 `APP_VERSION`、不签名、不跑打包 GUI

### 桌面 — 直接依赖 @tauri-apps/api/webview（L4）

- `apps/desktop/package.json` 现将 `@tauri-apps/api` 列为直接依赖，使 `nativeFs.ts` 导入 `@tauri-apps/api/webview` 不再依赖插件传递安装
- 不含版本号提升、签名、打包 GUI 或自动更新

### 桌面 — 非 Tauri 时 getNativeFs() 返回 null（L3）

- 桌面 `getNativeFs()` 在 `window` 既没有 `__TAURI_INTERNALS__` 也没有 `__TAURI__` 时返回 `null`，与 D2.01 web stub 对齐
- 用普通浏览器打开桌面 Vite 时不再走随后会在插件调用上失败的原生选择器分支
- 不含 L4（`@tauri-apps/api/webview` 直接依赖）、版本号提升、签名、打包 GUI 或自动更新

### 桌面 — 注册项目根时按名拒绝家目录（L2）

- `register_root` 现按名拒绝 `Path.home()` / `$HOME`，包括 Linux/WSL desktop-dev 把 `data_dir` 放在仓库下而不是 home 下的情况
- 家目录的子目录仍可注册；放宽路径仍是 D2.00 注册
- 不含 L3（`getNativeFs` 从不返回 null）或 L4（`@tauri-apps/api/webview` 直接依赖）、版本号提升、签名、打包 GUI 或自动更新

### 桌面 — sidecar spawn 剥离继承的项目根 allowlist（L1）

- Tauri sidecar spawn 会 `env_remove` `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST`，避免父 shell（例如 `tauri dev`）把宽 allowlist 泄漏进 sidecar
- 放宽路径仍是 D2.00 注册；API 侧 M1 对残留 env 条目的过滤不变
- 不含 L2–L4、版本号提升、签名、打包 GUI 或自动更新

### CI — 桌面 HTTP 冒烟门禁

- `.github/workflows/verify.yml` 在 pull request 与 `main` 上跑独立作业：`npm run test:desktop:smoke`（`tests/desktop/smoke.sh`：sidecar ready 行、`GET /health`、`GET /api/projects`、桌面 Origin CORS preflight、攻击者 `Host` → 403）
- 没有冻结二进制时使用 venv sidecar。仅 HTTP：不启动打包的 NSIS/DMG GUI，也不增加代码签名 / 公证
- 大规模真实浏览器（`test:e2e:real-browser:large`）仍为可选，不纳入默认门禁
- `tests/desktop/smoke.sh` 的残留进程检查只标记 sidecar/uvicorn（Linux 上 `pgrep -P $$` 会把自己也列进去）

### CI — 验证决策默认门禁

- `npm run verify` 现已包含 `npm run check:validation-decision`（`scripts/check-validation-decision.sh` / `docs/v2_rc2_validation_decision.md`）
- 在 `main` @ `1b6c15b1ca4faca4366a7b9a9d105b1b7c1d4961` 上核对：决策文件已完成且笔记存在，该子集不会误红
- GitHub Actions workflow YAML 未改；该检查随现有 `verify` 作业一起跑。不需要单独的 `check:pretag` 作业
- `npm run check:pretag` 仍是发布时间命令（`verify` 加上同一验证决策检查）
- 大规模真实浏览器（`test:e2e:real-browser:large`）仍为可选，不纳入默认门禁

### CI — Playwright E2E 门槛

- `.github/workflows/verify.yml` 在 pull request 与 `main` 上跑独立作业：`npm run test:e2e`（Playwright mocked E2E 加上 `tests/e2e/real-local-smoke.spec.ts`）
- `.github/workflows/verify.yml` 另跑独立作业：`npm run test:e2e:real-browser`（100 张生成 JPEG，Chromium）
- 大规模真实浏览器（`test:e2e:real-browser:large`，500/1000/2000）仍为可选，不纳入默认门禁
- 这些 E2E 作业不启动打包的 NSIS/DMG GUI，也不增加代码签名 / 公证
- Mocked 筛选 E2E 现在会先断言首页加载（`0/500 loaded reviewed` 以及 `500 of 501 loaded`），再点 Load all photos
- Playwright 在 CI 中使用单个 worker，避免 real-local-smoke 与真实浏览器 smoke 并行共用 E2E API 数据目录

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

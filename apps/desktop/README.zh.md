# FramePilot 桌面壳

> 语言：[English](README.md) | **中文**

Tauri 2 + Vite SPA，通过 HTTP 复用 `apps/web` 组件，对接本地 Python sidecar。

## 开发

从仓库根目录运行 `npm run dev:desktop` 会启动 `tauri dev`，它会：

1. 经 `beforeDevCommand` 在端口 **1420** 跑 Vite（`strictPort: true`）。
2. 拉起 sidecar，分配回环 `--port <n>`（从不用 `--port 0`），绝对 `--data-dir`，以及 `FRAMEPILOT_DESKTOP=1`。Spawn 还会 `env_remove` `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST`，避免父 shell（例如 `tauri dev`）把过宽的 allowlist 漏进 sidecar。
3. 在 UI 加载前注入 `window.__FRAMEPILOT_API_BASE__` 和 `window.__FRAMEPILOT_DESKTOP__ = true`。

在普通浏览器打开 Vite URL（没有 Tauri）时，`getNativeFs()` 返回 `null`，与 web stub 一致，因此不会用原生选择器。

需要用户空间的 Rust 工具链（`rustup`）。缺少 `cargo`/`rustc` 时脚本会打印明确错误并以 1 退出。不要从本仓库安装 brew/apt 的 Rust。

Windows NSIS 和 macOS DMG 安装包由 `.github/workflows/desktop.yml` 产出（未签名，供内部测试）。最终用户步骤：[桌面用户指南](../../docs/desktop_user_guide.zh.md)。签名：[桌面代码签名手册](../../docs/desktop_signing.zh.md)。手工矩阵：[桌面测试矩阵](../../docs/desktop_testing.zh.md)。

## 数据目录

- 打包后：macOS `~/Library/Application Support/FramePilot`；Windows `%APPDATA%\FramePilot`；Linux `~/.local/share/FramePilot`
- 开发：仓库 `.framepilot-desktop-dev`（已 gitignore）
- 打包运行从不用相对 CWD 的 `.framepilot-data`

用绝对路径的 `FRAMEPILOT_DATA_DIR` 覆盖。Sidecar stderr 追加到 `{data_dir}/logs/sidecar.log`。

## 验证

`npm run verify` 会对桌面 Vite 应用做类型检查（`typecheck:desktop`），**不得**调用 `rustc`、`cargo` 或 Tauri。`install:all` 已经会安装 `apps/desktop`。

## 有任务时退出

关闭窗口时若有活跃导入，显示继续工作 / 退出并取消导入 / 仍要退出。取消复用 `POST /api/projects/{id}/jobs/{job_id}/cancel`，最多等 10 秒，再 SIGTERM。活跃分组/排序任务则显示继续工作 / 退出并取消处理 / 仍要退出，同样是 POST cancel + 最多 10 秒等待 + SIGTERM。仍要退出会对 sidecar 发 SIGTERM，5 秒后杀掉。

下次启动时，残留导入/处理任务默认变为 `interrupted` 并自动回收（第六阶段 6.1，[#105](https://github.com/joe-cheung-cae/frame-pilot/issues/105)）。在环境里设 `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0`（sidecar 会继承）则改为把残留活跃任务标为 **failed**，以便手动重试。永不修改原图。见 [第六阶段计划](../../docs/plans/2026-08-29-phase6-durable-jobs.zh.md)。

HTTP 冒烟：从仓库根目录 `npm run test:desktop:smoke`（PR 和 `main` 的默认 CI 门）。该冒烟不含 WebView 渲染对话框。

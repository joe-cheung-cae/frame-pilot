# FramePilot 桌面打包实施计划

> 语言：[English](2026-08-18-desktop-packaging.md) | **中文**

> **给 Grok / Claude Goal Mode：** 必需子技能：使用 `superpowers:executing-plans`（或本文的循环）**一次只实现一个 task id**。在当前任务已实现、测试、审阅并提交之前，不要开始下一个任务。
>
> **Opus 5 审阅（2026-08-18）：** 结论已并入本计划；原审阅文件已作为冗余删除。从 **D0.00** 开始。状态见 §5.1。

**目标：** 将 FramePilot 发布为可安装的 Windows 与 macOS 桌面应用：自动启动本地 Python sidecar，复用当前 v2.0.0-rc2 筛选工作流，且永不修改原图。

**架构：** 把现有 FastAPI + SQLite 后端作为仅监听 localhost 的 sidecar。保留 `apps/web` 作为浏览器 / E2E 前端。新增 `apps/desktop`：Tauri 2 壳 + 复用 `apps/web/src/components` 与 `apps/web/src/lib` 的 Vite SPA。通过运行时注入的端口，经 `http://127.0.0.1:<port>` 与 sidecar 通信。增加分块的基于路径导入 API，使原生文件夹选择器不必经浏览器 File API 再上传成千上万张照片字节。

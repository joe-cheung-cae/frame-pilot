# FramePilot 桌面打包实施计划

> 语言：[English](2026-08-18-desktop-packaging.md) | **中文**

> **给 Grok / Claude Goal Mode：** 必需子技能：使用 `superpowers:executing-plans`（或本文的循环）**一次只实现一个 task id**。在当前任务已实现、测试、审阅并提交之前，不要开始下一个任务。
>
> **Opus 5 审阅（2026-08-18）：** 结论已并入本计划；原审阅文件已作为冗余删除。从 **D0.00** 开始。状态见 §5.1。

**目标：** 将 FramePilot 发布为可安装的 Windows 与 macOS 桌面应用：自动启动本地 Python sidecar，复用当前 v2.0.0-rc2 筛选工作流，且永不修改原图。

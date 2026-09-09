# FramePilot 2.1.0-desktop（未签名）

> 语言：[English](desktop_unsigned_release_notes.md) | **中文**

本 GitHub Release 从现有 `desktop` 工作流发布**未签名**的 Windows NSIS 与 macOS DMG 安装包。

这些安装包是**未签名**的。它们**不是** Authenticode 签名、**不是** Apple 公证、**不是** Gatekeeper 干净、**不是** SmartScreen 干净，也**不是**商店上架。Windows 可能显示**未知发布者** / SmartScreen。macOS 可能显示**无法打开，因为无法验证开发者**。这些对话框是预期现象。

**安装教程：** [未签名桌面安装教程](desktop_install.zh.md) · [English](desktop_install.md)

在 GitHub.com 上使用：

- https://github.com/joe-cheung-cae/frame-pilot/blob/main/docs/desktop_install.md
- https://github.com/joe-cheung-cae/frame-pilot/blob/main/docs/desktop_install.zh.md

## 资源

只从本 Release 下载安装文件：

- Windows：`FramePilot_2.1.0-desktop_x64-setup.exe`（NSIS，x64）
- macOS：`FramePilot_2.1.0-desktop_aarch64.dmg`（Apple Silicon / `aarch64`）

**不要**安装残留 GUI 证据 zip（`FramePilot-desktop-500-gui-*`、`FramePilot-desktop-quit-job-*`）。那些是测试日志，不是安装程序。

**Help → Check for updates** 不会下载或安装。请按教程从本 Release（或后续未签名 Release）安装更新的未签名构建。

这不是已签名的公开商店发行。不要把它当成 Gatekeeper 干净。

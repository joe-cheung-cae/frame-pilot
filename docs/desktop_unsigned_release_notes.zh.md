# FramePilot 2.1.1-desktop（未签名）

> 语言：[English](desktop_unsigned_release_notes.md) | **中文**

本 GitHub Release 从现有 `desktop` 工作流发布**未签名**的 Windows NSIS 与 macOS DMG 安装包。

这些安装包是**未签名**的。它们**不是** Authenticode 签名、**不是** Apple 公证、**不是** Gatekeeper 干净、**不是** SmartScreen 干净，也**不是**商店上架。Windows 可能显示**未知发布者** / SmartScreen。macOS 可能显示**无法打开，因为无法验证开发者**。这些对话框是预期现象。

本版含 [#191](https://github.com/joe-cheung-cae/frame-pilot/pull/191) Windows sidecar ready-line 修（Windows 启动预算 120 秒、`{data_dir}/logs/sidecar.ready` 回退、spawn 工作目录 / `CREATE_NO_WINDOW` / 无缓冲 stdio）。Win11 冷首启**不要**再用 `v2.1.0-desktop`。

**安装教程：** [未签名桌面安装教程](desktop_install.zh.md) · [English](desktop_install.md)

在 GitHub.com 上使用：

- https://github.com/joe-cheung-cae/frame-pilot/blob/main/docs/desktop_install.md
- https://github.com/joe-cheung-cae/frame-pilot/blob/main/docs/desktop_install.zh.md

## 资源

只从本 Release 下载安装文件：

- Windows：`FramePilot_2.1.0-desktop_x64-setup.exe`（NSIS，x64）
- macOS：`FramePilot_2.1.0-desktop_aarch64.dmg`（Apple Silicon / `aarch64`）

文件名仍带 `2.1.0-desktop`，因为没有改 `APP_VERSION`。Release tag 是 `v2.1.1-desktop`。

**不要**安装残留 GUI 证据 zip（`FramePilot-desktop-500-gui-*`、`FramePilot-desktop-quit-job-*`）。那些是测试日志，不是安装程序。

**Help → Check for updates** 不会下载或安装。请按教程从本 Release（或后续未签名 Release）安装更新的未签名构建。

这不是已签名的公开商店发行。不要把它当成 Gatekeeper 干净。

## Windows 11 冷首启

1. 从**本** Release（`v2.1.1-desktop`）安装 NSIS `.exe`，不要用 `v2.1.0-desktop`。
2. **不要**预先运行 `%LOCALAPPDATA%\FramePilot\framepilot-api\framepilot-api.exe`。
3. 从开始菜单启动 **FramePilot**。最多等两分钟。
4. 通过：窗口标题 `FramePilot`，项目 UI，没有 `timed out waiting for sidecar ready line`。

# FramePilot 2.1.2-desktop（未签名）

> 语言：[English](desktop_unsigned_release_notes.md) | **中文**

本 GitHub Release 从现有 `desktop` 工作流发布**未签名**的 Windows NSIS 与 macOS DMG 安装包。

这些安装包是**未签名**的。它们**不是** Authenticode 签名、**不是** Apple 公证、**不是** Gatekeeper 干净、**不是** SmartScreen 干净，也**不是**商店上架。Windows 可能显示**未知发布者** / SmartScreen。macOS 可能显示**无法打开，因为无法验证开发者**。这些对话框是预期现象。

本版含 [#195](https://github.com/joe-cheung-cae/frame-pilot/pull/195) / [#194](https://github.com/joe-cheung-cae/frame-pilot/issues/194) Win11 新建工程导入/导出修（新建后 File → Import/Export 与工作流选项卡会打开 Import Images / Export Selection），以及此前 [#191](https://github.com/joe-cheung-cae/frame-pilot/pull/191) Windows sidecar ready-line 修（Windows 启动预算 120 秒、`{data_dir}/logs/sidecar.ready` 回退、spawn 工作目录 / `CREATE_NO_WINDOW` / 无缓冲 stdio）。Win11 冷首启**不要**再用 `v2.1.0-desktop`。验新建工程导入/导出**不要**用 `v2.1.1-desktop`。

**安装教程：** [未签名桌面安装教程](desktop_install.zh.md) · [English](desktop_install.md)

在 GitHub.com 上使用：

- https://github.com/joe-cheung-cae/frame-pilot/blob/main/docs/desktop_install.md
- https://github.com/joe-cheung-cae/frame-pilot/blob/main/docs/desktop_install.zh.md

## 资源

只从本 Release 下载安装文件：

- Windows：`FramePilot_2.1.0-desktop_x64-setup.exe`（NSIS，x64）
- macOS：`FramePilot_2.1.0-desktop_aarch64.dmg`（Apple Silicon / `aarch64`）

文件名仍带 `2.1.0-desktop`，因为没有改 `APP_VERSION`。Release tag 是 `v2.1.2-desktop`。

**不要**安装残留 GUI 证据 zip（`FramePilot-desktop-500-gui-*`、`FramePilot-desktop-quit-job-*`）。那些是测试日志，不是安装程序。

**Help → Check for updates** 不会下载或安装。请按教程从本 Release（或后续未签名 Release）安装更新的未签名构建。

这不是已签名的公开商店发行。不要把它当成 Gatekeeper 干净。

## FramePilot 仍开着时升级

跑本 NSIS 覆盖已有安装前，先退出 FramePilot（**File → Quit**）。sidecar 会锁住 `framepilot-api\_internal` 下的文件。若 Windows 提示 **Error opening file for writing**，点 **Abort**，不要点 **Ignore**。忽略会留下残缺安装（导入/导出可能空白）。那不是 [#195](https://github.com/joe-cheung-cae/frame-pilot/pull/195) 回退。残留 [#198](https://github.com/joe-cheung-cae/frame-pilot/issues/198) 之后的 NSIS 会用 Retry/Cancel 停住，而不是一路 Ignore。书面步骤：[docs/desktop_install.md](desktop_install.zh.md#升级先关掉应用)。

## Windows 11 导入/导出检查

1. 从**本** Release（`v2.1.2-desktop`）安装 NSIS `.exe`，不要用 `v2.1.1-desktop` 或 `v2.1.0-desktop`。
2. 启动 **FramePilot**。NSIS 第一次启动最多等两分钟。
3. 新建工程 → **Create and Import**。
4. 点 **Import** / **Export** 工作流选项卡（或 File → Import / File → Export）。
5. 通过：打开 Import Images 与 Export Selection。

## Windows 11 冷首启

1. 从**本** Release（`v2.1.2-desktop`）安装 NSIS `.exe`，不要用 `v2.1.0-desktop`。
2. **不要**预先运行 `%LOCALAPPDATA%\FramePilot\framepilot-api\framepilot-api.exe`。
3. 从开始菜单启动 **FramePilot**。最多等两分钟。
4. 通过：窗口标题 `FramePilot`，项目 UI，没有 `timed out waiting for sidecar ready line`。

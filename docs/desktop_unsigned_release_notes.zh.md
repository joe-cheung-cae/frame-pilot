# FramePilot 2.1.3-desktop（未签名）

> 语言：[English](desktop_unsigned_release_notes.md) | **中文**

本 GitHub Release 从现有 `desktop` 工作流发布**未签名**的 Windows NSIS 与 macOS DMG 安装包。

这些安装包是**未签名**的。它们**不是** Authenticode 签名、**不是** Apple 公证、**不是** Gatekeeper 干净、**不是** SmartScreen 干净，也**不是**商店上架。Windows 可能显示**未知发布者** / SmartScreen。macOS 可能显示**无法打开，因为无法验证开发者**。这些对话框是预期现象。

本版含 [#199](https://github.com/joe-cheung-cae/frame-pilot/pull/199) / [#198](https://github.com/joe-cheung-cae/frame-pilot/issues/198) Win11 NSIS 锁文件升级 hooks（`installerHooks` / `hooks.nsh`）：FramePilot 或 `framepilot-api` 仍锁着 sidecar `_internal` DLL 时，PREINSTALL/PREUNINSTALL 会**停住**。对话框只有 **Retry / Cancel**——**不能一路 Ignore** 装出残缺包。也含此前 [#195](https://github.com/joe-cheung-cae/frame-pilot/pull/195) / [#194](https://github.com/joe-cheung-cae/frame-pilot/issues/194) Win11 新建工程导入/导出修，以及 [#191](https://github.com/joe-cheung-cae/frame-pilot/pull/191) Windows sidecar ready-line 修（Windows 启动预算 120 秒、`{data_dir}/logs/sidecar.ready` 回退、spawn 工作目录 / `CREATE_NO_WINDOW` / 无缓冲 stdio）。

升级前先退出 FramePilot 与 `framepilot-api`。验应用仍在运行时升级**不要**用 `v2.1.2-desktop`（那份 NSIS 没有 hooks）。验新建工程导入/导出**不要**用 `v2.1.1-desktop`。Win11 冷首启**不要**用 `v2.1.0-desktop`。

**安装教程：** [未签名桌面安装教程](desktop_install.zh.md) · [English](desktop_install.md)

在 GitHub.com 上使用：

- https://github.com/joe-cheung-cae/frame-pilot/blob/main/docs/desktop_install.md
- https://github.com/joe-cheung-cae/frame-pilot/blob/main/docs/desktop_install.zh.md

## 资源

只从本 Release 下载安装文件：

- Windows：`FramePilot_2.1.0-desktop_x64-setup.exe`（NSIS，x64）
- macOS：`FramePilot_2.1.0-desktop_aarch64.dmg`（Apple Silicon / `aarch64`）

文件名仍带 `2.1.0-desktop`，因为没有改 `APP_VERSION`。Release tag 是 `v2.1.3-desktop`。

**不要**安装残留 GUI 证据 zip（`FramePilot-desktop-500-gui-*`、`FramePilot-desktop-quit-job-*`）。那些是测试日志，不是安装程序。

**Help → Check for updates** 不会下载或安装。请按教程从本 Release（或后续未签名 Release）安装更新的未签名构建。

这不是已签名的公开商店发行。不要把它当成 Gatekeeper 干净。

## FramePilot 仍开着时升级

跑本 NSIS 覆盖已有安装前，先退出 FramePilot（**File → Quit**）。sidecar 会锁住 `framepilot-api\_internal` 下的文件。若 FramePilot 仍开着，**本** NSIS（`v2.1.3-desktop`）只会以 **Retry / Cancel** 停住——**没有忽略**。**Cancel** 保持旧树完整。**File → Quit** 后再点 **Retry**（或重跑安装程序）。

`v2.1.2-desktop` 及更旧的仍可能提供**忽略**。点 **Abort**，不要点忽略。书面步骤：[docs/desktop_install.md](desktop_install.zh.md#升级先关掉应用)。

## Windows 11 应用仍在运行时升级检查

1. 先装一份旧的未签名 NSIS（`v2.1.2-desktop` 可作为基线）。
2. 启动 **FramePilot**。等到项目 UI 出来。**不要**退出。
3. 跑**本** Release（`v2.1.3-desktop`）的 NSIS `.exe`，不要用 `v2.1.2-desktop`。
4. 通过：安装程序停住，只有 Retry / Cancel（关闭 FramePilot / `framepilot-api`）。Cancel 保持旧树完整。没有一路 Ignore。
5. **File → Quit**，再点 Retry（或重跑安装程序）。走完向导。
6. 通过：`%LOCALAPPDATA%\FramePilot\framepilot-api\_internal\MSVCP140.dll` 存在。冷启动 → 新建工程 → 导入 / 导出能打开。

## Windows 11 导入/导出检查

1. 从**本** Release（`v2.1.3-desktop`）安装 NSIS `.exe`，不要用 `v2.1.1-desktop` 或 `v2.1.0-desktop`。
2. 启动 **FramePilot**。NSIS 第一次启动最多等两分钟。
3. 新建工程 → **Create and Import**。
4. 点 **Import** / **Export** 工作流选项卡（或 File → Import / File → Export）。
5. 通过：打开 Import Images 与 Export Selection。

## Windows 11 冷首启

1. 从**本** Release（`v2.1.3-desktop`）安装 NSIS `.exe`，不要用 `v2.1.0-desktop`。
2. **不要**预先运行 `%LOCALAPPDATA%\FramePilot\framepilot-api\framepilot-api.exe`。
3. 从开始菜单启动 **FramePilot**。最多等两分钟。
4. 通过：窗口标题 `FramePilot`，项目 UI，没有 `timed out waiting for sidecar ready line`。

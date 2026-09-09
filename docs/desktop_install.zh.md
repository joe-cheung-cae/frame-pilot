# 未签名桌面安装教程

> 语言：[English](desktop_install.md) | **中文**

如何从当前**未签名**的 Windows NSIS 与 macOS DMG 包下载、安装、启动并退出 FramePilot。

**另见：** [桌面用户指南](desktop_user_guide.zh.md) · [桌面测试矩阵](desktop_testing.zh.md) · [桌面开发计划](desktop_development_plan.zh.md) · [签名手册](desktop_signing.zh.md) · [已知限制](v2_known_limitations.zh.md) · [桌面壳 README](../apps/desktop/README.zh.md)

---

## 当前构建为未签名

这些安装包是**未签名**的。它们**不是**已公证的 Mac 构建、**不是** Authenticode 签名、**不是** Gatekeeper 干净、**不是** SmartScreen 干净，也**不是**商店上架版本。

Windows 可能显示 **Windows 已保护你的电脑** / **未知发布者**。macOS 可能显示 **无法打开，因为无法验证开发者** / Apple 无法检查该 App 是否包含恶意软件。在本轨道上这些对话框是预期现象。不要把本 Release 当成已签名的公开商店构建。

当 secrets 已配置时，CI 已签名就绪；缺少 secrets 时未签名上传保持绿灯。见 [桌面代码签名手册](desktop_signing.zh.md)。本教程不签名、不公证。

---

## 从哪下载

优先从含 [#191](https://github.com/joe-cheung-cae/frame-pilot/pull/191) sidecar ready-line / 120 秒修的未签名 GitHub Release 下载。Release notes：[docs/desktop_unsigned_release_notes.md](desktop_unsigned_release_notes.zh.md)。Win11 冷首启**不要**用 `v2.1.0-desktop`。

1. 打开 [Releases](https://github.com/joe-cheung-cae/frame-pilot/releases)，进入 **FramePilot 2.1.1-desktop (unsigned)**（`v2.1.1-desktop`）。
2. 只下载安装包资源：
   - Windows：`FramePilot_2.1.0-desktop_x64-setup.exe`（NSIS，x64）
   - macOS：`FramePilot_2.1.0-desktop_aarch64.dmg`（Apple Silicon / `aarch64`）
3. **不要**拿残留 GUI 证据 zip（`FramePilot-desktop-500-gui-*`、`FramePilot-desktop-quit-job-*`）当安装包。那些是测试日志，不是安装程序。
4. **不要**从第三方镜像下载。确认 URL 是 `github.com/joe-cheung-cae/frame-pilot`。

若该 Release 尚未发布，或你需要比下一版 Release 更新的未签名构建，再用 **desktop** GitHub Actions 工作流：

1. 打开 [Actions → desktop](https://github.com/joe-cheung-cae/frame-pilot/actions/workflows/desktop.yml)。
2. 打开 `main` 上一次**成功**的运行（绿勾）。若最新产物已过期，或你需要更新的提交，维护者可用 **Run workflow**（`workflow_dispatch`）打一份新包。
3. 若页面要求登录，请先登录 GitHub。下载 artifact 通常需要能看见该次运行的 GitHub 账号。
4. 在该次运行的 **Artifacts** 列表里，只下载 `FramePilot-windows-nsis` 或 `FramePilot-macos-dmg`，然后解压。里面应只有一个 NSIS `.exe` 或一个 `.dmg`。文件名包含 `FramePilot` 与 `2.1.0-desktop` 版本字符串。

GitHub Actions artifact 会过期。GitHub Release 资源不会随 Actions 保留期一起过期。若 Artifacts 一栏是空的，说明运行尚未结束、失败了，或 zip 已过期——改用未签名 Release、另一次绿色的 `main` 运行，或请维护者先调度 `desktop.yml` 再调度 `desktop-release.yml`。

**Help → Check for updates** 不会下载或安装。安装更新的未签名构建，仍按本页步骤。

---

## Windows（未签名 NSIS）

### 安装

1. 保留未签名 Release 里的 NSIS `.exe`（典型文件名 `FramePilot_2.1.0-desktop_x64-setup.exe`）。若走 Actions 回退，先解压 `FramePilot-windows-nsis`。
2. 双击安装程序。NSIS 配置为**当前用户**（`installMode: currentUser`），正常安装不需要管理员 UAC。
3. 走完 NSIS 向导。应用装在每用户安装目录（通常是 `%LOCALAPPDATA%\FramePilot`）。向导会添加名为 **FramePilot** 的开始菜单快捷方式。

### SmartScreen / 未知发布者

未签名 NSIS 构建常会触发 Microsoft Defender SmartScreen。

若 Windows 显示 **Windows 已保护你的电脑**（无法识别的应用 / **未知发布者**）：

1. 点击 **更多信息**。
2. 确认文件名就是你刚从本仓库未签名 Release（或解压后的 Actions 产物）拿到的 FramePilot 安装 `.exe`。
3. 点击 **仍要运行**。

首次运行前也可先解除阻止（仅限同一份可信产物）：

1. 右键 `.exe` → **属性**。
2. 若 Windows 显示 **此文件来自其他计算机，可能被阻止以帮助保护此计算机**，勾选 **解除锁定** → **应用** → **确定**。
3. 再次运行安装程序。

仅在你信任该 Release 或该次 Actions 运行时才绕过 SmartScreen。本页**不声称** SmartScreen 会保持安静，也不记录 SmartScreen 豁免。

### 启动

1. 打开 **开始** 菜单，启动 **FramePilot**（或安装程序创建的快捷方式）。
2. 窗口标题为 `FramePilot`。你不必自己启动 uvicorn，也不必打开浏览器。
3. Python sidecar 只绑定回环（`127.0.0.1`）。局域网其他设备打不开该 API。
4. 默认数据目录：`%APPDATA%\FramePilot`。卸载不一定会删掉它。
5. **安装后第一次启动** 可能要等大约两分钟，Windows 会扫描 `%LOCALAPPDATA%\FramePilot` 下的本地 API。等窗口出现。不要强杀后再立刻重试——以前那会杀掉仍在冷启动的 sidecar（#190）。

### Sidecar 没起来（Windows）

若窗口显示 **FramePilot could not start the local API** / `timed out waiting for sidecar ready line`：

1. 确认打开的是已安装的 **FramePilot** 快捷方式，而不是再跑一遍 NSIS setup `.exe`。
2. 全新安装先等满两分钟再判断失败。
3. 打开 `%APPDATA%\FramePilot\logs\sidecar.log` 和 `%APPDATA%\FramePilot\logs\sidecar.ready`。日志为空通常表示还在 PyInstaller 引导 / Defender 扫描。有 ready 文件且随后 `/health` 可用，说明 API 已经起来。
4. 退出后再开一次 **FramePilot** 并再等一次。第一次扫描之后，以后启动应快得多。
5. 不要把这当成签名、SmartScreen 豁免或托盘问题。

### 退出

1. 没有正在运行的导入、处理或导出时：**File → Quit**、**Ctrl+Q**，或关闭主窗口（**X**）。关窗口会**退出** FramePilot，不会藏到托盘。
2. 若作业仍在运行，选择 **Keep working**、**Quit and cancel**（导入 / 处理 / 导出）或 **Quit anyway**。细节见 [桌面用户指南](desktop_user_guide.zh.md#有任务时退出)。
3. 托盘 **Quit**（若有托盘图标）与 **File → Quit** 使用同一套进行中作业对话框。

### 卸载

使用 **设置 → 应用 → 已安装的应用 → FramePilot → 卸载**，或安装目录旁的卸载程序。应用二进制会被移除。**`%APPDATA%\FramePilot` 可能仍留在磁盘上**，以免项目被静默删掉。

---

## macOS（未签名 DMG）

### 安装

1. 保留未签名 Release 里的 `.dmg`（当前 `macos-latest` 上典型文件名为 `FramePilot_2.1.0-desktop_aarch64.dmg`）。若走 Actions 回退，先解压 `FramePilot-macos-dmg`。
2. 双击 DMG 以挂载。
3. 把 **FramePilot** 拖到 **应用程序**（或把 `FramePilot.app` 拷到那里）。
4. 推出 DMG。从 `/Applications/FramePilot.app` 启动，不要从磁盘映像里启动。

Intel Mac 不能使用仅适用于 Apple Silicon 的 DMG。若需要其他架构，须由维护者另行出品；本教程不发明 universal 包。

### Gatekeeper / 无法验证开发者

下载后的未签名 DMG 会被隔离。第一次打开常常失败，提示 **无法打开“FramePilot”，因为无法验证开发者**，或 Apple 无法检查是否包含恶意软件。

仅对你从本仓库未签名 Release 或 Actions 下载的 DMG 使用以下任一方法：

**按住 Control 点按 → 打开（首选）**

1. 在 **应用程序** 中按住 Control 点按（或右键）**FramePilot**。
2. 选择 **打开**。
3. 在警告对话框里再选 **打开**。

**系统设置 → 允许**

1. 打开 **系统设置 → 隐私与安全性**。
2. 滚到提示 FramePilot 因并非来自身份明确的开发者而被阻止的那一段。
3. 点击 **仍要打开**。如有要求，用密码或触控 ID 确认。

**可选：清除隔离属性（仅限可信的内部 DMG）**

```bash
xattr -d com.apple.quarantine /Applications/FramePilot.app
```

**不要**全局关闭 Gatekeeper。本页**不声称** Gatekeeper 干净或已公证的 Mac 通过。

### 启动

1. 从应用程序或聚焦打开 **FramePilot**。
2. 窗口标题为 `FramePilot`。你不必自己启动 uvicorn，也不必打开浏览器。
3. Python sidecar 只绑定回环（`127.0.0.1`）。
4. 默认数据目录：`~/Library/Application Support/FramePilot`。卸载不一定会删掉它。

### 退出

1. 没有正在运行的导入、处理或导出时：**FramePilot → 退出 FramePilot**、**File → Quit**、**Cmd+Q**，或关闭主窗口。关窗口会**退出** FramePilot，不会藏到托盘。
2. 若作业仍在运行，选择 **Keep working**、**Quit and cancel**（导入 / 处理 / 导出）或 **Quit anyway**。细节见 [桌面用户指南](desktop_user_guide.zh.md#有任务时退出)。
3. 托盘 **Quit**（若有托盘图标）与 **File → Quit** 使用同一套进行中作业对话框。

### 卸载

把 `/Applications/FramePilot.app` 拖到废纸篓，需要彻底删除时再清空。**`~/Library/Application Support/FramePilot` 可能仍留在磁盘上**，以免项目被静默删掉。

---

## QA 路径：拿到包 → 装 → 开 → 关

把下面当作手工未签名安装检查的文字路径。能连上 sidecar 时记录日期、操作系统、Release URL（或 Actions 运行 URL），以及 `GET /health` 的 `APP_VERSION`。不要编造通过。

### Windows

1. 从 [FramePilot 2.1.1-desktop (unsigned)](https://github.com/joe-cheung-cae/frame-pilot/releases)（`v2.1.1-desktop`）下载 NSIS `.exe`。若 Release 还没有，再从一次绿色的 [desktop](https://github.com/joe-cheung-cae/frame-pilot/actions/workflows/desktop.yml) 运行解压 `FramePilot-windows-nsis`。本检查不要用 `v2.1.0-desktop`。
2. 按上文处理 SmartScreen / 未知发布者，然后走完 NSIS 向导。
3. 从开始菜单启动 **FramePilot**。NSIS **第一次**启动最多等两分钟。确认窗口标题为 `FramePilot`，并且能看到项目列表（不是 “timed out waiting for sidecar ready line”）。
4. 可选：只有在已经从 sidecar ready 文件（`%APPDATA%\FramePilot\logs\sidecar.ready`）读到分配端口时，才对 `GET http://127.0.0.1:<port>/health`。应看到 `version` + `service`。不要写死端口 `8000`。
5. 用 **File → Quit** 或窗口关闭按钮退出。确认窗口已消失（关窗口即退出，不是藏到托盘）。

### macOS

1. 从 [FramePilot 2.1.1-desktop (unsigned)](https://github.com/joe-cheung-cae/frame-pilot/releases)（`v2.1.1-desktop`）下载 `.dmg`。若 Release 还没有，再从一次绿色的 [desktop](https://github.com/joe-cheung-cae/frame-pilot/actions/workflows/desktop.yml) 运行解压 `FramePilot-macos-dmg`。
2. 挂载 DMG，把 **FramePilot** 拖到应用程序，推出映像。
3. 按上文处理 Gatekeeper，然后打开 `/Applications/FramePilot.app`。确认窗口标题为 `FramePilot`。
4. 用 **FramePilot → 退出 FramePilot**、**Cmd+Q** 或窗口关闭按钮退出。确认窗口已消失（关窗口即退出，不是藏到托盘）。

这条路径走通后，首次启动、项目、导入（只复制不移动）与导出见 [桌面用户指南](desktop_user_guide.zh.md)。手工矩阵行见 [桌面测试矩阵](desktop_testing.zh.md)。

---

## 本页不覆盖

- 代码签名、公证、SmartScreen 豁免或商店上架
- 改打包脚本或 `APP_VERSION`
- 声称 Gatekeeper 干净、SmartScreen 干净或商店上架
- 托盘隐藏到后台（关窗口仍是退出）
- 第十阶段 / 新的桌面功能门禁

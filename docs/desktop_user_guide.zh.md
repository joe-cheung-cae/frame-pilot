# 桌面用户指南

> 语言：[English](desktop_user_guide.md) | **中文**

FramePilot 桌面是本地优先的照片筛选应用。Tauri 窗口承载 UI，并在回环地址（`127.0.0.1`）启动 Python API **sidecar**。你不必自己跑 uvicorn。相机原图永不被修改；导入会**复制**到项目的 `originals/` 目录。

**另见：** [桌面测试矩阵](desktop_testing.zh.md) · [签名手册](desktop_signing.zh.md) · [已知限制](v2_known_limitations.zh.md) · [架构](v2_architecture.zh.md) · [Phase 2 工作流清单](../tests/desktop/workflow.md) · [桌面壳 README](../apps/desktop/README.md)（开发者）

---

## 安装

1. 从 GitHub Actions 的 **desktop** 工作流运行（或已打 tag 的发布）下载 Windows NSIS（`.exe`）或 macOS DMG。
2. 安装并启动 **FramePilot**。
3. 构建可能是**未签名**的。内部测试时可能看到 SmartScreen（Windows）或 Gatekeeper（macOS）警告。见 [桌面代码签名手册](desktop_signing.zh.md)。不要把未签名包当作商店级公开发布。

卸载会移除应用二进制。应用数据目录可能仍留在磁盘上（见下文），以免项目被静默删掉。

---

## 首次启动

- 窗口标题为 `FramePilot`。
- Sidecar 只绑定回环。局域网其他设备打不开该 API。
- 默认**数据目录**（应用支持目录）：
  - macOS：`~/Library/Application Support/FramePilot`
  - Windows：`%APPDATA%\FramePilot`
  - Linux（开发壳）：`~/.local/share/FramePilot`
- 打开 **Settings** 确认数据目录（`GET /api/meta`）。仅在明确需要时用绝对路径的 `FRAMEPILOT_DATA_DIR` 覆盖。

---

## 创建项目

1. 使用 **New project**（或桌面 File → New）。
2. 输入名称。桌面上 **Browse** 会打开原生文件夹选择器，注册文件夹（`POST /api/desktop/project-roots`），再填入项目数据目录。
3. 若文件夹已有文件，确认 FramePilot 会在其中创建项目子目录，且**不会**修改已有文件。
4. **Create and Import** 进入导入页。仪表盘 **Open project folder** 会在系统文件管理器中揭示 `root_path`。

---

## 导入（只复制，不移动）

- 优先 **Choose a folder** 或 **Choose image files**（原生对话框）。桌面使用路径导入（`POST .../imports/from-paths`），不会经 WebView File API 上传成千上万字节。
- 每次 HTTP 请求最多消费 **100** 个展开后的文件。大文件夹用同一 `job_id` 继续，直到最后一片 `finalize`。
- 支持：JPEG、PNG、WebP。HEIC/RAW 会以本地提示跳过。
- 有效文件**复制**到 `{root_path}/originals`。源卡与源文件夹保持不动（size、mtime、字节）。

也可以仅在导入页拖放文件/文件夹。在其他页面拖放不得开始导入。

---

## 处理、筛选、导出

1. 导入完成后运行分组与排序（**Process Project**）。
2. 打开筛选工作区。键盘快捷键与 web 一致（P/M/X/U、星级、导航）。Help 将桌面菜单组合键（CmdOrCtrl+N/W/Q）与裸筛选键分开列出。
3. 在 **Export Selection** 导出 CSV、ZIP 和/或文件夹。产物落在 `{root_path}/exports/...`。
4. 使用 **Open export folder**（揭示）或 **Copy Path**。桌面不要求经浏览器下载锚点。

---

## 有任务时退出

活跃**导入**时关闭，可选继续工作 / 退出并取消导入 / 仍要退出。取消走同一 job cancel API，再停止 sidecar。活跃**处理**任务无法取消；仍要退出会停止 sidecar，下次启动将过期任务标为失败。细节见 [apps/desktop/README.md](../apps/desktop/README.md)。

---

## 桌面 vs 开发用 web

| 用途 | 命令 / 路径 |
| ---- | ----------- |
| 终端用户桌面壳 | 安装包，或 `npm run dev:desktop`（需 Rust） |
| 贡献者 web + API | `npm run dev` → web `:3000`，API `:8000` |
| 无 Rust 检查 | `npm run verify` |

Playwright 与多数贡献者文档假设 Next.js web 应用。桌面壳通过 HTTP 复用同一套筛选组件对接 sidecar。

---


## 公开发布出处（签名构建）

内部 RC 安装包可为 **未签名**。在任何 **公开** 桌面发布之前：

1. 按 [桌面代码签名手册](desktop_signing.zh.md) 完成 Authenticode + macOS 公证（密钥仅存 CI）。
2. 只从维护者控制的 GitHub Releases（或该 Release 链接的 Actions 产物）发布安装包。
3. 为每个产物发布 **SHA-256 校验和**（例如 `SHA256SUMS.txt`），下载后核验：
   - Linux/macOS：`shasum -a 256 <installer>`
   - Windows（PowerShell）：`Get-FileHash .\installer.exe -Algorithm SHA256`
4. 确认下载 URL 与 org/repo 属于本项目；不要从第三方镜像安装。
5. Sidecar 的 `GET /api/meta` 与日志中的 `data_dir=` 仍是本机回环 / 同用户可见——符合 local-first；不是公开网络 API。

这关闭 Phase 5 安全评审运维清单（[#98](https://github.com/joe-cheung-cae/frame-pilot/issues/98)）。证书本身的组织密钥配置仍见签名手册。

## 隐私与安全

- 不把原图或预览上传到云端。
- API 仅回环；经机器 LAN IP 浏览必须失败。
- 自定义项目根必须注册；不要把白名单扩到 `$HOME` 或盘符根。

# 桌面用户指南

> 语言：[English](desktop_user_guide.md) | **中文**

FramePilot 桌面是本地优先的照片筛选应用。Tauri 窗口承载 UI，并在回环地址（`127.0.0.1`）启动 Python API **sidecar**。你不必自己跑 uvicorn。相机原图永不被修改；导入会**复制**到项目的 `originals/` 目录。

**另见：** [桌面测试矩阵](desktop_testing.zh.md) · [签名手册](desktop_signing.zh.md) · [已知限制](v2_known_limitations.zh.md) · [架构](v2_architecture.zh.md) · [Phase 2 工作流清单](../tests/desktop/workflow.zh.md) · [桌面壳 README](../apps/desktop/README.zh.md)（开发者）

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
- **Change data directory**（仅桌面）把当前应用数据目录拷贝到你选择并授权的空文件夹（`POST /api/desktop/project-roots`，然后 `POST /api/desktop/data-dir`）。该目录内的已存项目路径会被改写。相机卡和其他源文件夹不移动、不修改。旧数据目录留在磁盘。绝对路径的 `FRAMEPILOT_DATA_DIR` 仍优先于指针文件。
- **Import workers**（1–4，默认 1）可加快大导入的缩略图和预览。分组和排序仍是每个项目一个作业。原片不变。该值作用于下一次导入作业（`GET`/`PATCH /api/settings`）。

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
- 支持：JPEG、PNG、WebP、HEIC/HEIF、AVIF 静帧，以及带内嵌预览的 RAW（`.dng`、`.arw`、`.cr3`、`.nef`）。原片原样拷贝；预览为静帧 RGB 或 RAW 内嵌预览生成的 WebP。没有预览的 RAW 会以本地提示跳过。
- 有效文件**复制**到 `{root_path}/originals`。源卡与源文件夹保持不动（size、mtime、字节）。

也可以仅在导入页拖放文件/文件夹。在其他页面拖放不得开始导入。

---

## 处理、筛选、导出

1. 导入完成后运行分组与排序（**Process Project**）。
2. 打开筛选工作区。键盘快捷键与 web 一致（P/M/X/U、星级、导航）。Help 将桌面菜单组合键（CmdOrCtrl+N/W/Q）与裸筛选键分开列出。裸筛选键只作用于聚焦窗口。
3. 在 **Export Selection** 导出 CSV、ZIP 和/或文件夹。产物落在 `{root_path}/exports/...`。可选 **Write XMP sidecars**（默认关）会在文件夹拷贝旁和 ZIP 内写 `.xmp`；永不写到原片旁。CSV 已含状态和星级。
4. 使用 **Open export folder**（揭示）或 **Copy Path**。桌面不要求经浏览器下载锚点。

---

## 独立预览

**View → Detached preview**（或筛选工具栏的 **Toggle detached preview**）打开第二个窗口，显示当前筛选照片；compare 打开时显示 compare 集合。选中与主工作区共享。Space 和 Eye 仍切换壳内预览，不会被替换。裸筛选键（P/M/X/U、星级、方向键、Space 等）只作用于聚焦窗口。若第二个 WebView 无法创建，壳内预览仍在，应用不崩溃。关闭预览窗（或预览聚焦时 File → Close）不会退出 FramePilot。

---

## 系统托盘

桌面壳在 FramePilot 运行时会尝试创建系统托盘图标。无头主机或部分 Linux 桌面可能创建失败；这是非致命的，主窗口仍会启动。Tooltip 与状态栏作业行一致（`Import · {step} · {n}%`、分组与排序、或导出；空闲为 `No active job`）。**Show**（或左键单击图标）恢复主窗口。**Quit** 走与 File → Quit 同一套进行中作业对话框。关窗口或 File → Close 仍是退出，不会藏到托盘。最小化仍留在任务栏或程序坞。

---

## 有任务时退出

活跃**导入**时关闭，可选继续工作 / 退出并取消导入 / 仍要退出。活跃**处理**时关闭，可选继续工作 / 退出并取消处理 / 仍要退出。活跃**导出**时关闭，可选继续工作 / 退出并取消导出 / 仍要退出。取消会 POST 同一 job cancel API，最多等待 10 秒，再对 sidecar 发送 SIGTERM。取消处理会清部分分组；取消导出会清理不完整的 CSV/ZIP/文件夹产物；原图不变。仍要退出会直接 SIGTERM sidecar，不等待取消完成。默认下次启动会将残留导入/处理任务标为中断并回收；残留导出仍 fail-and-cleanup。设置 `FRAMEPILOT_JOB_RECLAIM_ON_STARTUP=0` 可改为将残留导入/处理任务标为失败以便手动重试。硬杀死不会被标记为 `cancelled`。细节见 [apps/desktop/README.zh.md](../apps/desktop/README.zh.md)。

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

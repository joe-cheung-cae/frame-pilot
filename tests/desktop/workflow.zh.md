# 桌面第二阶段工作流清单

> 语言：[English](workflow.md) | **中文**

D2.08 的手工 GUI 通过项。自动化覆盖是 `apps/api/tests/test_path_import_process_export_workflow.py`（`from-paths` → 处理 → Pick → CSV/ZIP/文件夹导出；源文件 `st_size` / mtime / hash 不变）。

**不要**修改或删除相机原图。只复制。HEIC/RAW/XMP 不在第二阶段范围内。

没有 WebView 的主机上，现场原生选择器、拖放和操作系统揭示点击可以保持带日期的 `[~]`。HTTP/API 覆盖仍必须是 `[x]`。

## 准备

- [ ] 用户空间 `rustc` / `cargo` 可用（[apps/desktop/README.zh.md](../../apps/desktop/README.zh.md)）。`npm run verify` 不得调用它们。
- [ ] 从仓库根目录：`npm run dev:desktop`。窗口标题是 `FramePilot`。Sidecar 在回环上，带 `FRAMEPILOT_DESKTOP=1`。
- [ ] 准备一个项目数据目录**之外**的一次性 JPEG/PNG/WebP 文件夹。至少记录两个文件的大小和修改时间。

## 创建项目

- [ ] 打开 Create Project（`/projects/new`）。
- [ ] 输入项目名。桌面上，**Browse** 打开原生目录选择器，注册文件夹（`POST /api/desktop/project-roots`），然后填入 **Project data folder**。
- [ ] 若所选文件夹已有文件，确认原文恰好是：`This folder already contains files. FramePilot will create its project folders inside it and will not modify existing files. Continue?`
- [ ] **Create and Import** 落到 Import Images。
- [ ] 仪表盘 **Open project folder** 在操作系统文件管理器中揭示 `root_path`。

## 导入（路径导入，不是 WebView File API）

- [ ] **Choose a folder**（或 **Choose image files**）使用原生对话框，经 `POST /api/projects/{id}/imports/from-paths` 导入。
- [ ] 可选：只在导入页拖放文件或文件夹。覆盖层文案是 `Drop files or folders to import`。在别处放下不得开始导入。
- [ ] 导入任务到达 `complete`（仅跳过不支持文件时可为 `complete_with_errors`）。导入进行中 **Process Project** 保持禁用。
- [ ] 项目副本在 `{root_path}/originals`。源文件夹列表、文件大小和修改时间不变。

## 处理

- [ ] **Process Project** → **Run Grouping and Ranking**。
- [ ] 任务到达 `complete`。**Open Culling Workspace** 可用。

## 用键盘筛选

- [ ] 方向键移动照片 / 组。
- [ ] `P` Pick，`M` Maybe，`X` Reject，`U` Unreviewed。
- [ ] `1`–`5` 设星；`0` 清星。
- [ ] `E` 打开导出。`Space` / `Z` / `C` / `G` / `F` 仍有效。带修饰键的组合不得抢走这些裸键。

## 导出与揭示

- [ ] 在 Export Selection 上保持勾选 **Pick**。先导出 **CSV**，再 **ZIP**，再 **Folder**。
- [ ] 每次运行在 `{root_path}/exports/{csv|zip|folders}` 下显示本地 `output_path`。
- [ ] **Open export folder** 揭示该 `output_path`（或项目 exports 根）。**Copy Path** 仍可用。
- [ ] 桌面不要求浏览器/WebView 下载锚点（D2.09）。在磁盘上确认产物，不要经 WebView 下载 blob。

## 原图

- [ ] 导入用的源文件仍在原路径。
- [ ] 大小和修改时间与导入前记录一致。
- [ ] 字节一致（无改写、原图旁无 sidecar、POSIX 上没有硬链接进 `originals`）。
- [ ] 导出文件夹/ZIP 内容来自项目 originals 的副本，不是相机卡上的文件。

## 记录

日期、操作系统、`APP_VERSION`（`2.0.0-rc2`），以及原生选择器 / 拖放 / 揭示是现场 `[x]` 还是带日期的 `[~]`。不要从本清单开始第三阶段。

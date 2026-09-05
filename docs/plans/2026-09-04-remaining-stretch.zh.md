# 第九阶段实现计划 — 剩余 stretch 收口（2026-09-04）

> 语言：[English](2026-09-04-remaining-stretch.md) | **中文**

**总览：** [#160](https://github.com/joe-cheung-cae/frame-pilot/issues/160)（S9.00 排期）  
**相关：** `develop_plan.zh.md` §1.1；第七阶段 [2026-09-03-phase7-processing-cancel.zh.md](2026-09-03-phase7-processing-cancel.zh.md)；第八阶段 [2026-09-04-heic-preview.zh.md](2026-09-04-heic-preview.zh.md)；XMP 历史 [#117](https://github.com/joe-cheung-cae/frame-pilot/issues/117)

Goal Mode 与 `/workflow remaining-stretch`：**每次运行只实现一个 GitHub issue**。传入 `args.slice`（`s901`…`s913`）。当前 issue 未实现、测试、评审、提交并推送之前，不要开始下一个 id。

---

## 1. 为什么做这一刀

到第八阶段为止的编号交付已在 `main`。§1.1 里剩下的是未排期 stretch，不是可以随便开工的许可。本计划把该清单**排期**为第九阶段（S9.00–S9.13）。不要发明第十阶段。

S9.00 是本文档、§1.1 指针、GitHub issue 和工作流文件。产品工作从 S9.01 开始。

---

## 2. 锁定决策

1. **本地优先。** 不上传原片，无登录、支付或捆绑神经网络模型。
2. **永不修改或删除原片。** 衍生件、导出物、XMP sidecar 和缓存都不写进源文件。
3. **每个 workflow `phase()` / 每次运行只对应一个 GitHub issue。** 不要把 S9.01–S9.13 塞进一次 开发。
4. **J7.07：** 在现有处理检查点上协作式 `pause_requested`；worker 退出时不 finalize 为 `cancelled`，也不留下可审阅的半成品分组。**恢复 = 经 `POST /process` 的 clear-and-rerun。** 不要保留半成品分组。
5. **导出取消：** 现有 cancel 路由允许 `job_type == "export"`。协作式检查点。不完整的 ZIP/文件夹走 fail-and-cleanup。修正 `"Only import jobs can be cancelled"`。桌面退出可取消进行中的导出。
6. **AVIF：** 把 `.avif` 加进现有静帧导入/导出管线。用 Pillow 自带的 `AvifImagePlugin` 解码（现场 `pillow-heif` 1.6 已去掉 AVIF；不要让 HEIF opener 宣称 `.avif`）。测试里进程内生成小文件。不是 RAW。
7. **RAW：** 原样拷贝字节；只抽**内嵌预览**。没有 thumb → 用明确本地消息跳过。不 demosaic。不把相机文件提交进 git。LibRaw 许可说明比照 libheif。
8. **XMP：** 在 [#165](https://github.com/joe-cheung-cae/frame-pilot/issues/165) 上实现。只在导出目录写 `.xmp`。永不写入 `originals/` 或相机原片旁。可选，默认关。
9. **并发旋钮：** 默认仍是一个导入/处理 worker。设置可将导入 worker 升到 2–4（opt-in）。每个项目一个处理作业。不要 Redis/Celery。
10. **检查更新：** 仅菜单点击；GitHub Releases；启动时不联网；清单缺失为非致命。
11. **签名：** CI 按 secrets 门控；未签名回退必须保持绿灯。DoD 是 signing-ready，不是商店发行。
12. **macOS QA：** skip ≠ pass。没有 Mac 主机时用 ISO-8601 时间戳记录 skip。
13. **不改 `APP_VERSION`。** 只写 CHANGELOG 未发布。
14. **活文档双语**；代码、注释、测试、提交说明用英文。
15. **测试先行。** 每次 上线 前 `npm run verify`。
16. **不做：** D4.03、完整 RAW 显影、保留半成品分组的原地暂停、云、Dramatiq/RQ、发明第十阶段。

---

## 3. 状态板

第九阶段 — 剩余 stretch（第八阶段之后）

- [x] S9.00 排期切片、GitHub issue、§1.1 指针、workflow — [#160](https://github.com/joe-cheung-cae/frame-pilot/issues/160)
- [x] S9.01 导出作业取消 — [#164](https://github.com/joe-cheung-cae/frame-pilot/issues/164)
- [x] S9.02 J7.07 处理暂停/恢复 — [#161](https://github.com/joe-cheung-cae/frame-pilot/issues/161)
- [x] S9.03 AVIF 静帧预览 — [#163](https://github.com/joe-cheung-cae/frame-pilot/issues/163)
- [x] S9.04 RAW 内嵌预览 — [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162)
- [x] S9.05 XMP sidecar 导出 — [#165](https://github.com/joe-cheung-cae/frame-pilot/issues/165)（历史 [#117](https://github.com/joe-cheung-cae/frame-pilot/issues/117)）
- [x] S9.06 可选系统托盘（D3.06） — [#169](https://github.com/joe-cheung-cae/frame-pilot/issues/169)
- [x] S9.07 独立预览窗口 — [#166](https://github.com/joe-cheung-cae/frame-pilot/issues/166)
- [x] S9.08 可选导入并发旋钮 — [#168](https://github.com/joe-cheung-cae/frame-pilot/issues/168)
- [x] S9.09 更改数据目录 — [#170](https://github.com/joe-cheung-cae/frame-pilot/issues/170)
- [x] S9.10 可选检查更新 — [#167](https://github.com/joe-cheung-cae/frame-pilot/issues/167)
- [x] S9.11 签名就绪 CI — [#171](https://github.com/joe-cheung-cae/frame-pilot/issues/171)
- [ ] S9.12 macOS DMG GUI 生命周期 QA — [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172)
- [ ] S9.13 文档残留修复 — [#173](https://github.com/joe-cheung-cae/frame-pilot/issues/173)

---

## 4. Issue 对照

| ID | GitHub | 提交说明 |
| -- | ------ | -------- |
| S9.00 | [#160](https://github.com/joe-cheung-cae/frame-pilot/issues/160) | `docs: schedule remaining stretch S9.00–S9.13` |
| S9.01 | [#164](https://github.com/joe-cheung-cae/frame-pilot/issues/164) | `v2: allow cooperative cancel on export jobs` |
| S9.02 | [#161](https://github.com/joe-cheung-cae/frame-pilot/issues/161) | `v2: cooperative pause for processing jobs` |
| S9.03 | [#163](https://github.com/joe-cheung-cae/frame-pilot/issues/163) | `v2: import AVIF still previews` |
| S9.04 | [#162](https://github.com/joe-cheung-cae/frame-pilot/issues/162) | `v2: extract RAW embedded previews` |
| S9.05 | [#165](https://github.com/joe-cheung-cae/frame-pilot/issues/165) | `v2: write XMP sidecars in export directory` |
| S9.06 | [#169](https://github.com/joe-cheung-cae/frame-pilot/issues/169) | `desktop: optional system tray` |
| S9.07 | [#166](https://github.com/joe-cheung-cae/frame-pilot/issues/166) | `desktop: detached preview window` |
| S9.08 | [#168](https://github.com/joe-cheung-cae/frame-pilot/issues/168) | `desktop: opt-in import worker concurrency` |
| S9.09 | [#170](https://github.com/joe-cheung-cae/frame-pilot/issues/170) | `desktop: change data directory with path rewrite` |
| S9.10 | [#167](https://github.com/joe-cheung-cae/frame-pilot/issues/167) | `desktop: optional check for updates` |
| S9.11 | [#171](https://github.com/joe-cheung-cae/frame-pilot/issues/171) | `ci: sign desktop installers when secrets exist` |
| S9.12 | [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172) | `docs: macOS DMG GUI lifecycle QA` |
| S9.13 | [#173](https://github.com/joe-cheung-cae/frame-pilot/issues/173) | `docs: close out remaining stretch S9` |

---

## 5. 各 issue 合同

### S9.00 — 排期（本提交）

文档 + GitHub issue + `.grok/workflows/remaining-stretch.rhai`。不改产品行为。

S9.01–S9.07 合同未改、已经交付。锁定的导出取消、暂停、AVIF、RAW、XMP、托盘和独立预览正文见 `feature/remaining-stretch` 上的 git 历史。

### S9.08 — 并发旋钮

锁定合同：[2026-09-04-s908.zh.md](2026-09-04-s908.zh.md)。设置 1–4 个导入**衍生** worker，默认 1。每个项目一个处理作业。不要 Redis/Celery。

**现场空洞：** `run_import_derivative_job` 是按照片顺序循环（`apps/api/app/services/importing.py`）。没有 `GET`/`PATCH /api/settings`。`SettingsPanel` 没有 worker 控件。独占的 `python -m app.worker` 锁。已知限制否认旋钮。#168：导入衍生 worker 1–4 opt-in，默认 1。

**身份：** 把 `import_workers` 持久化为整数 1–4，默认 1，写入 `{data_dir}/app_settings.json`（原子 tmp + replace）。由 API 拥有。不要 localStorage，不要 `/api/meta`，不要升 schema。在 `run_import_derivative_job` 开始时快照。`n==1` 保持顺序循环。`n=2–4` 用 `ThreadPoolExecutor`；每个任务自己的 Session；并发 `process_registered_import_photo` 峰值 ≤ n。取消协作式；等在飞任务；不杀线程。永不修改原片。不要 ProcessPool，不要额外操作系统 worker。

**API：** GET `/api/settings` → `{import_workers}`。PATCH 相同；`0`/`5`/非整数 → 422。Web 与桌面。

**处理：** 仍是每项目一个作业。不要处理 worker 旋钮。导入仍是每项目一个作业（409）。

**UI：** SettingsPanel **Import workers** 1–4 默认 1。`api.getSettings` / `api.patchSettings`。作用于下一次导入作业。

**本计划（仅实现提交）：** 勾选 §3 S9.08 `[x]`（中英）。不要勾 S9.09–S9.13。

**文件：** `apps/api/app/core/app_settings.py`（新建）；`apps/api/app/schemas/api.py`；`apps/api/app/api/routes.py`；`apps/api/app/services/importing.py`；`apps/api/tests/test_app_settings.py`；`apps/web/src/lib/api.ts`；`apps/web/src/components/SettingsPanel.tsx`（+ 测试）；`docs/api.md`、`docs/v2_known_limitations.md`、architecture、用户指南、CHANGELOG Unreleased（+ zh）。

**测试先行：** GET 默认 1；PATCH 2–4 持久化；非法 422；并发峰值；原片未动；workers=4 时取消；`POST /process` 复用；SettingsPanel。

**非目标：** Redis/Celery；处理池；cache 旋钮；S9.09–S9.13；`APP_VERSION`；签名。

### S9.09 — 数据目录

显式授权（D2.00 允许名单）。改写已存项目路径。永不改写相机卡上的原片。

**现场空洞：** SettingsPanel 用 `GET /api/meta` 只读展示数据目录，并写明本版本不能改位置（`apps/web/src/components/SettingsPanel.tsx`）。D3.03 把更改推迟到 2.2。Rust `resolve_runtime_data_dir` 用绝对 `FRAMEPILOT_DATA_DIR`，否则是操作系统 app-support / `.framepilot-desktop-dev`（`apps/desktop/src-tauri/src/data_dir.rs`）；没有指针文件。Sidecar 必须带 `--data-dir`。SQLite `framepilot.db` 以及绝对路径 `Project.root_path`、`Photo.original_path` / `project_copy_path` / `thumbnail_path` / `preview_path`、`ExportRecord.output_path`。`Project.source_root_path` 是导入文件夹（相机卡 / 源）。导入拷贝进 `{root_path}/originals`，永不改源文件。D2.00 `POST /api/desktop/project-roots` + `register_root` 是授权路径；拒绝 `$HOME` / `/` / 盘符根 / 当前 data_dir 及其父目录。`test_create_project_rejects_root_outside_allowlist` 必须保持全绿且不变。#170：显式用户授权；拷贝/移动 FramePilot 数据目录；改写已存项目路径；永不改写相机卡上的原片。

**身份：** 仅桌面更改 FramePilot **应用数据目录**（数据库、日志、`app_settings.json`、`desktop_project_roots.json`、`{data_dir}/projects/...`）。不是项目根选择器，也不是原地引用。把当前 data-dir 树拷贝到显式授权的目标；只改写解析后前缀为**旧** data_dir 的已存路径；旧树留在磁盘（本切片不删除）。**永不**打开、拷贝、移动、chmod 或改写相机卡上的文件，以及旧 data_dir 之外的任何路径。不升 schema。

**授权：** 与项目文件夹相同的 D2.00 流程：原生 `pickDirectory` → `POST /api/desktop/project-roots`（既有 422）。仅当目标已在 `registered_roots()` 里才迁移。复用 `register_root` / `is_blocked_allowlist_root`。另外拒绝当前 data_dir、其父目录、当前 data_dir 的**子目录**（嵌套拷贝）以及同一路径。目标必须存在、是目录、且为空。**不要**设置 `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST`。**不要**改 `test_create_project_rejects_root_outside_allowlist`。拷贝后从拷贝出的 `desktop_project_roots.json` 里去掉新 data_dir（它现在就是 data dir；D2.00 会拒绝它）。

**API：** 仅桌面 `POST /api/desktop/data-dir` `{"path": "<abs>"}`（无 `FRAMEPILOT_DESKTOP=1` 则 404）。若有作业处于 `BLOCKING_JOB_STATUSES` 则 409。未注册 / 被拦截 / 嵌套 / 缺失 / 非空则 422。拷贝整棵树（含 SQLite `-wal`/`-shm`）。只在**目标**数据库里改写（旧库和文件保持字节一致）。仅当已存路径位于旧 data_dir 下时，才对 `Project.root_path`、`Photo.original_path` / `project_copy_path` / `thumbnail_path` / `preview_path`、`ExportRecord.output_path` 做 old_data_dir 前缀替换。**永不**改写 `Project.source_root_path`。旧 data_dir 之外的自定义 D2.00 项目文件夹不动（不拷贝文件；`root_path` 不变）。200 `{ "data_dir": "<new>" }`。

**持久化 / 重启：** Rust 在环境变量覆盖之后、默认 app-support / `.framepilot-desktop-dev` 之前读取 `{anchor}/data_dir.json`（`{"data_dir": "<abs>"}`）。绝对 `FRAMEPILOT_DATA_DIR` 仍优先。API 200 之后，Tauri 把指针写到**默认锚点**（不写进可移动树内），更新 `DesktopPaths`，并用新的 `--data-dir` 重新拉起 sidecar。设置页重新请求 `GET /api/meta`。不要额外 `fs:` / `shell:` 能力。

**UI：** 仅桌面壳 + native FS 的 SettingsPanel：**Change data directory**（选择 → 注册 → 确认 → POST）。确认拷贝：只改写当前数据目录内的路径；相机卡和其他源文件夹不移动、不修改。浏览器保持只读。保留 **Open data folder**。

**本计划（仅实现提交）：** 勾选 §3 S9.09 `[x]`（中英）。不要勾 S9.10–S9.13。

**文件：** `apps/api/app/services/data_dir.py`（新建）；`apps/api/app/api/routes.py`；`apps/api/app/schemas/api.py`；`apps/api/tests/test_data_dir_relocate.py`（新建）；`apps/desktop/src-tauri/src/data_dir.rs`；`apps/desktop/src-tauri/src/lib.rs`；`apps/web/src/lib/api.ts`；`apps/web/src/components/SettingsPanel.tsx`（+ 测试）；`docs/api.md`、`docs/v2_known_limitations.md`、architecture、用户指南、CHANGELOG Unreleased（+ zh）。不要把 `docs/desktop_development_plan.md` §2.2 改写成已交付（留给 S9.13）。

**测试先行：** 先注册再 POST，拷贝数据库 + 托管项目；改写后的 `root_path` / 项目拷贝 / 衍生路径落在新 data_dir 下；旧 data_dir 文件字节不变；相机卡源 size/mtime/bytes 不变；`source_root_path` 不变；旧 data_dir 之外的自定义 D2.00 `root_path` 不变；被拦截 / 未注册 / 嵌套 / 非空 422；非桌面环境 404；阻塞作业 409；`test_create_project_rejects_root_outside_allowlist` 不变；SettingsPanel 仅桌面显示 Change；指针文件使下一次 `resolve_data_dir` 返回覆盖值；环境变量覆盖仍优先。

**非目标：** 删除旧数据目录；把 §2.2 改写成已完成；检查更新（S9.10）；签名；`APP_VERSION`；额外 `fs:`/`shell:` 能力；Redis/Celery；S9.10–S9.13。

### S9.10 — 检查更新

仅菜单。GitHub Releases。启动不联网。

**现场空洞：** Help 只有 Shortcuts + About（`apps/desktop/src-tauri/src/menu.rs`）。`Cargo.toml` 仅有 window-state、single-instance、dialog、opener — 无 updater 插件。`tauri.conf.json` 没有 `plugins.updater`。CSP `connect-src` 仅 loopback。能力只有 `opener:allow-reveal-item-in-dir`。`lib.rs` setup 除 sidecar `/health` 外不联网。已知限制：**自动更新已推迟**；用户手动安装新构建。`.github/workflows/desktop.yml` 上传未签名 NSIS/DMG 产物，不发布 GitHub Release 资源或 Tauri `latest.json`。#167：仅菜单点击；查询 GitHub Releases；启动时不联网；无遥测；清单缺失 = 非致命 no-op；未签名构建仍须能启动。

**身份：** 仅桌面**检查**，不是自动安装。Help → **Check for updates**（id `check-for-updates`，无快捷键）。与 About 一样由原生拥有；JS `menuRoutes` 忽略它。只在该点击时查询 GitHub Releases。**不要**加 `tauri-plugin-updater`、download-and-install 或 `bundle.createUpdaterArtifacts`（签名 / 更新产物留给 S9.11）。缺少证书 / pubkey / `TAURI_SIGNING_PRIVATE_KEY` 不得阻止 `Builder`/`run`。永不读取或上传原片。无遥测、登录、支付或 GitHub token。

**网络：** Rust 辅助线程，不是 WebView。未认证 `GET https://api.github.com/repos/joe-cheung-cae/frame-pilot/releases/latest`。User-Agent `FramePilot/{CARGO_PKG_VERSION}`。超时约 10s。小型同步客户端（`ureq`）。不要在启动 / Ready / 定时器 / 设置页轮询。检查进行中时忽略第二次点击。CSP 不变。不要额外 `fs:` / `shell:` 能力；不要加 `opener:default`。

**清单：** Releases JSON 就是清单（必须有 `tag_name`；`html_url` 可选）。404 / 空 body / 缺 `tag_name` / 版本无法解析 → 清单缺失 → **非致命 no-op**（不 panic、不做阻塞错误；可选 stderr）。403 / 429 / 超时 / 5xx → 非致命本地对话框，不是崩溃。本切片不要求 Tauri `latest.json` 资源。

**比较：** 规范化 `tag_name` 与 `CARGO_PKG_VERSION`（`2.1.0-desktop`）：去掉前导 `v`，取 `-`/`+` 之前的 MAJOR.MINOR.PATCH。远端 core > 本地 → 有更新。否则已是最新。现场最新 tag `v2.0.0` 比 `2.1.0-desktop` 旧 → 已是最新。不改 `APP_VERSION`。

**UI：** 现有 `tauri-plugin-dialog` 消息。有更新：当前 vs 最新（Releases URL 作为文本）。已是最新：当前版本。浏览器/web 没有该项。不是 SettingsPanel。本切片不打开 URL。

**本计划（仅实现提交）：** 勾选 §3 S9.10 `[x]`（中英）。不要勾 S9.11–S9.13。

**文件：** `apps/desktop/src-tauri/src/updater.rs`（新建）；`apps/desktop/src-tauri/src/menu.rs`；`apps/desktop/src-tauri/src/lib.rs`；`apps/desktop/src-tauri/Cargo.toml`（+ `ureq` 的 lock）；`apps/web/src/lib/menuRoutes.test.ts`；`docs/v2_known_limitations.md`、用户指南、architecture、CHANGELOG Unreleased（+ zh）。不要把 `docs/desktop_development_plan.md` §2.2 / §5.4 / §5.6 改写成已交付（留给 S9.13）。不要改 `desktop.yml`（S9.11）。

**测试先行：** 菜单 id 存在、无快捷键、不是保留的精修键；`menuRoutes.test.ts` 里 `check-for-updates` 为 native-owned；`lib.rs` setup 不调用检查；404/空 JSON → no-op 枚举、不 panic；`v2.2.0` vs `2.1.0-desktop` → 有更新；`v2.0.0` / `v2.1.0` vs `2.1.0-desktop` → 当前；超时/403 不 panic；测试注入 status/body（不访问现场 GitHub）。`npm run verify` 仍不依赖 Rust。

**非目标：** 启动时 / 周期性检查；自动下载安装；`tauri-plugin-updater`；发布 `latest.json` 或签名（S9.11）；额外 `fs:`/`shell:`/`opener:default`；遥测；GitHub token；设置开关；`APP_VERSION`；把 §2.2 改写成已完成；S9.11–S9.13。

### S9.11 — 签名就绪 CI

`desktop.yml` 步骤按 secrets 门控。未签名路径保持绿灯。更新 `docs/desktop_signing.md`（+ zh）中的 secret 名。git 里不要证书。

**现场空洞：** `.github/workflows/desktop.yml` 文件头写着 **Unsigned builds only (signing is D4.05)**；`npx tauri build --bundles nsis|dmg` 没有签名环境变量；上传 `FramePilot-windows-nsis` / `FramePilot-macos-dmg`，`if-no-files-found: error`。`apps/desktop/src-tauri/tauri.conf.json` 的 identifier 是 `com.framepilot.app`，NSIS `currentUser`，没有 `certificateThumbprint` / `signingIdentity` / 公证字段。`docs/desktop_signing.md` 把典型材料标成**仅作示例**，不是确切的 GitHub secret 名。`scripts/check-release-artifacts.sh` 拦截 zip/sqlite/照片，但不拦 `.pfx` / `.p12` / `.p8`。D4.05 只交付了手册。#171：把 Authenticode / 公证接到 secrets 门控上；缺少 secrets 时保持今天的未签名上传；DoD 是 signing-ready，不是 SmartScreen 干净的公开发布；git 里不要证书；写明确切 secret 名。

**身份：** CI **签名就绪**，不是商店发行。保留现有 `npx tauri build` 路径（**不要**改成 `tauri-apps/tauri-action`；不要把 `contents` 升为 `write`；不要发布 GitHub Releases 或 Tauri `latest.json`）。当某平台的**完整** secret 集都非空时，在现有构建步骤里签署该平台安装包（Windows Authenticode 签 NSIS `.exe`；macOS Developer ID + 公证 + staple 签 `.app` / DMG）。当该平台任一必需 secret 缺失或为空时，跳过该平台签名，上传与今天相同的未签名产物；作业保持**绿灯**。若完整集已在场但签名 / 公证失败，作业为**红灯**（不要悄悄回退到未签名）。Windows 与 macOS 独立门控（`fail-fast: false` 保持）。永不读取或上传原片。无遥测、登录、支付或捆绑模型。

**Secrets（锁定的 GitHub Actions 名）：** Windows 仅在 **两个** `WINDOWS_CERTIFICATE`（base64 Authenticode `.pfx`）和 `WINDOWS_CERTIFICATE_PASSWORD` 都非空时签名。macOS 仅在 **全部** `APPLE_CERTIFICATE`（base64 Developer ID Application `.p12`）、`APPLE_CERTIFICATE_PASSWORD`、`APPLE_SIGNING_IDENTITY`、`APPLE_TEAM_ID`、`APPLE_API_ISSUER`、`APPLE_API_KEY`（App Store Connect Key ID）、`APPLE_API_KEY_CONTENT`（`.p8` 文件内容）都非空时签名并公证。`APPLE_API_KEY_PATH` 是由 `APPLE_API_KEY_CONTENT` 写出的 runner 临时路径，不是 GitHub secret。把 secrets 拷进 `env:` 再测非空；永不 echo 值。**不要**在空的时候 export `APPLE_CERTIFICATE`（Tauri 会尝试导入并失败）。本切片**不要**加 `APPLE_ID` / `APPLE_PASSWORD` / `KEYCHAIN_PASSWORD` / Azure Trusted Signing / `TAURI_SIGNING_PRIVATE_KEY`。

**Windows：** 完整集在场 → 在 runner 上解码 PFX，导入 `Cert:\CurrentUser\My`，算出 thumbprint，用**本地** `--config` 覆盖 `digestAlgorithm=sha256`、公开 DigiCert 时间戳 URL 和该 thumbprint 后执行 `npx tauri build --bundles nsis`。上传前删除解码出的 PFX。**不要**把 thumbprint 或 PFX 提交进 git。任一 secret 缺失 → 保持现在的未签名 `npx tauri build --bundles nsis`。

**macOS：** 完整集在场 → 在 `$RUNNER_TEMP` 下写 `AuthKey_${APPLE_API_KEY}.p8`，export APPLE_* 环境变量，执行 `npx tauri build --bundles dmg`（Tauri 导入 p12、签名、公证、staple）。上传前从 runner 删除 p12 / p8。任一必需 secret 缺失 → 保持现在的未签名 `npx tauri build --bundles dmg`，且不设置那些环境变量。

**CI 形态：** 保留 `on:`（`workflow_dispatch` + push `main` 路径过滤）、矩阵 `windows-latest` / `macos-latest`、sidecar 构建 + `npm run test:sidecar`、stage sidecar、现有产物名。不要启动打包 GUI。不要附加照片。`permissions.contents: read` 保持。文件头注释：signing-ready，按 secrets 门控，未签名回退必须绿灯。

**文档：** 把 `docs/desktop_signing.md`（+ zh）里「仅作示例」的表换成上面的确切名称（只写名称和用途；不要示例值）。写明：缺少 secrets → 未签名绿灯；完整 secrets → 签名；secrets 在场但签名失败 → 红灯。保留给内部测试者的未签名说明。

**Git 卫生：** 永不提交 `.pfx` / `.p12` / `.p8` / 私钥 / base64 证书内容。扩展 `scripts/check-release-artifacts.sh`，拒绝已跟踪的 `\.(pfx|p12|p8)$`。把这些 glob 加进 `.gitignore`。

**本计划（仅实现提交）：** 勾选 §3 S9.11 `[x]`（中英）。不要勾 S9.12–S9.13。

**文件：** `.github/workflows/desktop.yml`；`docs/desktop_signing.md`（+ zh）；`scripts/check-release-artifacts.sh`；`scripts/test-release-checks.sh`；`.gitignore`；`docs/v2_known_limitations.md`、README、CHANGELOG Unreleased（+ zh）。不要改 `verify.yml`。不要改 `APP_VERSION`。不要把 `docs/desktop_development_plan.md` §2.2 / §5.4 / §5.6 改写成已交付（留给 S9.13）。不要提交证书。

**测试先行：** `scripts/test-release-checks.sh` 断言 `desktop.yml` 引用锁定的 secret 名；Windows 导入/签名与 macOS 公证按非空 env 门控（不是无条件）；缺 secret 路径没有 `exit 1`；空的 `APPLE_CERTIFICATE` 不会被 export；`verify.yml` 仍无 codesign/notarize；`check:artifacts` 拒绝已跟踪的 `.pfx` / `.p12` / `.p8`。`npm run verify` 仍不依赖 Rust，也不跑 `desktop.yml`。

**非目标：** SmartScreen 信誉 / 公开商店上架；Mac App Store；Azure / DigiCert 云签名；`tauri-action` Release 发布；`tauri-plugin-updater` / `createUpdaterArtifacts` / `TAURI_SIGNING_PRIVATE_KEY` / `latest.json`；Apple ID + 应用专用密码认证；启动打包 GUI；S9.12 macOS DMG GUI QA；S9.13 残留文档；`APP_VERSION`；git 里的证书。

### S9.12 — macOS DMG QA

遵循 `docs/desktop_testing.zh.md`。没有 Mac → 带时间戳 skip，不是 pass。

### S9.13 — 文档残留修复

对齐 `docs/desktop_development_plan.zh.md` §2.2；已知限制；README；CHANGELOG；`implement_goals.zh.md`。在对应框变成 `[x]` 之前，不要声称 2.2 项已完成。PR 正文只在本 issue 之后才可写 `Fixes`。

---

## 6. 完成定义（整项）

- [x] §1.1 点名 S9.00–S9.13，并禁止发明第十阶段
- [ ] S9.01–S9.13 各自 `[x]`，且带 §4 的提交说明
- [ ] 测试中原片从未被修改
- [ ] S9.13 上线 前分支尖上 `npm run verify` 绿灯
- [ ] `feature/remaining-stretch` 只有一份草稿 PR；`Refs #160` 加子编号；S9.13 之前不要 `Fixes`
- [ ] 不改 `APP_VERSION`，无证书，无相机文件，无模型权重

---

## 7. 工作流执行

工作流不能启动其他工作流。一个带参数的文件：

| 运行 | 命令 |
| --- | --- |
| 下一个产品 issue | `/workflow remaining-stretch` 传入 `{"slice":"s901"}`（然后 `s902`…） |
| 文件 | `.grok/workflows/remaining-stretch.rhai` |

每次运行的仪表盘 `phase()` 标题就是该 issue id。phase 内部：需求拆解 → 评审（+ skeptic） → 归档 → 开发 → 测试 → 上线。

**分支：** 从 `origin/main` 拉出的 `feature/remaining-stretch`。每个 issue 后推送。永远不要第二份 PR。工作流不要合并进 `main`。不要 squash。不要 force-push。

**幂等：** 若 §3 已是 `[x]` 且 `git log origin/main..HEAD` 已有该提交说明，返回 `ok=true`，不要重做。

**失败即停：** `ok=false` 或 skeptic `real=false` → 停止。不要开始下一个切片。

建议 `agent_budget`: 32.

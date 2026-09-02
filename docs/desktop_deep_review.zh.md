# 桌面深审（apps/desktop、打包、sidecar API）

> Language: **中文** | [English](desktop_deep_review.md)

评审日期：2026-09-01。

对 FramePilot 桌面版 `2.1.0-desktop` 以及桌面相关 API（sidecar CLI、路径导入、任务回收、data-dir、Origin/Host）在 `main` `011fb61c745cf0eaac103ec3998db46095ace1cf` 上的文档-only 工程评审。来源：[GitHub issue #118](https://github.com/joe-cheung-cae/frame-pilot/issues/118)。

这**不是**产品导出。**XMP 不在范围**（[#117](https://github.com/joe-cheung-cae/frame-pilot/issues/117) 已关）。本次评审**未改生产代码**。

## 1. 结论

桌面壳、本机 sidecar、路径导入复制路径，以及 Phase 6 默认开启的启动回收，**适合继续作为内部桌面 RC**。已交付路径上安全红线成立：原图只复制不改写；sidecar 只绑 `127.0.0.1`；无云/更新器/遥测；Tauri 不会设置过宽的项目根 allowlist。

**无 critical / high 发现。** 三项 **medium** 留到本评审 rebase-merge 之后的跟进 PR：环境 allowlist 在操作者设成 `$HOME`/`/`/盘符根时不被 API 拒绝；`opener:default` 宽于“在文件夹中显示”；Windows 冻结 sidecar 的 smoke 可能被 `PYTHONPATH` 掩盖，且 spec 未列出 `uvicorn.loops.asyncio`。

**不要在本 PR 里开始修这些问题。**

## 2. 范围与方法

| 项 | 值 |
| -- | -- |
| 工作区 | `/workspace` |
| 检出 tip / 基线 | `main` @ `011fb61c745cf0eaac103ec3998db46095ace1cf`（`docs: close D3.04 with dated system theme WebView run`） |
| Diff 模式 | 对桌面 + 打包 + 桌面相关 API/共享 web 的树审查（不是仅 Phase 5 增量） |
| 产品版本 | `2.1.0-desktop` |
| 对照 | `docs/plans/2026-08-18-desktop-packaging.md`、Phase 6 `docs/plans/2026-08-29-phase6-durable-jobs.md`（含 §7 默认开启）、`AGENTS.md` / `develop_plan.md` 本地优先规则 |
| 不在范围 | XMP / HEIC / RAW / 模型；重做安装壳；D3.06 托盘；合入 [PR #41](https://github.com/joe-cheung-cae/frame-pilot/pull/41)；升版本；生产代码修复 |

### 审查面

- `apps/desktop` — Tauri 2 / Vite / Rust 生命周期（`sidecar.rs`、`lib.rs`、`menu.rs`、`data_dir.rs`）、`tauri.conf.json`、capabilities、原生 FS 适配、路由、主题 CSS
- `packaging/` — PyInstaller one-dir spec、`build.sh`、`stage-sidecar.sh`、`scripts/sidecar-smoke.sh`
- 桌面相关 API — `sidecar_main.py`、`origins.py` / Host 中间件、路径导入、项目根注册、`GET /api/meta`、Phase 6 回收（`jobs.py`、`main.py` lifespan、`worker.py`）
- 共享 `apps/web` — `shell.ts`、`apiBase.ts`、`StatusBar`、`SettingsPanel`、`Shell`、导航适配、ImportPanel / ExportPanel 桌面分支

### 明确不视为新缺口

| 项 | 原因 |
| -- | ---- |
| D0.07、D1.08、D3.01–D3.04 的带日期 GUI `[x]` 收尾 | 打包计划 tracker 已记录 rustc 1.98.0 / 实机 WebView 证据；本次未重开 GUI |
| D3.06 托盘 `[-]` | 2026-08-28 推迟；D5.05 已记录；未加 `fs:` / `shell:` 托盘能力 |
| 未签名 NSIS/DMG | 已接受的 RC 姿态（`docs/desktop_signing.md`、D5.05） |
| `GET /api/meta` 回环 `data_dir` | D3.03 Settings 有意为之；已做 Host 检查 |
| 500 张 GUI RSS 未测 | D5.03 / 性能基线已标 pending |
| [PR #41](https://github.com/joe-cheung-cae/frame-pilot/pull/41) | 已关闭、未合入，被 #45 取代；本次未合入 |

## 3. 安全红线

| 红线 | 已交付结果 | 本次是否触线 |
| ---- | ---------- | ------------ |
| 原图不得修改或删除 | 路径导入以 `rb` 打开源文件，经 `_copy_file_to_path` 写入 `originals/`；不可变测试断言 size / mtime / SHA-256；回收只改 job/derivative/group 行 | **否** |
| 只绑 `127.0.0.1` | CLI 对 `0.0.0.0` / 局域网 host 退出码 2；`localhost` 绑定时改写为 `127.0.0.1`；Tauri 始终传 `--host 127.0.0.1`；ready line 的 host 必须匹配 | **否** |
| 不接云 | 无 updater 插件、无登录/支付/遥测、无远程处理；Help About 无更新器 | **否** |
| 不写宽 allowlist | 默认 `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` 为空；Tauri 从不设置；放宽路径是 D2.00 注册。残留：API 会接受误设的环境变量（发现 M1） | **默认未触线**（见 M1） |

## 4. 按严重程度列出的发现

### 4.1 Medium

| ID | 路径 | 发现 | 安全红线 |
| -- | ---- | ---- | -------- |
| **M1** | `apps/api/app/core/config.py:34-44`，`apps/api/app/services/projects.py:30-35` | 环境 allowlist 接受 `$HOME` / `/` / 盘符根，API 不拒绝 | **默认未触线。** 若操作者导出过宽父目录，会废掉“不写宽 allowlist”控制。Tauri 不设置该变量。 |
| **M2** | `apps/desktop/src-tauri/capabilities/default.json:3-11` | `opener:default` 宽于“在文件夹中显示” IPC | **否** |
| **M3** | `scripts/sidecar-smoke.sh:32`，`packaging/pyinstaller/framepilot-api.spec:13-21`，`apps/api/app/sidecar_main.py:62-69` | Windows 冻结 sidecar 的 `/health` 未在去掉 `PYTHONPATH` 的条件下证明；spec 未列 `uvicorn.loops.asyncio`，而 Windows 强制该 loop | **否**（可用性 / 打包验证） |

#### M1 — 环境 allowlist 设宽时不被拒绝

**证据。** `get_settings()` 按 `os.pathsep` 拆分 `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST`，expand/resolve 后直接存入，没有 `$HOME` / 文件系统锚点 / 盘符根过滤：

```python
allowlist_raw = os.getenv("FRAMEPILOT_PROJECT_ROOT_ALLOWLIST", "")
# ...
allowlist.append(Path(cleaned).expanduser().resolve())
```

`create_project` 随后把这些条目当作允许的父目录（`projects.py:30-35`）。默认是 `[]`。注册（`project_roots.py`）**会**拦截 `/`、盘符根、Windows `\Windows`、以及 `data_dir` 及其父目录 — 但这套过滤**没有**用到环境 allowlist。

**计划。** 打包锁定决策 11 与 “What Not To Do” 要求 **Tauri 壳**不得把 allowlist 设为 `$HOME`、`/` 或盘符根。Tauri spawn（`sidecar.rs:467-477`）设置 `FRAMEPILOT_DESKTOP=1` 且**不**设置 allowlist（已确认 `apps/desktop` 下无 `FRAMEPILOT_PROJECT_ROOT_ALLOWLIST` 赋值）。D2.00 正文已警告把该环境变量设为 `$HOME` 会废掉该控制。

**QA 复核。** `rg FRAMEPILOT_PROJECT_ROOT_ALLOWLIST apps/desktop apps/api/app/core/config.py`。确认 `test_create_project_rejects_root_outside_allowlist` 仍在且保持全绿。可选：`FRAMEPILOT_PROJECT_ROOT_ALLOWLIST=$HOME` 后对家目录下的 `root_path` 做 `POST /api/projects` 目前会成功 — 这是缺口，不是已交付默认。

**建议跟进（不在本 PR）：** 对环境条目使用与 `register_root` 相同的助手，拒绝 `$HOME`、`/`、盘符根及其他被禁名称。

#### M2 — `opener:default` 宽于“在文件夹中显示”

**证据。** Capabilities：

```json
"permissions": [
  "core:default",
  "core:window:allow-show",
  "core:window:allow-unminimize",
  "core:window:allow-set-focus",
  "window-state:default",
  "dialog:default",
  "opener:default"
]
```

**没有** `fs:allow-*` 或 `shell:allow-open`（D3.06 托盘正确地一个都没加）。前端只调用 `revealItemInDir`（`apps/desktop/src/lib/nativeFs.ts:45-46`；菜单 Open data folder 在 `menu.rs:128-131`）。`opener:default` 是插件的完整默认集，通常还包含 open-url / open-path，而不是仅 reveal 的白名单。

**计划。** 锁定决策 4 / D2.01：可选 Tauri IPC 仅用于对话框、路径、在文件夹中显示。CSP `script-src 'self'` 降低 XSS 可达性；这是最小权限问题，不是绑定/云/原图红线。

**QA 复核。** 读 `apps/desktop/src-tauri/capabilities/default.json`。`rg "fs:|shell:" apps/desktop/src-tauri` 应继续没有文件系统/shell capability。

**建议跟进（不在本 PR）：** 用仅 reveal 的权限列表替换 `opener:default`。

#### M3 — 冻结 sidecar smoke 可能掩盖 Windows loop/导入缺口

**证据。**

1. `sidecar_main.serve` 在 Windows 上强制 `loop="asyncio"`（`sidecar_main.py:62-69`），因为可能没有 uvloop。
2. `framepilot-api.spec` 的 hiddenimports 有 `uvicorn.loops.auto`，**没有** `uvicorn.loops.asyncio`（也没有 `uvicorn.protocols.http.httptools_impl`）。`hook-app.py` 只 `collect_submodules("app")`。
3. `scripts/sidecar-smoke.sh:32` 总是 `export PYTHONPATH="$repo_root/apps/api..."`，即使被测进程是冻结的 `dist/framepilot-api/framepilot-api[.exe]`。打包后的 Tauri spawn **会移除** `PYTHONPATH`（`sidecar.rs:474-477`）。
4. `packaging/pyinstaller/build.sh` 在冻结后跑该 smoke；`.github/workflows/desktop.yml` 构建 NSIS/DMG 但**不**启动打包后的应用。

**计划。** D0.05 要求 hiddenimports 足以在启动后通过 `/health`。D1.04 生产 spawn 不得继承会遮蔽打包导入的父进程 `PYTHONPATH` — Rust 做到了；smoke 脚本与生产不一致。

**QA 复核。** 对比 smoke 环境与 `spawn_sidecar`。在 Windows 主机：冻结后 `env -u PYTHONPATH dist/framepilot-api/framepilot-api.exe --host 127.0.0.1 --port 0 --data-dir <abs>`，解析 ready line，再 `GET /health`。

**建议跟进（不在本 PR）：** 把 `uvicorn.loops.asyncio`（以及实际会导入的 http impl 模块）写入 spec；调用冻结二进制时不要导出 `PYTHONPATH`。

### 4.2 Low

| ID | 路径 | 发现 | 安全红线 |
| -- | ---- | ---- | -------- |
| **L1** | `apps/desktop/src-tauri/src/sidecar.rs:467-477` | Spawn 没有 `env_remove("FRAMEPILOT_PROJECT_ROOT_ALLOWLIST")`；父级 `tauri dev` shell 可能把宽 allowlist 泄漏进 sidecar | **否**（Tauri 不设置；与 M1 成对） |
| **L2** | `apps/api/app/core/project_roots.py:11`，`108-125` | `register_root` 不按名称拒绝 `Path.home()`。打包的 macOS/Windows 通常会拦，因为 `data_dir` 在 home 下（`_is_data_dir_or_parent`）。Linux/WSL **dev** 使用仓库 `.framepilot-desktop-dev`，注册 `$HOME` 可能成功。**跟进：** [#138](https://github.com/joe-cheung-cae/frame-pilot/issues/138) — `register_root` 现已按名拒绝当前家目录。 | 打包 OS app-support **否**；Linux desktop-dev **部分**（由 #138 关闭） |
| **L3** | `apps/desktop/src/lib/nativeFs.ts:75-77` 对比 `apps/web/src/lib/nativeFs.ts:10-12` | 桌面 `getNativeFs()` 总是返回适配器对象，从不 `null`。D2.01 的浏览器 null 是 web stub。非 Tauri 打开桌面 Vite 可能走原生选择器分支然后插件调用失败。**跟进：** [#140](https://github.com/joe-cheung-cae/frame-pilot/issues/140) — 桌面 `getNativeFs()` 现已在非 Tauri 时返回 `null`。 | **否**（由 #140 关闭） |
| **L4** | `apps/desktop/src/lib/nativeFs.ts:1`，`apps/desktop/package.json` | 导入 `@tauri-apps/api/webview` 但不是直接依赖（经插件传递）。**跟进：** [#142](https://github.com/joe-cheung-cae/frame-pilot/issues/142) — `apps/desktop/package.json` 现将 `@tauri-apps/api` 列为直接依赖，覆盖 `@tauri-apps/api/webview`。 | **否**（由 #142 关闭） |

### 4.3 备注（未达上报门槛 / 已文档化）

| ID | 路径 | 备注 | 安全红线 |
| -- | ---- | ---- | -------- |
| N1 | `apps/api/app/api/meta.py:10-12` | `GET /api/meta` 返回绝对 `data_dir`。Host 中间件仍生效。本机回环披露；D3.03 设计如此。Phase 5 评审已作低于门槛记录 | 否 |
| N2 | `apps/api/app/sidecar_main.py:84`，`{data_dir}/logs/sidecar.log` | Ready line 与 sidecar 日志含 `data_dir`。同用户本机可见 | 否 |
| N3 | `apps/web/src/lib/api.ts`（`export const API_BASE`） | 仍导出冻结常量；`request` / `assetUrl` / `exportDownloadUrl` 在调用时执行 `resolveApiBase()`（D1.02）。残留坑只影响日后在延迟注入之后读取 `API_BASE` 的代码 | 否 |
| N4 | `apps/desktop/src-tauri/src/sidecar.rs:289-296` | 回环端口先分配、关掉 listener，再传 `--port <n>`（TOCTOU）。计划 D1.04 指定该模式；ready line 端口不匹配会快速失败；已交付路径从不传 `--port 0` | 否 |
| N5 | `apps/desktop/src-tauri/tauri.conf.json` 的 `withGlobalTauri` | 退出对话框需要 `window.__TAURI__.event.emit`。相对纯 invoke 扩大了页面 IPC 面 | 否 |
| N6 | `apps/desktop/src-tauri/src/sidecar.rs` 退出遮罩 CSS | 写死 `#fff` / system-ui，未用 `--fp-*`。D3.04 壳主题本身已实现 | 否 |
| N7 | `apps/api/app/core/config.py:32-33` | 非 sidecar 的 `get_settings()` 仍回退 CWD `.framepilot-data`。Sidecar 的 `--data-dir` 必填，且在 `import app.main` 之前生效 | sidecar 路径否 |
| N8 | `.github/workflows/desktop.yml` | CI 上传未签名 NSIS/DMG；不启动打包 GUI。已文档化 | 否 |
| N9 | `apps/web/src/components/ExportPanel.tsx` | 浏览器下载是 `<a href={exportDownloadUrl(...)}>`，没有 HTML `download` 属性。桌面走 reveal（`isDesktopShell()`）。不是 WebView 下载回退 | 否 |

## 5. 已核对无问题的区域

| 区域 | 结果 |
| ---- | ---- |
| Sidecar CLI（D0.01） | `--host` 必须是 `127.0.0.1` 或 `localhost`（否则退出码 2）；`--data-dir` 必填且绝对；在 `import app.main` 前设置 `FRAMEPILOT_DATA_DIR`；绑 IPv4 回环；仅 POSIX 设 `SO_REUSEADDR`（`os.name != "nt"`）；ready line 打 stdout 且 `flush=True`，端口来自 `getsockname()`；uvicorn 日志走 stderr；把 FastAPI 对象传给 `Server` |
| Health（D0.02） | `/health` 与 `/api/health` 返回 `status` / `version`（`APP_VERSION`）/ `service` |
| Origin + Host（D0.03） | **所有**方法（含 GET）做 Host 检查；缺 Host 拒绝；变更请求的 Origin 白名单；CORS 无 `*`；仅当 `FRAMEPILOT_DESKTOP=1` 时加入桌面 origin（`origins.py`，`main.py:117-131`；`test_desktop_origins.py`） |
| 路径导入（D0.04） | 绝对路径；`os.walk(..., followlinks=False)`；上限 5000/20000；跳过项目根下的源；每批 100 + `remaining_paths`；`source.open("rb")` → `register_import_file` → `_copy_file_to_path` 仅对目标 `wb`；`test_import_from_paths_immutability.py` |
| 项目根（D2.00 / D2.07） | 非桌面环境端点 404；注册表 `{data_dir}/desktop_project_roots.json` 上限 50；`test_create_project_rejects_root_outside_allowlist` 仍在 |
| Data dir（D1.05） | 打包：macOS Application Support / Windows `%APPDATA%\FramePilot` / Linux `~/.local/share/FramePilot`；开发：`.framepilot-desktop-dev`；打包拒绝 CWD `.framepilot-data` 文件名 |
| 生命周期（D1.04 / D1.09 / J6.07） | 分配回环端口，注入 `__FRAMEPILOT_API_BASE__` 与 `__FRAMEPILOT_DESKTOP__ = true`；崩溃：自动重启一次后阻塞错误页；关闭/Cmd+Q 共用 `app_quit_action` → 对话框；导入可取消再 SIGTERM；处理任务无取消；文案感知回收；等待取消时把 `interrupted` 当终态；窗口 Destroyed/Exit 停止 sidecar |
| 菜单（D3.01 / D3.07） | File/Edit/View/Project/Help；加速键只有 `CmdOrCtrl+N/W/Q`；无裸 P/M/X/U；About 用 `CARGO_PKG_VERSION`；无更新器 |
| 状态栏（D3.02） | 仅桌面；`Shell` 传入 `usePathname()`；jobs key `["jobs", projectId]`；不读 `window.location` / 不导入 `menuRoutes` |
| 设置（D3.03） | 只读 data dir；仅桌面有“打开数据文件夹”；不提供更改 data dir |
| 主题（D3.04） | 仅在 `html[data-shell="desktop"]` + `prefers-color-scheme: dark` 下替换 token；浏览器保持浅色 |
| 共享导航（D1.01） | 组件只从 `@/lib/navigation` 导入；Vite 把 `navigation.next` 别名到 `navigation.router.tsx`；`apps/web/src/components` 无 `next/link` |
| API base（D1.02 / D1.02a） | `resolveApiBase()` 为 window → env → `http://127.0.0.1:8000`；`isDesktopShell()` 仅 `=== true` |
| 导入 / 导出 UI（D2.03 / D2.09） | 桌面路径导入 + remaining-paths 循环；`!desktopShell` 时保留浏览器 `<input type="file">` + `webkitdirectory`；桌面 reveal vs 浏览器下载 href |
| CSP（D0.07） | 与锁定 CSP 一致：`default-src 'self'`；回环 `img-src`/`connect-src`；`object-src 'none'`；`frame-ancestors 'none'` |
| 打包（D4.01 / D4.02） | `targets: ["nsis","dmg"]`；identifier `com.framepilot.app`；resources 为 one-dir `framepilot-api`（不是 `externalBin`）；制品检查例外仍是 `^apps/desktop/src-tauri/icons/[^/]+\.(png\|ico\|icns)$` |
| Phase 6 回收 | `job_reclaim_on_startup` 默认 `True`（`config.py`）；`ensure_db_ready` 里 `reconcile_active_jobs_on_startup`；`start_reclaimable_jobs` 在 lifespan，**不在** `GET /api/projects`（`routes.py:331-337` 写明只读）；导出仍 fail-and-cleanup；lease claim 避免与 `python -m app.worker` 双跑（#104）；不改写原图 |
| 云 / 更新器 | `Cargo.toml` 仅有 window-state、single-instance、dialog、opener — 无 updater 插件 |

## 6. 计划对齐快照

| 来源 | 对齐情况 |
| ---- | -------- |
| 打包 Phase 0–5 tracker | 所有必做 id 为 `[x]` 或推迟 `[-]`（D3.06、D4.03）。GUI `[x]` 收尾日期为 2026-08-31 |
| 锁定决策 1–16 | 成立，残留缺口见上方 M1/M2/M3 |
| Phase 6 J6.01–J6.08 + 6.1 默认开启 | 已落地；J6.07 退出文案匹配回收默认；GET 列表不做回收写入 |
| `AGENTS.md` 红线 | 原图 / 绑定 / 云成立；allowlist 在默认成立（M1 残留） |

## 7. 建议

1. Rebase-merge **本 docs-only 评审 PR**。在该合入之前不要开始生产修复。
2. 合入后，另开实现 PR 处理 M1–M3（allowlist 拒绝、opener 范围、冻结 smoke 的 `PYTHONPATH` + `uvicorn.loops.asyncio`）。
3. **不要**重开 D3.06 托盘、重做安装壳、升版本、做 XMP，或合入 PR #41（已关闭）。
4. 任何**公开签名**发布前，仍以 D4.05 / D5.05 的未签名安装包说明与签名手册为门禁（已文档化；此处不是新缺口）。

---

2026-09-01 针对 `011fb61c745cf0eaac103ec3998db46095ace1cf`、issue #118 生成。无生产代码变更。

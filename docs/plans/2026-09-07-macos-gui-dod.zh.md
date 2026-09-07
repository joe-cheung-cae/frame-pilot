# 残留：双平台安装包 GUI DoD（macOS DMG 安装并运行）

> 语言：[English](2026-09-07-macos-gui-dod.md) | **中文**

**GitHub：** [joe-cheung-cae/frame-pilot#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177)。2026-09-07 检索后新建（open：无；最近残留是已关闭的 [#175](https://github.com/joe-cheung-cae/frame-pilot/issues/175)；最近 PR 是 [#176](https://github.com/joe-cheung-cae/frame-pilot/pull/176)）。不要重开 [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172)。Windows pass 仍是 [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144)。

**分支：** 从 `origin/main` 建 `feature/macos-gui-dod`。`isolation_worktree` 为 false。不要为了提交切回 `main`。不要合进 `main`。不要 squash。不要 force-push。

**相关：** `develop_plan.zh.md` §1.1；`docs/desktop_development_plan.zh.md` §2.2 与 §5.6；`docs/desktop_testing.zh.md` S9.12 skip 记录；工作流 `.grok/workflows/macos-gui-dod.rhai`。

需求拆解 只写文档合同。评审 已按现场树修正规格漏洞。本次 归档 提交只记录 开发 交接。还不要实现冒烟脚本，也不要改 `.github/workflows/desktop.yml`。不要勾 开发、DoD-ticked 或 §2.2。

---

## 1. 为什么是残留，不是第十阶段

第九阶段 remaining-stretch（S9.00–S9.13）已在 `main` 关闭（[#174](https://github.com/joe-cheung-cae/frame-pilot/pull/174)）。残留 cache 旋钮已交付（[#175](https://github.com/joe-cheung-cae/frame-pilot/issues/175)）。

活指针仍把 **macOS GUI pass** 列为未排期。双平台安装包 GUI DoD **尚未声称**：Windows NSIS GUI 是 pass（[#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144)，2026-09-04 按 Windows-only 关闭）；S9.12 包装 macOS DMG GUI 生命周期（[#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172)）是 **skip，不是 pass**，日期 `2026-09-05T12:31:10Z`（Linux/WSL2；`uname -s` 不是 Darwin）。skip 不是 macOS pass。

用户批准的残留是 **安装并运行 DoD**，不是完整重跑 S9.12 生命周期，也不是新的编号阶段。不要发明第十阶段 / S10 / 2.3。只有在 `desktop.yml` macOS GUI 冒烟绿灯且带日期的 Darwin 证据之后，才勾 `docs/desktop_development_plan.md` §2.2 安装包那一行。

---

## 2. 锁定决策

1. **本地优先。** 不上传云端、无登录、无支付、不捆绑神经网络模型。
2. **永不修改或删除原片。** 这次残留冒烟不导入照片。不要提交相机照片、证书或模型权重。
3. **DoD 是安装并运行**，不是完整 S9.12 退出+作业矩阵。同一 job 内 DMG attach + 启动 + 回环 `GET /health` 就足以勾 §2.2。
4. **skip ≠ pass。** `docs/desktop_testing.md` 里 S9.12 skip 小节作为历史保留。pass 必须另写带日期的 Darwin 结果小节。
5. **Windows 已经是 pass。** 不要重跑 Windows NSIS GUI。不要把 #144 当 macOS 载体重开。
6. **不要重开 #172。** 新残留 issue 只是 [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177)。
7. **CI 同一 job 的 DMG**，不要从别的 job 下载产物。现场树 `.github/workflows/desktop.yml` 是一个 matrix `build` job（`os: [windows-latest, macos-latest]`），不是单独的 macOS job。在该现有 job 上**新增一步**，用 `if: runner.os == 'macOS'` 门控，在 `npx tauri build --bundles dmg` 之后，对着刚打出的 `apps/desktop/src-tauri/target/release/bundle/dmg/*.dmg`。不要再开一个 job 去下载 `FramePilot-macos-dmg`。不要把冒烟塞进 `Build Tauri installer` 那一步（`scripts/test-release-checks.sh` 禁止该步出现 `exit 1`）。
8. **`verify.yml` 保持无 Rust。** 不要从 `verify.yml` 启动包装 GUI。`npm run verify` 不得要求 `rustc` / `cargo` / Tauri（`typecheck:desktop` 是 `tsc --noEmit`）。
9. **仅 Darwin 做 attach/启动。** 非 Darwin 主机（Linux/WSL2 的 开发/测试）必须打印 skip is not pass，并以非零退出（用 2）。Linux 上永远不要打印 pass。GitHub 托管的 `macos-latest` 是 Darwin（`uname -s`）；attach/启动路径**必须**在那里跑。不要把该 runner 当成 S9.12 的 Linux skip。
10. **不改 `APP_VERSION`。** 产品名 / 窗口标题仍是 `FramePilot`。版本仍是 `2.1.0-desktop`。
11. **本残留不签名。** 不要求 secrets、不新增签名/公证、不声称 Gatekeeper 干净或商店上架。保留 `desktop.yml` 里现有的 S9.11 按 secret 门控的签名/公证分支（不要删掉）。secrets 缺失时，未签名 Gatekeeper 警告仍是预期。
12. **不勾包装桌面 ≥500 GUI。** Web Playwright `test:e2e:real-browser:large` 与 API `perf:api` 500 不是包装桌面 GUI 证据。
13. **草稿目录：** `mkdir -p "$HOME/.cache/framepilot-macos-gui-dod" && chmod 700`。密钥或 QA 照片不要放 `/tmp`。
14. **代码、注释、测试、提交说明用英文。** 活文档双语。
15. **`feature/macos-gui-dod` 对 `main` 只开一个草稿 PR。** 标题：`ci: macOS DMG installer GUI smoke (leftover DoD)`。正文写 `Refs` [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177)；在证据提交（上线，且 `desktop.yml` macOS GUI 冒烟绿灯）之前，不得写 `Fixes` 或 `Close`。永远不要第二个 PR。
16. **不做：** 第十阶段、包装桌面 ≥500 GUI、签名、重跑 Windows、完整退出+作业矩阵、`APP_VERSION` 升级。

---

## 3. 状态板

残留双平台安装包 GUI DoD（macOS DMG 安装并运行）

- [x] 需求拆解 — 双语残留计划 + GitHub issue
- [x] 评审 — 对照现场树对抗评审
- [x] 归档 — 已记录 开发 交接（本次提交）；开发 保持 `[ ]`
- [x] 开发 — 冒烟脚本 + `desktop.yml` macOS 步骤；同一提交勾残留计划 开发 `[x]`；**不要**勾 §2.2
- [ ] 测试
- [ ] 上线 — 派发 `desktop.yml`，带日期的 Darwin 证据，然后勾 §2.2
- [x] smoke-landed
- [ ] DoD-ticked

本次 归档 提交只勾 **归档**。开发、smoke-landed、DoD-ticked 与 §2.2 保持 `[ ]`。

---

## 4. 冒烟脚本合同（开发，不是本次提交）

**测试先行。** 增加 `tests/desktop/macos-dmg-gui-smoke-nondarwin.sh`（或等价物），在本机跑 `packaging/scripts/macos-dmg-gui-smoke.sh`，断言非零退出 **且** stdout/stderr 含 `skip is not pass`。先看着它因冒烟脚本缺失而失败，再实现冒烟脚本，让主机检查在 Linux 上通过。

新建 `packaging/scripts/macos-dmg-gui-smoke.sh`，使用 `set -euo pipefail`。attach/启动路径仅 Darwin。

要求行为：

1. 若 `uname -s` 不是 Darwin，打印 skip is not pass，非零退出（用 2）。Linux 上永远不要打印 pass。
2. 需要 `.dmg` 路径参数。`hdiutil attach -nobrowse`。把 `FramePilot.app` 拷到 `$HOME/.cache/framepilot-macos-gui-dod` 下的一次性目录（不要 `/tmp`）。对拷贝做 `xattr -cr`。`open` 该 `.app`。
3. 最多轮询 30s（必要时 `open` 重试一次）等待 sidecar ready。**不要把 `{data_dir}/logs/sidecar.log` 当成 ready 行来源。** 现场树：`sidecar_main.py` 把 `FRAMEPILOT_API ready host=127.0.0.1 port=<n> data_dir=<path>` 打到 **stdout**；`spawn_sidecar` 把 stdout 管道给 Tauri 父进程，把 **stderr**（uvicorn）追加到 sidecar.log。桌面壳用 `allocate_loopback_port()` 分配临时端口并传入 `--port <n>`（从不 `--port 0`）。从 `framepilot-api` 的 argv `--port` **或** `lsof` 看到 `framepilot-api` 在 `127.0.0.1` 上 LISTEN 来发现端口。拒绝 `0.0.0.0`。永远不要写死端口 `8000`/`6300`。永远不要把 sidecar.log 里 uvicorn 的 “running on …:8000” 当成绑定端口（Config 默认是 8000；真正端口是分配出来的）。可以顺带扫 sidecar.log 里的 ready 前缀；**没有不算失败**。
4. `GET http://127.0.0.1:<n>/health` 必须是带 `version` 与 `service` 的 200 JSON（现场 payload 还有 `status`）。打印 `APP_VERSION`。回环请求必须绕过代理，做法同 `tests/desktop/smoke.sh`（`curl --noproxy '*'` 和/或 unset `http_proxy`/`HTTP_PROXY`）。
5. 尽力用 `lsappinfo` 或 `osascript` 核对窗口标题 `FramePilot`。失败则记录 `title_ok=false` 和确切错误；若进程+health 已成功，冒烟仍可 pass。
6. 退出 `FramePilot.app`（sidecar 是该进程的子进程）；等待；没有残留 `framepilot-api` LISTEN（`TIME_WAIT` 可以）。只杀 `framepilot-api` 不算 GUI 退出。`hdiutil detach`。删除拷贝的 `.app`。数据目录可以留下（`~/Library/Application Support/FramePilot`，不是 `com.framepilot.app`）。
7. 打印机器可读摘要：`os`、带 `Z` 的 UTC ISO-8601 时间戳、health json、port、`title_ok`、`result=pass`。

不要导入照片。不要自动化退出+导入/处理/导出对话框。

Ready 行与日志路径（现场树，本残留除非必要不要改）：

- Ready 前缀：`FRAMEPILOT_API ready `（`apps/desktop/src-tauri/src/sidecar.rs`）
- 格式：`FRAMEPILOT_API ready host=127.0.0.1 port=<n> data_dir=<path>`（`framepilot-api` 的 stdout，由 Tauri 消费；**不保证**出现在 sidecar.log）
- 冻结二进制：`framepilot-api`，argv 为 `--host 127.0.0.1 --port <n> --data-dir <abs>`
- 包装日志：`{data_dir}/logs/sidecar.log` 是 **stderr** → macOS `~/Library/Application Support/FramePilot/logs/sidecar.log`
- 窗口标题 / productName：`FramePilot`（`apps/desktop/src-tauri/tauri.conf.json`）；identifier `com.framepilot.app` 不是数据目录文件夹名
- Sidecar 暂存：`packaging/scripts/stage-sidecar.sh` 把 `dist/framepilot-api` 拷进 `apps/desktop/src-tauri/resources/framepilot-api`

优先零处 Rust/Python/TypeScript 生产改动。不要改 `verify.yml`。不要加 Playwright GUI。不要加会打开 WebView 的 pytest。

---

## 5. `desktop.yml` 仅 macOS 接线（开发，不是本次提交）

当前 `.github/workflows/desktop.yml` 是**单个 matrix `build` job**（`windows-latest` + `macos-latest`，`fail-fast: false`）。它构建 NSIS/DMG、跑冻结 sidecar `/health`、上传产物，**不**启动包装 GUI。页眉写：不要启动包装 NSIS/DMG GUI。`on:` 是 `workflow_dispatch` 加上带路径过滤的 `main` push（PR 不跑此 workflow）。

开发必须：

- 在该现有 `build` job 上**新增一步**，`if: runner.os == 'macOS'`（与 `Upload macOS DMG` 同一门控），在 `npx tauri build --bundles dmg` 之后，对着刚打出的 `apps/desktop/src-tauri/target/release/bundle/dmg/*.dmg`（仓库根路径；构建步骤的 `working-directory` 是 `apps/desktop`）。
- 不要再开一个 `needs:` matrix 再下载 `FramePilot-macos-dmg` 的后续 job。
- 不要把 `hdiutil` / `open` / 冒烟塞进 `Build Tauri installer` 那一步。
- 更新页眉：本次冒烟允许在 macOS 启动包装 GUI；仍不启动 NSIS；仍不从 `verify.yml` 启动 GUI。
- Windows 保持现有未签名/已签名 NSIS 上传路径，不启动 GUI。S9.11 按 secret 门控的签名保持原样。
- `scripts/test-release-checks.sh` 必须保持绿灯（`npm run test` 含 `test:scripts`）。只有需要新断言时才改它。

---

## 6. 勾选规则

| 何时 | 勾 | 不要勾 |
| ---- | -- | ------ |
| 需求拆解 | 残留板 需求拆解 `[x]` | 开发、DoD-ticked、§2.2 安装包行 |
| 评审 | 残留板 评审 `[x]` | 开发、DoD-ticked、§2.2 安装包行 |
| 归档（本次提交） | 残留板 归档 `[x]` | 开发、smoke-landed、DoD-ticked、§2.2 安装包行 |
| 开发 | 残留板 开发 `[x]`；主机检查通过才勾 smoke-landed `[x]` | §2.2 安装包行；DoD-ticked |
| 上线 Darwin 冒烟绿灯 | 残留板 上线 `[x]` 与 DoD-ticked `[x]`；`docs/desktop_development_plan.md` §2.2 安装包行 `[x]`，写上 Windows #144 + 残留 [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177) + Actions run URL；§5.6 包装 macOS GUI pass 的 Target = 本残留 `[x]`（**安装并运行** DoD），注明完整退出+作业矩阵仍未排期 | 包装桌面 ≥500；Gatekeeper 干净；商店上架；第十阶段 |

绿灯证据提交主题（仅 上线）：`docs: record dual-platform installer GUI DoD pass`。

该提交**必须**在 `docs/desktop_testing.md`（+ zh）新增带日期的结果小节，S9.12 skip 小节作为历史保留；更新 `develop_plan.md` §1.1（+ zh）、`docs/v2_known_limitations.md`（+ zh）、`README.md`（+ zh）、CHANGELOG 未发布（+ zh）、`implement_goals.md`（+ zh）。时间戳用带时区的 ISO-8601（UTC `Z` 可以）。

红灯或 skip：不要勾 §2.2。在残留 [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177) 上评论 run URL 和失败摘录。不声称 DoD。

---

## 7. 非目标

- 第十阶段 / S10 / 2.3 编号
- 包装桌面 ≥500 GUI
- 签名、公证、Gatekeeper 干净声称、商店上架
- 重跑 Windows NSIS GUI
- 完整 S9.12 退出+导入/处理/导出对话框矩阵
- `APP_VERSION` 升级
- 从 `verify.yml` 启动包装 GUI
- 本次残留冒烟导入照片
- 重开 #172
- 第二个 PR；合进 `main`；squash；force-push

---

## 8. 文件图

| 文件 | 需求拆解 | 评审 | 归档（本次提交） | 开发 | 上线 |
| ---- | -------- | ---- | ---------------- | ---- | ---- |
| `docs/plans/2026-09-07-macos-gui-dod.md`（+ zh） | 新建；需求拆解 `[x]` | 漏洞 + 评审 `[x]` | 勾 归档 + §11 交接；开发 保持 `[ ]` | 勾 开发 | 勾 上线 + DoD-ticked |
| `.grok/workflows/macos-gui-dod.rhai` | 若存在则纳入 | 不变 | 不变 | 不变 | 不变 |
| `packaging/scripts/macos-dmg-gui-smoke.sh` | 不做 | 不做 | **不做** | 新建 | 不变 |
| `tests/desktop/macos-dmg-gui-smoke-nondarwin.sh` | 不做 | 不做 | **不做** | 新建 | 不变 |
| `.github/workflows/desktop.yml` | 不做 | 不做 | **不做** | 新增 macOS 门控步骤 + 页眉 | 不变 |
| `.github/workflows/verify.yml` | 不做 | 不做 | **不要改** | **不要改** | **不要改** |
| `scripts/test-release-checks.sh` | 不做 | 不做 | 不做 | 保持绿灯；只有需要新断言时才改 | 不做 |
| `docs/desktop_development_plan.md`（+ zh）§2.2 | **不要勾** | **不要勾** | **不要勾** | **不要勾** | 仅 Darwin 绿灯才勾安装包行 |
| `docs/desktop_testing.md`（+ zh） | 不做 | 不做 | 不做 | 不做 | 新增带日期结果小节；保留 S9.12 skip |
| `develop_plan.md` §1.1、已知限制、README、CHANGELOG、`implement_goals.md`（+ zh） | 不做 | 不做 | 不做 | 不做 | 仅证据提交 |

开发以**本评审后的计划**为准，不要跟 `.grok/workflows/macos-gui-dod.rhai` 的 `develop_prompt` 里评审前那套 sidecar.log 措辞。

---

## 9. GitHub / PR

每个阶段提交完成后：`git push -u origin HEAD`。本分支第一次成功推送后，若还不存在 head 为 `feature/macos-gui-dod`、base 为 `main` 的打开 PR，则创建**一个**草稿 PR：

- 标题：`ci: macOS DMG installer GUI smoke (leftover DoD)`
- 正文：`Refs` [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177)；历史 `Refs` #144 / #172。在证据提交（上线）之前不得写 `Fixes` 或 `Close`。永远不要 `Fixes #172`。

回退：GitHub MCP `create_pull_request`，`draft` 为 true。永远不要第二个 PR。

每次推送后把 SHA、主题、推送结果、PR URL 追加到 `$HOME/.cache/framepilot-macos-gui-dod/git-github.txt`。

若提交因空 ident 失败，只为该命令设置 `GIT_AUTHOR_NAME`、`GIT_AUTHOR_EMAIL`、`GIT_COMMITTER_NAME`、`GIT_COMMITTER_EMAIL`，与 `git log -1 --format='%an <%ae>'` 一致。不要加 Co-authored-by Cursor 一类 trailer。不要跑 `git config --global` 或 `git config user.name`。

---

## 10. 评审结论（评审，2026-09-07）

对照 `feature/macos-gui-dod` 上 需求拆解 之后的现场树评审。确认：

- DoD 是 **安装并运行**，不是完整 S9.12 退出+作业矩阵。`docs/desktop_development_plan.md` §2.2 安装包行仍是 `[ ]`。开发 不要勾它。
- `docs/desktop_testing.md` 的 S9.12 是 **skip，不是 pass**，日期 `2026-09-05T12:31:10Z`（Linux/WSL2）。该小节保留。不要重开 [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172)。
- Windows NSIS GUI pass 仍是已关闭的 [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144)（仅 Windows，2026-09-04）。不要重跑。
- 残留 issue 是 [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177)（与 GitHub 一致）。草稿 PR 是 [#178](https://github.com/joe-cheung-cae/frame-pilot/pull/178)。没有第十阶段 / S10 / 2.3。
- `.github/workflows/verify.yml` 不安装 Rust；`npm run verify` 是 lint / typecheck / `tsc --noEmit` / pytest / `test:scripts`。保持无 Rust。不要从 `verify.yml` 启动 GUI。
- `APP_VERSION` / productName / 窗口标题是 `2.1.0-desktop` / `FramePilot`。不要升级。
- 包装后 macOS 数据目录是 `~/Library/Application Support/FramePilot`（`apps/desktop/src-tauri/src/data_dir.rs`），不是 `com.framepilot.app`。
- Health 是 `GET /health` → JSON `status`、`version`、`service`。

本次提交修掉的漏洞（现场树让 需求拆解 规格写错了）：

1. **ready 行不在 sidecar.log。** stdout 管道给 Tauri；sidecar.log 是 stderr。从 `--port` / `lsof` 在 `127.0.0.1` 上发现端口。不要信 uvicorn `:8000`。
2. **`desktop.yml` 是一个 matrix `build` job。** 新增 `if: runner.os == 'macOS'` 步骤；不要下载产物的第二 job；不要塞进 `Build Tauri installer`。
3. **不签名** 指本残留不新增/不要求/不声称签名。保留 S9.11 按 secret 门控的签名/公证。
4. **`macos-latest` 是 Darwin。** 退出码 2 的 skip 给 Linux/WSL2 的 开发/测试，不是给 macOS runner。
5. **回环 GET 必须绕过代理**，与 `tests/desktop/smoke.sh` 相同。

非漏洞：Windows job 仍上传 NSIS 且不启动 GUI；不勾包装桌面 ≥500；草稿目录不是 `/tmp`；本残留不导入照片；活文档只在 上线 勾选。

---

## 11. 归档交接（归档，2026-09-07）

评审后的计划已锁定给 开发。状态：需求拆解 `[x]`，评审 `[x]`，归档 `[x]`。开发 仍是 `[ ]`（本分支还没有 `ci: smoke packaged macOS DMG GUI launch` 提交）。

**开发必须**在主题为 `ci: smoke packaged macOS DMG GUI launch` 的同一提交里：

1. 按 §4 落地 `packaging/scripts/macos-dmg-gui-smoke.sh` 与 `tests/desktop/macos-dmg-gui-smoke-nondarwin.sh`（测试先行）。
2. 按 §5 在现有 `.github/workflows/desktop.yml` matrix `build` job 上新增 macOS 门控步骤。
3. **同一提交**勾残留计划 开发 `[x]`（英+中）。
4. `git push -u origin HEAD`。不要开第二个 PR（草稿 PR 是 [#178](https://github.com/joe-cheung-cae/frame-pilot/pull/178)）。
5. **不要**勾 `docs/desktop_development_plan.md` §2.2 安装包行。**不要**勾 DoD-ticked。只有 上线 在 `desktop.yml` macOS GUI 冒烟绿灯且带日期的 Darwin 证据之后才勾 §2.2。

本次 归档 提交不要实现冒烟脚本。以**本评审后的计划**（§4–§5）为准，不要跟 `.grok/workflows/macos-gui-dod.rhai` 的 `develop_prompt` 里评审前那套 sidecar.log 措辞。

指针：残留 [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177)；Windows pass [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144)；S9.12 skip [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172) 保持 skip；不要重开 #172。

---

## 12. 开发（2026-09-07）

已落地 `packaging/scripts/macos-dmg-gui-smoke.sh`、`tests/desktop/macos-dmg-gui-smoke-nondarwin.sh`，以及现有 `.github/workflows/desktop.yml` matrix `build` job 上的 macOS 门控步骤（对着刚打出的 DMG；不在 `Build Tauri installer` 内）。Linux 主机检查：skip is not pass（退出码 2）。**不要**勾 `docs/desktop_development_plan.md` §2.2。**不要**勾 DoD-ticked。测试 / 上线 下一步：派发 `desktop.yml` 以取得带日期的 Darwin 证据。草稿 PR 仍是 [#178](https://github.com/joe-cheung-cae/frame-pilot/pull/178)。

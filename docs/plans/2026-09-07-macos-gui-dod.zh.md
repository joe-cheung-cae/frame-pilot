# 残留：双平台安装包 GUI DoD（macOS DMG 安装并运行）

> 语言：[English](2026-09-07-macos-gui-dod.md) | **中文**

**GitHub：** [joe-cheung-cae/frame-pilot#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177)。2026-09-07 检索后新建（open：无；最近残留是已关闭的 [#175](https://github.com/joe-cheung-cae/frame-pilot/issues/175)；最近 PR 是 [#176](https://github.com/joe-cheung-cae/frame-pilot/pull/176)）。不要重开 [#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172)。Windows pass 仍是 [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144)。

**分支：** 从 `origin/main` 建 `feature/macos-gui-dod`。`isolation_worktree` 为 false。不要为了提交切回 `main`。不要合进 `main`。不要 squash。不要 force-push。

**相关：** `develop_plan.zh.md` §1.1；`docs/desktop_development_plan.zh.md` §2.2 与 §5.6；`docs/desktop_testing.zh.md` S9.12 skip 记录；工作流 `.grok/workflows/macos-gui-dod.rhai`。

本次 需求拆解 提交只写文档合同。还不要实现冒烟脚本，也不要改 `.github/workflows/desktop.yml`。

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
7. **CI 同一 job 的 DMG**，不要从别的 job 下载产物。只接 macOS，在 `npx tauri build --bundles dmg` 之后，对着刚打出的 `apps/desktop/src-tauri/target/release/bundle/dmg/*.dmg`。
8. **`verify.yml` 保持无 Rust。** 不要从 `verify.yml` 启动包装 GUI。`npm run verify` 不得要求 `rustc` / `cargo` / Tauri。
9. **仅 Darwin 做 attach/启动。** 非 Darwin 主机必须打印 skip is not pass，并以非零退出（用 2）。Linux 上永远不要打印 pass。
10. **不改 `APP_VERSION`。** 产品名 / 窗口标题仍是 `FramePilot`。版本仍是 `2.1.0-desktop`。
11. **不签名。** 不声称 Gatekeeper 干净或商店上架。未签名 Gatekeeper 警告仍是预期。
12. **不勾包装桌面 ≥500 GUI。** Web Playwright `test:e2e:real-browser:large` 与 API `perf:api` 500 不是包装桌面 GUI 证据。
13. **草稿目录：** `mkdir -p "$HOME/.cache/framepilot-macos-gui-dod" && chmod 700`。密钥或 QA 照片不要放 `/tmp`。
14. **代码、注释、测试、提交说明用英文。** 活文档双语。
15. **`feature/macos-gui-dod` 对 `main` 只开一个草稿 PR。** 标题：`ci: macOS DMG installer GUI smoke (leftover DoD)`。正文写 `Refs` [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177)；在证据提交（上线，且 `desktop.yml` macOS GUI 冒烟绿灯）之前，不得写 `Fixes` 或 `Close`。永远不要第二个 PR。
16. **不做：** 第十阶段、包装桌面 ≥500 GUI、签名、重跑 Windows、完整退出+作业矩阵、`APP_VERSION` 升级。

---

## 3. 状态板

残留双平台安装包 GUI DoD（macOS DMG 安装并运行）

- [x] 需求拆解 — 双语残留计划 + GitHub issue（本次提交）
- [ ] 评审
- [ ] 归档
- [ ] 开发 — 冒烟脚本 + `desktop.yml` macOS 步骤；同一提交勾残留计划 开发 `[x]`；**不要**勾 §2.2
- [ ] 测试
- [ ] 上线 — 派发 `desktop.yml`，带日期的 Darwin 证据，然后勾 §2.2
- [ ] smoke-landed
- [ ] DoD-ticked

本次 需求拆解 提交只勾 **需求拆解**。开发 与 DoD-ticked 保持 `[ ]`。

---

## 4. 冒烟脚本合同（开发，不是本次提交）

**测试先行。** 增加 `tests/desktop/macos-dmg-gui-smoke-nondarwin.sh`（或等价物），在本机跑 `packaging/scripts/macos-dmg-gui-smoke.sh`，断言非零退出 **且** stdout/stderr 含 `skip is not pass`。先看着它因冒烟脚本缺失而失败，再实现冒烟脚本，让主机检查在 Linux 上通过。

新建 `packaging/scripts/macos-dmg-gui-smoke.sh`，使用 `set -euo pipefail`。attach/启动路径仅 Darwin。

要求行为：

1. 若 `uname -s` 不是 Darwin，打印 skip is not pass，非零退出（用 2）。Linux 上永远不要打印 pass。
2. 需要 `.dmg` 路径参数。`hdiutil attach -nobrowse`。把 `FramePilot.app` 拷到 `$HOME/.cache/framepilot-macos-gui-dod` 下的一次性目录（不要 `/tmp`）。对拷贝做 `xattr -cr`。`open` 该 `.app`。
3. 最多轮询 30s（必要时 `open` 重试一次）等待 sidecar ready：解析 `~/Library/Application Support/FramePilot/logs/sidecar.log` 中的 `FRAMEPILOT_API ready host=127.0.0.1 port=<n>`，**或** `lsof` 看到 `framepilot-api` 在 `127.0.0.1` 上 LISTEN。拒绝 `0.0.0.0`。永远不要写死端口 `8000`/`6300`。
4. `GET http://127.0.0.1:<n>/health` 必须是带 `version` 与 `service` 的 200 JSON。打印 `APP_VERSION`。
5. 尽力用 `lsappinfo` 或 `osascript` 核对窗口标题 `FramePilot`。失败则记录 `title_ok=false` 和确切错误；若进程+health 已成功，冒烟仍可 pass。
6. 退出应用；等待；没有残留 `framepilot-api` LISTEN（`TIME_WAIT` 可以）。`hdiutil detach`。删除拷贝的 `.app`。数据目录可以留下。
7. 打印机器可读摘要：`os`、带 `Z` 的 UTC ISO-8601 时间戳、health json、port、`title_ok`、`result=pass`。

不要导入照片。不要自动化退出+导入/处理/导出对话框。

Ready 行与日志路径（现场树，本残留除非必要不要改）：

- Ready 前缀：`FRAMEPILOT_API ready `（`apps/desktop/src-tauri/src/sidecar.rs`）
- 格式：`FRAMEPILOT_API ready host=127.0.0.1 port=<n> data_dir=<path>`
- 包装日志：`{data_dir}/logs/sidecar.log` → macOS `~/Library/Application Support/FramePilot/logs/sidecar.log`
- 窗口标题 / productName：`FramePilot`（`apps/desktop/src-tauri/tauri.conf.json`）
- Sidecar 暂存：`packaging/scripts/stage-sidecar.sh` 把 `dist/framepilot-api` 拷进 `apps/desktop/src-tauri/resources/framepilot-api`

优先零处 Rust/Python/TypeScript 生产改动。不要改 `verify.yml`。不要加 Playwright GUI。不要加会打开 WebView 的 pytest。

---

## 5. `desktop.yml` 仅 macOS 接线（开发，不是本次提交）

当前 `.github/workflows/desktop.yml` 构建 NSIS/DMG、跑冻结 sidecar `/health`、上传产物，**不**启动包装 GUI。页眉写：不要启动包装 NSIS/DMG GUI。

开发必须：

- 只接到 **macOS job**，在 `npx tauri build --bundles dmg` 之后，对着刚打出的 `apps/desktop/src-tauri/target/release/bundle/dmg/*.dmg`。
- 更新页眉：本次冒烟允许在 macOS 启动包装 GUI；仍不启动 NSIS；仍不从 `verify.yml` 启动 GUI。
- Windows 保持现有未签名/已签名 NSIS 上传路径，不启动 GUI。

---

## 6. 勾选规则

| 何时 | 勾 | 不要勾 |
| ---- | -- | ------ |
| 需求拆解（本次提交） | 残留板 需求拆解 `[x]` | 开发、DoD-ticked、§2.2 安装包行 |
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

| 文件 | 本次提交 | 开发 | 上线 |
| ---- | -------- | ---- | ---- |
| `docs/plans/2026-09-07-macos-gui-dod.md`（+ zh） | 新建；需求拆解 `[x]` | 勾 开发 | 勾 上线 + DoD-ticked |
| `.grok/workflows/macos-gui-dod.rhai` | 若存在则纳入 | 不变 | 不变 |
| `packaging/scripts/macos-dmg-gui-smoke.sh` | 不做 | 新建 | 不变 |
| `tests/desktop/macos-dmg-gui-smoke-nondarwin.sh` | 不做 | 新建 | 不变 |
| `.github/workflows/desktop.yml` | 不做 | macOS 冒烟步骤 + 页眉 | 不变 |
| `.github/workflows/verify.yml` | 不做 | **不要改** | **不要改** |
| `docs/desktop_development_plan.md`（+ zh）§2.2 | **不要勾** | **不要勾** | 仅 Darwin 绿灯才勾安装包行 |
| `docs/desktop_testing.md`（+ zh） | 不做 | 不做 | 新增带日期结果小节；保留 S9.12 skip |
| `develop_plan.md` §1.1、已知限制、README、CHANGELOG、`implement_goals.md`（+ zh） | 不做 | 不做 | 仅证据提交 |

---

## 9. GitHub / PR

每个阶段提交完成后：`git push -u origin HEAD`。本分支第一次成功推送后，若还不存在 head 为 `feature/macos-gui-dod`、base 为 `main` 的打开 PR，则创建**一个**草稿 PR：

- 标题：`ci: macOS DMG installer GUI smoke (leftover DoD)`
- 正文：`Refs` [#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177)；历史 `Refs` #144 / #172。在证据提交（上线）之前不得写 `Fixes` 或 `Close`。永远不要 `Fixes #172`。

回退：GitHub MCP `create_pull_request`，`draft` 为 true。永远不要第二个 PR。

每次推送后把 SHA、主题、推送结果、PR URL 追加到 `$HOME/.cache/framepilot-macos-gui-dod/git-github.txt`。

若提交因空 ident 失败，只为该命令设置 `GIT_AUTHOR_NAME`、`GIT_AUTHOR_EMAIL`、`GIT_COMMITTER_NAME`、`GIT_COMMITTER_EMAIL`，与 `git log -1 --format='%an <%ae>'` 一致。不要加 Co-authored-by Cursor 一类 trailer。不要跑 `git config --global` 或 `git config user.name`。

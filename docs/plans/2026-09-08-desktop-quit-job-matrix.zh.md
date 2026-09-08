# 残留：包装 macOS 退出+作业矩阵（2026-09-08）

> 语言：[English](2026-09-08-desktop-quit-job-matrix.md) | **中文**

**GitHub：** [joe-cheung-cae/frame-pilot#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181)。2026-09-08 检索后新建（open：无；最近残留是已关闭的 [#179](https://github.com/joe-cheung-cae/frame-pilot/issues/179)，经 [#180](https://github.com/joe-cheung-cae/frame-pilot/pull/180) 合入）。不要重开 [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144)、[#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172)、[#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177)。不要折进 `macos-dmg-gui-smoke.sh` 或 `desktop-500-gui.sh`。

**分支：** 从 `origin/main` @ `d75a8dc` 建 `cursor/desktop-quit-job-matrix-186e`。`isolation_worktree` 为 false。不要为了提交切回 `main`。不要合进 `main`。不要 squash。不要 force-push。

**相关：** `develop_plan.zh.md` §1.1；`docs/desktop_development_plan.zh.md` §2.2 与 §5.6；`docs/desktop_testing.zh.md`；`.github/workflows/desktop.yml`。实现已合入 [#182](https://github.com/joe-cheung-cae/frame-pilot/pull/182)。

---

## 1. 为什么是残留，不是第十阶段

第九阶段 remaining-stretch 已在 `main` 关闭（[#174](https://github.com/joe-cheung-cae/frame-pilot/pull/174)）。缓存旋钮（[#175](https://github.com/joe-cheung-cae/frame-pilot/issues/175)）、双平台安装并运行（[#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177)）、包装桌面 ≥500 GUI（[#179](https://github.com/joe-cheung-cae/frame-pilot/issues/179)）已交付。

本残留开始时 `develop_plan.md` §1.1 仍把 **完整包装 macOS 退出+作业矩阵** 列为未排期。[#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177) 只认 **安装并运行**。[#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172) S9.12 仍是 **skip，不是 pass**。[#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144) 仍是 Windows-only 历史（Quit clean / Quit+导入；分组/导出退出对话是后来加的）。本残留后来经 [#182](https://github.com/joe-cheung-cae/frame-pilot/pull/182) 合入 `main`，再加本上线文档戳。

不要发明第十阶段 / S10 / 2.3。产品仍是 `2.1.0-desktop`。不升 `APP_VERSION`。

---

## 2. 锁定决策

1. **本地优先。** 不上传云端、无登录、无支付、无遥测、不捆绑神经网络模型。
2. **永不修改或删除原片。** 只走 copy-mode `POST .../imports/from-paths`。不要提交相机照片、证书或模型权重。不要把照片、项目库或导出树挂到 GitHub artifacts。
3. **DoD 是同一 `desktop.yml` `macos-latest` job 上的四行 Darwin：** Quit clean、Quit+导入、Quit+分组排序、Quit+导出。四行都 `result=pass` 才能勾。
4. **Path B 只负责起 job。** 原生选文件夹对话框仍 stub。生产退出路径是 File → Quit / `osascript` quit / `ExitRequested` → `handle_close_requested` → `#framepilot-quit-dialog`。Path B 点击 `[data-choice=cancel_and_quit]`。
5. **失败关闭的 `qa_request_close`。** QA 关闭时返回错误。ACL 仍只在 `capabilities/qa.json` 的 **main**。不要把 QA 命令放到 `default.json`。不加 `fs:` / `shell:`。仅在 Apple Event 退出不稳时使用。
6. **同一 job 的未签名 DMG。** 不要从第二个 job 下载安装包。不要折进 `macos-dmg-gui-smoke.sh` 或 `desktop-500-gui.sh`。
7. **`verify.yml` 保持无 Rust。** 不要从 `verify.yml` 启动包装 GUI。
8. **skip ≠ pass。** Linux/WSL2：打印 `skip is not pass`，**exit 2**，永远不要 `result=pass`。GHA `macos-latest`：**失败（exit 1）**，不要 skip。
9. **不改 `APP_VERSION`。** 窗口标题仍是 `FramePilot`。版本仍是 `2.1.0-desktop`。
10. **本残留不签名。** 不声称 Gatekeeper 干净或商店上架。
11. **草稿前缀：** `$HOME/.cache/framepilot-desktop-quit-job`（`chmod 700`）。QA 照片不要放 `/tmp`。同级目录：`photos/`、`project/`、`data/`、`evidence/`（可选 `app/`）。失败关闭的前缀门必须接受此前缀，并继续接受 #179 的 `framepilot-desktop-500-gui`。
12. **500** 张生成的 3000×2000 q88 JPEG，让导入/分组/导出足够久以便取消。GHA [34227247641](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/34227247641) 上 30 张分组在 cancel 发出时已经是 `complete`（HTTP 200，不是 202）。不要在生产代码里加 sleep。
13. **Keep working / Quit anyway** 仍由 Rust 单元测试覆盖。包装证据仍须在点 Cancel 之前记录三个按钮都在。
14. **Windows 不是本残留的勾选项。** 不要重开 #144。
15. **代码、注释、测试、提交说明用英文。** 活文档双语。
16. **一个草稿 PR。** 标题：`ci: packaged macOS quit+job matrix (leftover)`。正文 `Refs` [#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181)；`Refs` #177 / #144 / #172 作历史。四行 Darwin 都绿之前不要写 `Fixes`。永远不要第二个 PR。
17. **排除：** 第十阶段、Path C、包装 Stay/Quit anyway 点击、Windows DoD、sidecar 崩溃 / 端口占用 / 装卸载行、升 `APP_VERSION`、把退出折进 #177/#179 脚本。

---

## 3. 状态板

残留包装 macOS 退出+作业矩阵

- [x] 需求拆解 — 双语残留计划 + GitHub issue [#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181)
- [x] 开发 — Path B 退出模式 + harness + `desktop.yml` macOS 步骤
- [x] 测试 — Linux skip-not-pass + `npm run verify`
- [x] 上线 — [desktop.yml run 34230112750](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/34230112750)（`8658e14`，`2026-09-08T13:26:18Z`）四行 Darwin `result=pass`；实现已合入 [#182](https://github.com/joe-cheung-cae/frame-pilot/pull/182)（仅 `Refs`）；本上线文档戳使用 `Fixes` [#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181)
- [x] DoD-ticked — 残留板上线 + `docs/desktop_development_plan.md` §5.6 退出+作业 `[x]` 带 run URL；**不要**重勾 §2.2

失败的 Darwin 记录作为历史保留：[34209655915](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/34209655915)（`osascript` 在 `quit_dialog` 前退出）；[34227247641](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/34227247641)（30 张分组已是 `complete`）。Skip ≠ pass。不要再伪造 Darwin 通过。

---

## 4. 行

| 行 | Path B 模式 | 通过条件 |
| --- | ----------- | ---- |
| Quit clean | `quit-clean` | 无活动作业；sidecar 退出；无残留 `framepilot-api` LISTEN（`TIME_WAIT` 可以）；不要求退出对话 |
| Quit + 导入 | `quit-import` | 标题 `Import is still running`；按钮 stay / cancel_and_quit / quit_anyway；点 cancel；作业 `cancelled`；原片未改 |
| Quit + 分组排序 | `quit-processing` | 标题 `Grouping and ranking is still running`；点 cancel；部分组被清掉；原片未改 |
| Quit + 导出 | `quit-export` | 标题 `Export is still running`；点 cancel；项目导出根下的部分导出物被清掉；原片未改 |

每条 CancelAndQuit 行在作业进入 `queued` 或 `running` 时立刻写 JSONL `*_running`，然后等 `#framepilot-quit-dialog`。退出前**不要**等 `complete`。Quit clean 只写 `idle`；harness 负责退出。

四次包装启动（CancelAndQuit 会退出应用）。

---

## 5. 勾选规则

| 时机 | 勾 | 不要勾 |
| ---- | ---- | ----------- |
| 需求拆解 | 残留板 需求拆解 | 开发、DoD-ticked、§5.6 退出+作业 |
| 开发 | 残留板 开发 | §5.6 退出+作业；§2.2 安装并运行 / ≥500 |
| 上线且 Darwin 四行都绿 | 残留板 上线 + DoD-ticked；`docs/desktop_development_plan.md` §5.6 退出+作业 `[x]` 带 run URL；§1.1 未排期清单去掉本残留 | 重勾 §2.2；Gatekeeper 干净；商店上架；第十阶段 |

上线证据提交说明（仅上线）：`docs: record packaged macOS quit+job matrix leftover pass`。

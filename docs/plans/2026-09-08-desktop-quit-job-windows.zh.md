# 残留：包装 Windows 退出+作业矩阵（2026-09-08）

> 语言：[English](2026-09-08-desktop-quit-job-windows.md) | **中文**

**GitHub：** [joe-cheung-cae/frame-pilot#184](https://github.com/joe-cheung-cae/frame-pilot/issues/184)。2026-09-08 在包装 macOS 退出+作业矩阵已交付后新建（[#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181) / [#182](https://github.com/joe-cheung-cae/frame-pilot/pull/182) / [#183](https://github.com/joe-cheung-cae/frame-pilot/pull/183)，[desktop.yml run 34230112750](https://github.com/joe-cheung-cae/frame-pilot/actions/runs/34230112750)）。不要重开 [#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144)、[#172](https://github.com/joe-cheung-cae/frame-pilot/issues/172)、[#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177)、[#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181)。不要折进 `macos-dmg-gui-smoke.sh` 或 `desktop-500-gui.sh`。复用/扩展 `packaging/scripts/desktop-quit-job-gui.sh`。

**分支：** 从 `origin/main` @ `cf79b1829c9f22e52431bec971c1040b8f0ffae4` 建 `cursor/desktop-quit-job-windows-7bb0`。`isolation_worktree` 为 false。不要为了提交切回 `main`。不要合进 `main`。不要 squash。不要 force-push。

**相关：** `develop_plan.zh.md` §1.1；`docs/desktop_development_plan.zh.md` §2.2 与 §5.6；`docs/desktop_testing.zh.md`；`.github/workflows/desktop.yml`。macOS 残留计划：[2026-09-08-desktop-quit-job-matrix.zh.md](2026-09-08-desktop-quit-job-matrix.zh.md)。草稿 PR [#185](https://github.com/joe-cheung-cae/frame-pilot/pull/185)。

---

## 1. 为什么是残留，不是第十阶段

第九阶段 remaining-stretch 已在 `main` 关闭（[#174](https://github.com/joe-cheung-cae/frame-pilot/pull/174)）。缓存旋钮（[#175](https://github.com/joe-cheung-cae/frame-pilot/issues/175)）、双平台安装并运行（[#177](https://github.com/joe-cheung-cae/frame-pilot/issues/177)）、包装桌面 ≥500 GUI（[#179](https://github.com/joe-cheung-cae/frame-pilot/issues/179)）、包装 macOS 退出+作业矩阵（[#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181)）已交付。

本残留开始时 `develop_plan.md` §1.1 把 **包装 Windows 退出+作业矩阵** 列为 Darwin #181 之后的下一最低桌面门禁。[#144](https://github.com/joe-cheung-cae/frame-pilot/issues/144) 仍是 Windows-only 历史（Quit clean / Quit+导入；分组/导出退出对话是后来加的）。**不要**重开它。

不要发明第十阶段 / S10 / 2.3。产品仍是 `2.1.0-desktop`。不升 `APP_VERSION`。

---

## 2. 锁定决策

1. **本地优先。** 不上传云端、无登录、无支付、无遥测、不捆绑神经网络模型。
2. **永不修改或删除原片。** 只走 copy-mode `POST .../imports/from-paths`。不要提交相机照片、证书或模型权重。不要把照片、项目库或导出树挂到 GitHub artifacts。
3. **DoD 是同一 `desktop.yml` `windows-latest` job 上的四行 Windows：** Quit clean、Quit+导入、Quit+分组排序、Quit+导出。四行都 `result=pass` 才能勾。
4. **Path B 只负责起 job。** 原生选文件夹对话框仍 stub。生产退出路径是 File → Quit / 关窗 / `CloseRequested` / `ExitRequested` → `handle_close_requested` → `#framepilot-quit-dialog`。Path B 点击 `[data-choice=cancel_and_quit]`。做法与残留 [#181](https://github.com/joe-cheung-cae/frame-pilot/issues/181) / [#182](https://github.com/joe-cheung-cae/frame-pilot/pull/182) 相同。
5. **失败关闭的 `qa_request_close`。** QA 关闭时返回错误。ACL 仍只在 `capabilities/qa.json` 的 **main**。不要把 QA 命令放到 `default.json`。不加 `fs:` / `shell:`。作业行在 `quit_dialog` 前不得 `CloseMainWindow` / `taskkill`。
6. **同一 job 的未签名 NSIS。** 不要从第二个 job 下载安装包。不要折进 `macos-dmg-gui-smoke.sh` 或 `desktop-500-gui.sh`。复用/扩展 `desktop-quit-job-gui.sh`。
7. **`verify.yml` 保持无 Rust。** 不要从 `verify.yml` 启动包装 GUI。
8. **skip ≠ pass。** Linux/WSL2：打印 `skip is not pass`，**exit 2**，永远不要 `result=pass`。GHA `windows-latest`：**失败（exit 1）**，不要 skip。
9. **不改 `APP_VERSION`。** 窗口标题仍是 `FramePilot`。版本仍是 `2.1.0-desktop`。
10. **本残留不签名。** 不声称 SmartScreen 干净或商店上架。
11. **草稿前缀：** `%LOCALAPPDATA%\framepilot-desktop-quit-job`（`chmod 700` / 等价 ACL）。QA 照片不要放 `/tmp`。同级目录：`photos/`、`project/`、`data/`、`evidence/`（可选 `app/`）。失败关闭的前缀门必须接受此前缀，并继续接受 #179 的 `framepilot-desktop-500-gui` 以及 #181 的 POSIX `$HOME/.cache/framepilot-desktop-quit-job`。
12. **500** 张生成的 3000×2000 q88 JPEG，让导入/分组/导出足够久以便取消。不要在生产代码里加 sleep。
13. **Keep working / Quit anyway** 仍由 Rust 单元测试覆盖。包装证据仍须在点 Cancel 之前记录三个按钮都在。
14. **不要重开 #144 / #172 / #177 / #181。** Darwin #181 通过记录作为历史保留。不要重勾 §2.2 安装并运行 / ≥500。
15. **代码、注释、测试、提交说明用英文。** 活文档双语。
16. **一个草稿 PR。** 标题：`ci: packaged Windows quit+job matrix (leftover)`。正文 `Refs` [#184](https://github.com/joe-cheung-cae/frame-pilot/issues/184)；`Refs` #181 / #177 / #144 / #172 作历史。四行 Windows 都绿之前不要写 `Fixes`。实现者不合入。
17. **排除：** 第十阶段、Path C、包装 Stay/Quit anyway 点击、重开 #144、sidecar 崩溃 / 端口占用 / 装卸载行、升 `APP_VERSION`、签名、XMP、合入 #41、重开 D3.06、把退出折进 #177/#179 脚本。

---

## 3. 状态板

残留包装 Windows 退出+作业矩阵

- [x] 需求拆解 — 双语残留计划 + GitHub issue [#184](https://github.com/joe-cheung-cae/frame-pilot/issues/184)
- [x] 开发 — Path B Windows NSIS 启动 + 生产 `CloseMainWindow` 干净退出 + `desktop.yml` windows 步骤
- [x] 测试 — Linux skip-not-pass + packaged-path Windows 检查 + `npm run verify`
- [ ] 上线 — 同一次 `desktop.yml` `windows-latest` 四行 `result=pass`；证据可下载
- [ ] DoD-ticked — 残留板上线 + `docs/desktop_development_plan.md` §5.6 Windows 退出+作业 `[x]` 带 run URL；**不要**重勾 §2.2 / ≥500 / Darwin #181

Skip ≠ pass。不要伪造 Windows 通过。

---

## 4. 行

| 行 | Path B 模式 | 通过条件 |
| --- | ----------- | ---- |
| Quit clean | `quit-clean` | 无活动作业；sidecar 退出；无残留 `framepilot-api` LISTEN（`TIME_WAIT` 可以）；不要求退出对话；生产关窗（`CloseMainWindow` / `CloseRequested`） |
| Quit + 导入 | `quit-import` | 标题 `Import is still running`；按钮 stay / cancel_and_quit / quit_anyway；点 cancel；作业 `cancelled`；原片未改 |
| Quit + 分组排序 | `quit-processing` | 标题 `Grouping and ranking is still running`；点 cancel；部分组被清掉；原片未改 |
| Quit + 导出 | `quit-export` | 标题 `Export is still running`；点 cancel；项目导出根下的部分导出物被清掉；原片未改 |

每条 CancelAndQuit 行在作业进入 `queued` 或 `running` 时立刻写 JSONL `*_running`，然后等 `#framepilot-quit-dialog`。退出前**不要**等 `complete`。Quit clean 只写 `idle`；harness 走生产关窗。

四次包装启动（CancelAndQuit 会退出应用）。NSIS 安装一次，启动四次。

---

## 5. 勾选规则

| 时机 | 勾 | 不要勾 |
| ---- | ---- | ----------- |
| 需求拆解 | 残留板 需求拆解 | 开发、DoD-ticked、§5.6 Windows 退出+作业 |
| 开发 | 残留板 开发 | §5.6 Windows 退出+作业；§2.2 安装并运行 / ≥500；Darwin #181 |
| 上线且 Windows 四行都绿 | 残留板 上线 + DoD-ticked；`docs/desktop_development_plan.md` §5.6 Windows 退出+作业 `[x]` 带 run URL；§1.1 未排期清单去掉本残留 | 重勾 §2.2；重戳 Darwin #181；SmartScreen 干净；商店上架；第十阶段 |

上线证据提交说明（仅上线）：`docs: record packaged Windows quit+job matrix leftover pass`。

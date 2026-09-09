# 残留：NSIS 升级在 sidecar `_internal` 被锁时停住（2026-09-09）

> 语言：[English](2026-09-09-nsis-locked-internal-upgrade.md) | **中文**

**GitHub：** [joe-cheung-cae/frame-pilot#198](https://github.com/joe-cheung-cae/frame-pilot/issues/198)。Joe 在 Win11 上升级未签名 `v2.1.2-desktop` NSIS 时，对 `%LOCALAPPDATA%\FramePilot\framepilot-api\_internal\MSVCP140.dll` 出现 **Error opening file for writing**。连续点**忽略**后留下残缺的 `_internal` 树；新建工程导入/导出空白。这是残缺安装，不是 [#195](https://github.com/joe-cheung-cae/frame-pilot/pull/195) 回退。不要重开 [#194](https://github.com/joe-cheung-cae/frame-pilot/issues/194)、[#196](https://github.com/joe-cheung-cae/frame-pilot/issues/196) 或 [#190](https://github.com/joe-cheung-cae/frame-pilot/issues/190)。不要动 [#41](https://github.com/joe-cheung-cae/frame-pilot/issues/41) / D3.06 托盘。不要发明第十阶段。

**分支：** `cursor/nsis-locked-internal-upgrade-b75d`。不要合入 `main`。实现者不合入。

**相关：** `develop_plan.md` §1.1；[docs/desktop_install.md](../desktop_install.zh.md)；`apps/desktop/src-tauri/windows/hooks.nsh`；`apps/desktop/src-tauri/tauri.conf.json`（`bundle.windows.nsis.installerHooks`）。

---

## 1. 为什么是残留，不是第十阶段

第九阶段 remaining-stretch 已关闭。Tauri 自带 NSIS 的 `CheckIfAppIsRunning` 只停 `${MAINBINARYNAME}.exe`（`framepilot-desktop.exe`）。PyInstaller one-dir sidecar `framepilot-api.exe` 仍锁着 `_internal` DLL。NSIS 随后提供 Abort / Retry / **Ignore**。Ignore 会越过被锁文件，装出残缺树。

本残留接上 `NSIS_HOOK_PREINSTALL` / `NSIS_HOOK_PREUNINSTALL`：升级/安装在壳、sidecar 与已知锁目标空闲之前**停住**，对话框只有 Retry / Cancel（没有 Ignore）。Cancel 在 File 拷贝**之前** Abort，因此旧的 `_internal` 树不会被写到一半。

**不要**发明第十阶段 / S10 / 2.3。产品字符串仍是 `2.1.0-desktop`。不改 `APP_VERSION`。合入后再开未签名 Release tag 是后续件——不是本 issue。

---

## 2. 已锁定决定

1. **本地优先。** 无云上传、登录、付费、遥测或捆绑神经模型。
2. **先拦住再重试。** 提示 **File → Quit**。Retry 可以强杀 `framepilot-desktop.exe` / `FramePilot.exe` / `framepilot-api.exe`（先杀壳，避免 sidecar 监督进程再拉起）。Cancel / 静默仍被锁则 **Abort**。禁止 `MB_ABORTRETRYIGNORE` / `IDIGNORE` / `SetOverwrite try`。
3. **探测已存在的锁目标：** 主程序、`framepilot-api.exe`、`_internal\MSVCP140.dll`、`_internal\VCRUNTIME140.dll`。
4. **只做未签名。** 不 Authenticode、不公证、不 staple、无 SmartScreen 豁免、不上架。不声称 Win11 GUI pass。
5. **不改 `APP_VERSION`。** 不用 `tauri-action`。不动托盘 / D3.06 / #41。
6. **一个 draft PR。** 正文必须含 `Closes #198`。实现者不合入。
7. **不做：** 新的未签名 tag/Release、签名、第十阶段、在 `_internal` 不完整时把空白导入/导出当成 #195 回退。

---

## 3. 状态板

残留 NSIS 锁定 `_internal` 升级

- [x] 需求拆解 — 中英残留计划 + GitHub 议题 [#198](https://github.com/joe-cheung-cae/frame-pilot/issues/198)
- [x] 开发 — `installerHooks` PREINSTALL/PREUNINSTALL 在壳/sidecar 仍运行或 `_internal` 被锁时拦住；教程 + 矩阵验收步骤
- [x] 测试 — `scripts/check-nsis-locked-upgrade-hooks.sh`；`npm run test:scripts`
- [ ] 上线 — 合入 + 从 `desktop.yml` 打出新的未签名 NSIS（实现者不合入）
- [ ] DoD-ticked — 有 #198+ NSIS 之后再勾残留计划上线；**不要**编造带日期的 Win11 GUI pass / 第十阶段 / 重勾 §2.2

---

## 4. 勾选规则

| 何时 | 勾 | 不要勾 |
| ---- | -- | ------ |
| 需求拆解 | 残留板 需求拆解 | 上线；§2.2 |
| 开发 + 脚本检查 | 残留板 开发 + 测试 | 上线；Gatekeeper 干净；商店上架；Win11 GUI pass |
| 已发布 #198+ NSIS（Actions 或后续 Release） | 残留板上线 + DoD-ticked；§1.1 本残留已交付 | 重勾 §2.2；公开签名清单；第十阶段；编造 Win11 pass |

---

## 5. Win11 验收：应用仍在运行时升级

本 PR 不要编造通过。等有 #198+ NSIS 之后在真机 Win11 走此路径。

1. 先装一份旧的未签名 NSIS（`v2.1.2-desktop` 可作为基线）。
2. 启动 **FramePilot**。等到项目 UI 出来（sidecar 已启动）。**不要**退出。
3. 跑**新的** NSIS（本残留的 `desktop.yml` 产物，或之后的未签名 Release——不要用缺少 hooks 的同一份 `v2.1.2-desktop`）。
4. **通过：** 安装程序**停住**，Retry / Cancel 提示关闭 FramePilot / `framepilot-api`。没有一路 Ignore 的 **Error opening file for writing**。**Cancel** 保持原来的 `%LOCALAPPDATA%\FramePilot` 树完整（`_internal` 没有写到一半）。
5. 在 FramePilot：**File → Quit**（或退出后再点 **Retry**，让 hook 强关残留进程）。走完向导。
6. **通过：** 装完后 `%LOCALAPPDATA%\FramePilot\framepilot-api\_internal\MSVCP140.dll` 存在。冷启动 → 新建工程 → 导入 / 导出能打开（与 #195 一致）。
7. **失败：** 靠 Ignore 才能装完；因为 `_internal` 残缺，导入/导出仍空白。

已发布的 `v2.1.2-desktop` NSIS **不含**这些 hook。若旧向导出现 **Error opening file for writing**，点 **Abort**，退出 FramePilot，再重试——永远不要点 Ignore。

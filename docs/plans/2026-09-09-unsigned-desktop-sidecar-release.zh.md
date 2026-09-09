# 残留：含 sidecar 冷首启修的未签名桌面 Release（2026-09-09）

> 语言：[English](2026-09-09-unsigned-desktop-sidecar-release.md) | **中文**

**GitHub：** [joe-cheung-cae/frame-pilot#192](https://github.com/joe-cheung-cae/frame-pilot/issues/192)。在 Windows 包装 sidecar ready-line 修合入 `main` 之后开立（[#190](https://github.com/joe-cheung-cae/frame-pilot/issues/190) / [#191](https://github.com/joe-cheung-cae/frame-pilot/pull/191)，SHA `602c022b6842ca8c96f8cf6434a1bf750bfcb7b0`）。不要重开 [#190](https://github.com/joe-cheung-cae/frame-pilot/issues/190) 或 [#188](https://github.com/joe-cheung-cae/frame-pilot/issues/188)。不要动 [#41](https://github.com/joe-cheung-cae/frame-pilot/issues/41) / D3.06 托盘。不要发明第十阶段。

**分支：** `cursor/unsigned-desktop-sidecar-release-7a6c`，起点 `602c022b6842ca8c96f8cf6434a1bf750bfcb7b0`。不要为提交切到 `main`。不要合入 `main`。实现者不合入。

**相关：** `develop_plan.md` §1.1；[docs/desktop_install.md](../desktop_install.zh.md)；`.github/workflows/desktop.yml`（现有 NSIS/DMG 构建）；`.github/workflows/desktop-release.yml`（未签名发布）。

---

## 1. 为什么是残留，不是第十阶段

第九阶段 remaining-stretch 已关闭。#191 sidecar ready-line / 120 秒 / `sidecar.ready` 修已在 `main`。Joe 在 Win11 做冷 NSIS 首启仍需要**新的未签名安装包**——`v2.1.0-desktop` 不含该修。

`602c022` 上的 `desktop.yml` Windows **Build Tauri installer** 失败（`Path` 没有 `to_os_string`；`verify.yml` 无 Rust，未编译 `#[cfg(windows)]` 块）。本残留先修该编译错误以便打出 NSIS，再发布 `v2.1.1-desktop`。

**不要**发明第十阶段 / S10 / 2.3。产品版本字符串保持 `2.1.0-desktop`。不要改 `APP_VERSION`。

---

## 2. 锁定决定

1. **本地优先。** 无云上传、登录、支付、遥测或捆绑神经网络模型。
2. **复用 `desktop.yml` 安装包。** 不签名、不公证、不 staple、不用 `tauri-action`。不从 `verify.yml` 或发布工作流启动包装 GUI。
3. **仅未签名。** 不做 Authenticode、Developer ID、公证、staple、SmartScreen 豁免或商店上架。不声称 Gatekeeper 干净或 SmartScreen 干净。
4. **Release notes** 必须写明 **unsigned / 未签名**，写明含 #191 sidecar ready-line / 120 秒修，并链到 [docs/desktop_install.md](../desktop_install.md) 与 [docs/desktop_install.zh.md](../desktop_install.zh.md)。
5. **Tag** 为 `v2.1.1-desktop`。标题含 `(unsigned)`。只挂 NSIS `.exe` 与 macOS `.dmg`。不要挂残留 GUI 证据 zip。安装包文件名仍为 `FramePilot_2.1.0-desktop_*`（不改 `APP_VERSION`）。
6. **拒绝 #191 之前的产物。** 只从 `headSha` 为 `602c022b6842ca8c96f8cf6434a1bf750bfcb7b0` 或其后代、且同时有两份安装包 artifact 的 `desktop.yml` 运行发布。上传之后残留 GUI 红灯允许。
7. **不改 `APP_VERSION`。** 不用 `tauri-action`。不用 `TAURI_SIGNING_PRIVATE_KEY`。不做 `latest.json` 自动下载安装。
8. **一个 draft PR。** 正文必须含 `Closes #192`。实现者不合入。
9. **不做：** #41 / D3.06 托盘改动、第十阶段、签名、SHA256SUMS 公开发布清单、声称已签名商店发行。

---

## 3. 状态板

残留：含 sidecar 冷首启修的未签名桌面 Release

- [x] 需求拆解 — 中英残留计划 + GitHub issue [#192](https://github.com/joe-cheung-cae/frame-pilot/issues/192)
- [x] 开发 — Windows PATH helper 编译修复；`desktop-release.yml` 从含 #191 的安装包运行发布 `v2.1.1-desktop`；教程优先该 Release
- [x] 测试 — release notes + 工作流脚本检查；sidecar PATH 单测；`npm run test:scripts`
- [ ] 上线 — 合入后得到带 NSIS + DMG 的 GitHub Release `v2.1.1-desktop`（实现者不合入）
- [ ] DoD-ticked — Release URL 存在后再勾残留计划上线；**不要**重勾 §2.2 / 发明第十阶段 / 编造 Win11 GUI pass

---

## 4. 勾选规则

| 何时 | 勾 | 不要勾 |
| ---- | ---- | ----------- |
| 需求拆解 | 残留板 需求拆解 | 上线；§2.2 |
| 开发 + 脚本 / cargo 测试 | 残留板 开发 + 测试 | 上线；Gatekeeper 干净；商店上架；Win11 GUI pass |
| `v2.1.1-desktop` Release 已有 NSIS + DMG | 残留板 上线 + DoD-ticked；§1.1 本残留已交付 | 重勾 §2.2；公开签名清单；第十阶段 |

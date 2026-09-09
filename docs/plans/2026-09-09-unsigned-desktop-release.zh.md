# 残留：未签名桌面 GitHub Release（2026-09-09）

> 语言：[English](2026-09-09-unsigned-desktop-release.md) | **中文**

**GitHub：** [joe-cheung-cae/frame-pilot#188](https://github.com/joe-cheung-cae/frame-pilot/issues/188)。在未签名安装教程合入之后开立（[#186](https://github.com/joe-cheung-cae/frame-pilot/issues/186) / [#187](https://github.com/joe-cheung-cae/frame-pilot/pull/187)，SHA `f0ad7fc00fb7d722d97c2d154116269d9abb6f68`）。不要重开 [#186](https://github.com/joe-cheung-cae/frame-pilot/issues/186)。不要动 [#41](https://github.com/joe-cheung-cae/frame-pilot/issues/41) / D3.06 托盘。不要发明第十阶段。

**分支：** `cursor/unsigned-desktop-release-679f`，起点 `f0ad7fc00fb7d722d97c2d154116269d9abb6f68`。不要为提交切到 `main`。不要合入 `main`。实现者不合入。

**相关：** `develop_plan.md` §1.1；[docs/desktop_install.md](../desktop_install.zh.md)；`.github/workflows/desktop.yml`（现有 NSIS/DMG 构建）；`.github/workflows/desktop-release.yml`（未签名发布）。

---

## 1. 为什么是残留，不是第十阶段

第九阶段 remaining-stretch 已关闭。安装教程（[#186](https://github.com/joe-cheung-cae/frame-pilot/issues/186)）已在 `main`。Joe standing order：签名 / 公证 / SmartScreen·商店继续延后。本残留只发一版**未签名** GitHub Release，让 QA 能从持久的 Release 页下载 Windows NSIS + macOS DMG。

**不要**发明第十阶段 / S10 / 2.3。产品版本保持 `2.1.0-desktop`。不要改 `APP_VERSION`。

---

## 2. 锁定决定

1. **本地优先。** 无云上传、登录、支付、遥测或捆绑神经网络模型。
2. **复用现有 `desktop.yml` 安装包。** 本残留不重打 NSIS/DMG。不改打包脚本。不从 `verify.yml` 或发布工作流启动包装 GUI。
3. **仅未签名。** 不做 Authenticode、Developer ID、公证、staple、SmartScreen 豁免或商店上架。不声称 Gatekeeper 干净或 SmartScreen 干净。
4. **Release notes** 必须写明 **unsigned / 未签名**，并链到 [docs/desktop_install.md](../desktop_install.md) 与 [docs/desktop_install.zh.md](../desktop_install.zh.md)。
5. **Tag** 为 `v2.1.0-desktop`。标题含 `(unsigned)`。只挂 NSIS `.exe` 与 macOS `.dmg`。不要挂残留 GUI 证据 zip。
6. **不改 `APP_VERSION`。** 不用 `tauri-action`。不用 `TAURI_SIGNING_PRIVATE_KEY`。不做 `latest.json` 自动下载安装。
7. **一个 draft PR。** 正文必须含 `Closes #188`。实现者不合入。
8. **不做：** #41 / D3.06 托盘改动、第十阶段、签名、SHA256SUMS 公开发布清单、声称已签名商店发行。

---

## 3. 状态板

残留未签名桌面 GitHub Release

- [x] 需求拆解 — 中英残留计划 + GitHub issue [#188](https://github.com/joe-cheung-cae/frame-pilot/issues/188)
- [x] 开发 — `desktop-release.yml` 发布最近一次成功的 `desktop.yml` NSIS + DMG；教程优先该 Release
- [x] 测试 — release notes + 工作流脚本检查；`npm run test:scripts`
- [ ] 上线 — 合入后跑 `desktop-release.yml`，得到带 NSIS + DMG 的 GitHub Release `v2.1.0-desktop`（实现者不合入）
- [ ] DoD-ticked — Release URL 存在后再勾残留计划上线；**不要**重勾 §2.2 / 发明第十阶段

---

## 4. 勾选规则

| 何时 | 勾 | 不要勾 |
| ---- | ---- | ----------- |
| 需求拆解 | 残留板 需求拆解 | 上线；§2.2 |
| 开发 + 脚本测试 | 残留板 开发 + 测试 | 上线；Gatekeeper 干净；商店上架 |
| `v2.1.0-desktop` Release 已有 NSIS + DMG | 残留板 上线 + DoD-ticked；§1.1 本残留已交付 | 重勾 §2.2；公开签名清单；第十阶段 |

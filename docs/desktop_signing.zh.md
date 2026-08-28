# 桌面代码签名手册

> 语言：[English](desktop_signing.md) | **中文**

本手册说明 FramePilot 桌面安装包如何进行签名（Windows Authenticode）与公证（macOS Developer ID），密钥应存放在何处，以及在配置证书之前，内部测试者应如何对待**未签名**构建。

本文档仅为说明。不会把签名密钥写入仓库，也不要求第一个发布候选必须具备证书。

## 当前状态

- Tauri 产品名：`FramePilot`
- Bundle 标识符：`com.framepilot.app`（见 `apps/desktop/src-tauri/tauri.conf.json`）
- 安装包目标：Windows NSIS（`.exe`）与 macOS DMG（`.dmg`）
- CI 工作流：`.github/workflows/desktop.yml` 在 `windows-latest` 与 `macos-latest` 上构建并**上传未签名**安装包产物
- 本仓库不存放代码签名证书或 Apple 公证凭据
- 缺少证书**不得**导致第一个桌面 RC 失败；未签名安装包仍可用于内部测试

## 密钥与证书存放

切勿将私钥、`.p12` / `.pfx` 文件、Apple API 密钥、公证密码或 base64 编码的证书内容提交到 Git。

日后启用签名时，凭据只应存放在 GitHub Actions secrets（或等价的 CI 密钥库）中，例如：

| 平台 | 典型密钥材料（仅作示例） |
| ---- | ------------------------ |
| Windows | Authenticode 证书（PFX）+ 密码，或云签名服务令牌 |
| macOS | Developer ID Application 证书、Apple ID / App Store Connect API 密钥、团队 ID、公证凭据 |

本地开发机可将一次性签名构建放在系统钥匙串中。正式发布签名应在 CI 中完成，使密钥远离个人电脑，也不进入代码树。

不要把密钥值粘贴到 issue、PR、可行性说明或本手册中。

## Windows Authenticode（概览）

Authenticode 对 Windows 安装包（以及可选的应用内二进制）签名，以便 SmartScreen 与企业策略能够信任发布者。

在具备证书时的高层流程：

1. 从受信任 CA（或组织托管的签名服务）获取代码签名证书。
2. 将证书导入 CI 密钥库（不要放进仓库）。
3. 在 `tauri build` / 构建后步骤中，用 `signtool` 或 Tauri Windows 签名钩子签署 NSIS `.exe`。
4. 可选：为签名加时间戳，使证书过期后签名仍可验证。
5. 发布前在本地验证签名（`signtool verify` 或属性 → 数字签名）。

在这些密钥就绪之前，CI 继续上传**未签名** NSIS 安装包。Windows 可能显示 SmartScreen /「未知发布者」警告；对内部构建而言这是预期行为。

## macOS Developer ID 与公证（概览）

在 Mac App Store 之外分发，需使用 **Developer ID Application** 签名，并完成 **Apple 公证**，Gatekeeper 才会接受该应用。

在具备凭据时的高层流程：

1. 加入 Apple Developer Program，创建与 bundle id `com.framepilot.app` 配套的 Developer ID Application 证书。
2. 将签名身份与公证凭据存入 CI secrets（不要放进仓库）。
3. 在 `tauri build` 期间签署 `.app`，打包 DMG，再将 DMG（或 zip）提交到 Apple 公证服务。
4. 将公证票据装订（staple）到 DMG / 应用，以便离线 Gatekeeper 检查通过。
5. 发布前用 `spctl --assess` / `xcrun stapler validate` 验证。

在这些凭据就绪之前，CI 继续上传**未签名** DMG。macOS 可能因 Gatekeeper 阻止打开（「无法验证开发者」）；对内部构建而言这是预期行为。

## 内部测试者：未签名安装包

来自 `desktop` 工作流的未签名 Windows / macOS 产物仅供**内部测试者与开发者**使用，不面向公开下载页。

测试者应当：

- 仅从项目的 GitHub Actions 运行或其他维护者可控渠道下载产物
- 预期未签名包会出现 OS 信任警告（SmartScreen / Gatekeeper）
- 尽可能使用一次性或专用测试机/账户
- 不要把未签名安装包当作「正式」版本对外分发
- 将安装/启动失败与 OS 信任对话框分开报告

在 Windows 上，仅在信任构建来源时绕过 SmartScreen（例如对已知的 Actions 产物选择「更多信息」→「仍要运行」）。

在 macOS 上，仅对已知可靠的内部 DMG 清除 Gatekeeper 隔离（例如移除下载应用上的 quarantine 属性，或通过 Control-单击 → 打开）。一旦有签名并公证的构建，应优先使用它们。

## 第一个 RC 策略

当证书尚不可用时，第一个桌面发布候选可以用**未签名**安装包进行发布或验证。不要仅因缺少 Authenticode 或 Apple 公证凭据而阻塞 RC 打标签或 Phase 4 验收。在 CI 中配置密钥后，再跟进签名。

## 相关文件

- `.github/workflows/desktop.yml` — 未签名 Windows/macOS 安装包 CI
- `apps/desktop/src-tauri/tauri.conf.json` — `identifier`、NSIS 与 DMG 打包配置
- `docs/plans/2026-08-18-desktop-packaging.zh.md` — D4.05 任务定义

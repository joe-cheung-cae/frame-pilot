# FramePilot 2.1.0-desktop (unsigned)

> Language: **English** | [中文](desktop_unsigned_release_notes.zh.md)

This GitHub Release publishes **unsigned** Windows NSIS and macOS DMG installers from the existing `desktop` workflow.

These packages are **unsigned**. They are **not** Authenticode-signed, **not** Apple-notarized, **not** Gatekeeper-clean, **not** SmartScreen-clean, and **not** a store listing. Windows may show **Unknown publisher** / SmartScreen. macOS may show **cannot be opened because the developer cannot be verified**. Those dialogs are expected.

**Install walkthrough:** [Unsigned desktop install tutorial](desktop_install.md) · [中文](desktop_install.zh.md)

On GitHub.com use:

- https://github.com/joe-cheung-cae/frame-pilot/blob/main/docs/desktop_install.md
- https://github.com/joe-cheung-cae/frame-pilot/blob/main/docs/desktop_install.zh.md

## Assets

Download only the installer files from this Release:

- Windows: `FramePilot_2.1.0-desktop_x64-setup.exe` (NSIS, x64)
- macOS: `FramePilot_2.1.0-desktop_aarch64.dmg` (Apple Silicon / `aarch64`)

Do **not** install leftover GUI-evidence zips (`FramePilot-desktop-500-gui-*`, `FramePilot-desktop-quit-job-*`). Those are test logs, not installers.

**Help → Check for updates** does not download or install. Install a newer unsigned build from this Release (or a later unsigned Release) using the tutorial.

This is not a signed public store release. Do not treat it as Gatekeeper-clean.

## 中文摘要

本 Release 提供**未签名**的 Windows NSIS 与 macOS DMG。不是 Authenticode、不是 Apple 公证、不是 Gatekeeper 干净、不是 SmartScreen 干净、不是商店上架。安装教程见 [docs/desktop_install.zh.md](desktop_install.zh.md)。

# FramePilot 2.1.1-desktop (unsigned)

> Language: **English** | [中文](desktop_unsigned_release_notes.zh.md)

This GitHub Release publishes **unsigned** Windows NSIS and macOS DMG installers from the existing `desktop` workflow.

These packages are **unsigned**. They are **not** Authenticode-signed, **not** Apple-notarized, **not** Gatekeeper-clean, **not** SmartScreen-clean, and **not** a store listing. Windows may show **Unknown publisher** / SmartScreen. macOS may show **cannot be opened because the developer cannot be verified**. Those dialogs are expected.

This cut includes the [#191](https://github.com/joe-cheung-cae/frame-pilot/pull/191) Windows sidecar ready-line fix (120s Windows startup budget, `{data_dir}/logs/sidecar.ready` fallback, spawn cwd / `CREATE_NO_WINDOW` / unbuffered stdio). Do **not** use `v2.1.0-desktop` for a Win11 cold first Start.

**Install walkthrough:** [Unsigned desktop install tutorial](desktop_install.md) · [中文](desktop_install.zh.md)

On GitHub.com use:

- https://github.com/joe-cheung-cae/frame-pilot/blob/main/docs/desktop_install.md
- https://github.com/joe-cheung-cae/frame-pilot/blob/main/docs/desktop_install.zh.md

## Assets

Download only the installer files from this Release:

- Windows: `FramePilot_2.1.0-desktop_x64-setup.exe` (NSIS, x64)
- macOS: `FramePilot_2.1.0-desktop_aarch64.dmg` (Apple Silicon / `aarch64`)

Filenames still say `2.1.0-desktop` because `APP_VERSION` was not bumped. The Release tag is `v2.1.1-desktop`.

Do **not** install leftover GUI-evidence zips (`FramePilot-desktop-500-gui-*`, `FramePilot-desktop-quit-job-*`). Those are test logs, not installers.

**Help → Check for updates** does not download or install. Install a newer unsigned build from this Release (or a later unsigned Release) using the tutorial.

This is not a signed public store release. Do not treat it as Gatekeeper-clean.

## Windows 11 cold first-start

1. Install the NSIS `.exe` from **this** Release (`v2.1.1-desktop`), not `v2.1.0-desktop`.
2. Do **not** pre-run `%LOCALAPPDATA%\FramePilot\framepilot-api\framepilot-api.exe`.
3. Start **FramePilot** from the Start menu. Wait up to two minutes.
4. Pass: window title `FramePilot`, project UI, no `timed out waiting for sidecar ready line`.

## 中文摘要

本 Release 提供**未签名**的 Windows NSIS 与 macOS DMG，并含 [#191](https://github.com/joe-cheung-cae/frame-pilot/pull/191) sidecar ready-line / 120 秒修。不是 Authenticode、不是 Apple 公证、不是 Gatekeeper 干净、不是 SmartScreen 干净、不是商店上架。安装教程见 [docs/desktop_install.zh.md](desktop_install.zh.md)。Win11 冷首启请用 `v2.1.1-desktop`，不要用 `v2.1.0-desktop`。

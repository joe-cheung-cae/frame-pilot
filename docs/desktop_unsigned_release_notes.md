# FramePilot 2.1.3-desktop (unsigned)

> Language: **English** | [中文](desktop_unsigned_release_notes.zh.md)

This GitHub Release publishes **unsigned** Windows NSIS and macOS DMG installers from the existing `desktop` workflow.

These packages are **unsigned**. They are **not** Authenticode-signed, **not** Apple-notarized, **not** Gatekeeper-clean, **not** SmartScreen-clean, and **not** a store listing. Windows may show **Unknown publisher** / SmartScreen. macOS may show **cannot be opened because the developer cannot be verified**. Those dialogs are expected.

This cut includes the [#199](https://github.com/joe-cheung-cae/frame-pilot/pull/199) / [#198](https://github.com/joe-cheung-cae/frame-pilot/issues/198) Win11 NSIS locked-file upgrade hooks (`installerHooks` / `hooks.nsh`): PREINSTALL/PREUNINSTALL **stop** when FramePilot or `framepilot-api` still lock sidecar `_internal` DLLs. The dialog is **Retry / Cancel** only — **no Ignore-through** half install. It also includes the earlier [#195](https://github.com/joe-cheung-cae/frame-pilot/pull/195) / [#194](https://github.com/joe-cheung-cae/frame-pilot/issues/194) Win11 new-project Import/Export fix and the [#191](https://github.com/joe-cheung-cae/frame-pilot/pull/191) Windows sidecar ready-line fix (120s Windows startup budget, `{data_dir}/logs/sidecar.ready` fallback, spawn cwd / `CREATE_NO_WINDOW` / unbuffered stdio).

Quit FramePilot and `framepilot-api` before upgrading. Do **not** use `v2.1.2-desktop` to verify upgrade-while-running (that NSIS lacks the hooks). Do **not** use `v2.1.1-desktop` to verify new-project Import/Export. Do **not** use `v2.1.0-desktop` for a Win11 cold first Start.

**Install walkthrough:** [Unsigned desktop install tutorial](desktop_install.md) · [中文](desktop_install.zh.md)

On GitHub.com use:

- https://github.com/joe-cheung-cae/frame-pilot/blob/main/docs/desktop_install.md
- https://github.com/joe-cheung-cae/frame-pilot/blob/main/docs/desktop_install.zh.md

## Assets

Download only the installer files from this Release:

- Windows: `FramePilot_2.1.0-desktop_x64-setup.exe` (NSIS, x64)
- macOS: `FramePilot_2.1.0-desktop_aarch64.dmg` (Apple Silicon / `aarch64`)

Filenames still say `2.1.0-desktop` because `APP_VERSION` was not bumped. The Release tag is `v2.1.3-desktop`.

Do **not** install leftover GUI-evidence zips (`FramePilot-desktop-500-gui-*`, `FramePilot-desktop-quit-job-*`). Those are test logs, not installers.

**Help → Check for updates** does not download or install. Install a newer unsigned build from this Release (or a later unsigned Release) using the tutorial.

This is not a signed public store release. Do not treat it as Gatekeeper-clean.

## Upgrade while FramePilot is open

Quit FramePilot (**File → Quit**) before running this NSIS over an existing install. The sidecar locks files under `framepilot-api\_internal`. If FramePilot is still open, **this** NSIS (`v2.1.3-desktop`) stops with **Retry / Cancel** only — there is **no Ignore**. **Cancel** leaves the previous tree intact. After **File → Quit**, click **Retry** (or re-run the installer).

`v2.1.2-desktop` and older still offer **Ignore**. Click **Abort**, not Ignore. Written steps: [docs/desktop_install.md](desktop_install.md#upgrade-close-the-app-first).

## Windows 11 upgrade-while-running check

1. Install a previous unsigned NSIS (`v2.1.2-desktop` is a valid baseline).
2. Start **FramePilot**. Wait until the project UI is up. Do **not** quit.
3. Run the NSIS `.exe` from **this** Release (`v2.1.3-desktop`), not `v2.1.2-desktop`.
4. Pass: the installer stops with Retry / Cancel (close FramePilot / `framepilot-api`). Cancel leaves the previous tree intact. There is no Ignore-through loop.
5. **File → Quit**, then Retry (or re-run the installer). Finish the wizard.
6. Pass: `%LOCALAPPDATA%\FramePilot\framepilot-api\_internal\MSVCP140.dll` exists. Cold start → create a project → Import / Export open.

## Windows 11 Import/Export check

1. Install the NSIS `.exe` from **this** Release (`v2.1.3-desktop`), not `v2.1.1-desktop` or `v2.1.0-desktop`.
2. Start **FramePilot**. On a first launch after NSIS, wait up to two minutes.
3. Create a project → **Create and Import**.
4. Click **Import** / **Export** workflow tabs (or File → Import / File → Export).
5. Pass: Import Images and Export Selection open.

## Windows 11 cold first-start

1. Install the NSIS `.exe` from **this** Release (`v2.1.3-desktop`), not `v2.1.0-desktop`.
2. Do **not** pre-run `%LOCALAPPDATA%\FramePilot\framepilot-api\framepilot-api.exe`.
3. Start **FramePilot** from the Start menu. Wait up to two minutes.
4. Pass: window title `FramePilot`, project UI, no `timed out waiting for sidecar ready line`.

## 中文摘要

本 Release 提供**未签名**的 Windows NSIS 与 macOS DMG，并含 [#199](https://github.com/joe-cheung-cae/frame-pilot/pull/199) / [#198](https://github.com/joe-cheung-cae/frame-pilot/issues/198) 锁文件升级 hooks（Retry/Cancel，无 Ignore-through），以及此前 [#195](https://github.com/joe-cheung-cae/frame-pilot/pull/195) / [#194](https://github.com/joe-cheung-cae/frame-pilot/issues/194) 导入/导出修与 [#191](https://github.com/joe-cheung-cae/frame-pilot/pull/191) sidecar ready-line / 120 秒修。不是 Authenticode、不是 Apple 公证、不是 Gatekeeper 干净、不是 SmartScreen 干净、不是商店上架。安装教程见 [docs/desktop_install.zh.md](desktop_install.zh.md)。验应用仍在运行时升级不要用 `v2.1.2-desktop`。验新建工程导入/导出不要用 `v2.1.1-desktop`。Win11 冷首启不要用 `v2.1.0-desktop`。

# Unsigned desktop install tutorial

> Language: **English** | [中文](desktop_install.zh.md)

How to download, install, start, and quit FramePilot from the current **unsigned** Windows NSIS and macOS DMG packages.

**Also see:** [Desktop User Guide](desktop_user_guide.md) · [Desktop Testing Matrix](desktop_testing.md) · [Desktop Development Plan](desktop_development_plan.md) · [Signing runbook](desktop_signing.md) · [Known limitations](v2_known_limitations.md) · [Desktop shell README](../apps/desktop/README.md)

---

## Current builds are unsigned

These installers are **unsigned**. They are **not** a notarized Mac build, **not** Authenticode-signed, **not** Gatekeeper-clean, **not** SmartScreen-clean, and **not** a store listing.

Windows may show **Windows protected your PC** / **Unknown publisher**. macOS may show **cannot be opened because the developer cannot be verified** / Apple cannot check the app for malicious software. Those dialogs are expected on this track. Do not treat this Release as a signed public store build.

Signing-ready CI exists when secrets are provisioned; missing secrets keep the unsigned upload green. See [Desktop Code Signing Runbook](desktop_signing.md). Do not ask this tutorial to sign or notarize.

---

## Where to download

Prefer the unsigned GitHub Release that includes the [#195](https://github.com/joe-cheung-cae/frame-pilot/pull/195) Import/Export fix and the [#191](https://github.com/joe-cheung-cae/frame-pilot/pull/191) sidecar ready-line / 120s fix. Release notes: [docs/desktop_unsigned_release_notes.md](desktop_unsigned_release_notes.md). Do **not** use `v2.1.0-desktop` for a Win11 cold first Start. Do **not** use `v2.1.1-desktop` to verify new-project Import/Export.

1. Open [Releases](https://github.com/joe-cheung-cae/frame-pilot/releases) and open **FramePilot 2.1.2-desktop (unsigned)** (`v2.1.2-desktop`).
2. Download only the installer assets:
   - Windows: `FramePilot_2.1.0-desktop_x64-setup.exe` (NSIS, x64)
   - macOS: `FramePilot_2.1.0-desktop_aarch64.dmg` (Apple Silicon / `aarch64`)
3. Do **not** install leftover GUI-evidence zips (`FramePilot-desktop-500-gui-*`, `FramePilot-desktop-quit-job-*`). Those are test logs, not installers.
4. Do **not** download from third-party mirrors. Confirm the URL is `github.com/joe-cheung-cae/frame-pilot`.

If that Release is not published yet, or you need a newer unsigned build before the next Release, use the **desktop** GitHub Actions workflow:

1. Open [Actions → desktop](https://github.com/joe-cheung-cae/frame-pilot/actions/workflows/desktop.yml).
2. Open a **successful** run on `main` (green check). A maintainer can start a fresh build with **Run workflow** (`workflow_dispatch`) if the latest artifacts expired or you need a newer commit.
3. Sign in to GitHub if the run asks you to. Artifact download usually requires a GitHub account that can see the run.
4. In the run’s **Artifacts** list, download only `FramePilot-windows-nsis` or `FramePilot-macos-dmg`, then unzip it. Inside you should see a single NSIS `.exe` or a single `.dmg`. The file name includes `FramePilot` and the `2.1.0-desktop` version string.

GitHub Actions artifacts expire. GitHub Release assets do not expire with the Actions retention window. If the Artifacts section is empty, the run is still in progress, failed, or the zip aged out — use the unsigned Release, another green `main` run, or ask a maintainer to dispatch `desktop.yml` and then `desktop-release.yml`.

**Help → Check for updates** does not download or install. Install a newer unsigned build the same way as this page.

---

## Windows (unsigned NSIS)

### Install

1. Keep the NSIS `.exe` from the unsigned Release (typical name `FramePilot_2.1.0-desktop_x64-setup.exe`). If you used the Actions fallback, unzip `FramePilot-windows-nsis` first.
2. Double-click the installer. NSIS is configured for **current user** (`installMode: currentUser`), so a normal install does not need an Administrator UAC prompt.
3. Complete the NSIS wizard. The app lands under the per-user install directory (typically `%LOCALAPPDATA%\FramePilot`). The wizard adds a Start menu shortcut named **FramePilot**.

### Upgrade (close the app first)

Quit FramePilot **before** running a newer NSIS over an existing install. The Python sidecar (`framepilot-api.exe`) keeps DLLs under `%LOCALAPPDATA%\FramePilot\framepilot-api\_internal` open. If those files stay locked, a stock NSIS **Ignore** continues past them and leaves a half-written tree — Import/Export can then stay blank (Joe’s `v2.1.2-desktop` Win11 repro). That is a broken install, not a [#195](https://github.com/joe-cheung-cae/frame-pilot/pull/195) regression.

1. Quit FramePilot: **File → Quit**, **Ctrl+Q**, or the window **X**. Wait until the window is gone.
2. Optional: Task Manager should show no `framepilot-desktop.exe` and no `framepilot-api.exe`.
3. Then run the new setup `.exe`.

Installers that include leftover [#198](https://github.com/joe-cheung-cae/frame-pilot/issues/198) **stop** if those processes (or locked `_internal` files such as `MSVCP140.dll`) are still in use. The dialog is **Retry / Cancel** only — not Ignore. **Retry** after you quit (the installer may also force-close leftovers). **Cancel** aborts so the previous `_internal` tree is not half-overwritten.

`v2.1.2-desktop` and older NSIS builds can still show **Error opening file for writing** with Abort / Retry / **Ignore**. Click **Abort — not Ignore**. Then quit FramePilot and run the installer again.

If you already Ignore-through a broken install: quit FramePilot and `framepilot-api`, then re-run a #198+ NSIS (or uninstall and reinstall). Do not treat blank Import/Export as a #195 regression until `_internal` is complete.

### Win11 acceptance: upgrade while the app is still running

Use this after a #198+ NSIS exists (a `desktop.yml` artifact from this leftover, or a later unsigned Release — not the published `v2.1.2-desktop` setup). Do not invent a pass here.

1. Install a previous unsigned NSIS (`v2.1.2-desktop` is a valid baseline).
2. Start **FramePilot**. Wait until the project UI is up. Do **not** quit.
3. Run the **new** NSIS.
4. Pass: the installer stops with Retry / Cancel (close FramePilot / `framepilot-api`). Cancel leaves the previous tree intact. There is no Ignore-through loop.
5. **File → Quit**, then Retry (or re-run the installer). Finish the wizard.
6. Pass: `%LOCALAPPDATA%\FramePilot\framepilot-api\_internal\MSVCP140.dll` exists. Cold start → create a project → Import / Export open.

### SmartScreen / unknown publisher

Unsigned NSIS builds often trigger Microsoft Defender SmartScreen.

If Windows shows **Windows protected your PC** (unrecognized app / **Unknown publisher**):

1. Click **More info**.
2. Confirm the file name is the FramePilot setup `.exe` you just downloaded from this repo’s unsigned Release (or unzipped Actions artifact).
3. Click **Run anyway**.

Optional unblock before the first run (same trusted artifact only):

1. Right-click the `.exe` → **Properties**.
2. If Windows shows **This file came from another computer and might be blocked to help protect this computer**, check **Unblock** → **Apply** → **OK**.
3. Run the installer again.

Bypass SmartScreen only when you trust that Release or Actions run. This page does **not** claim SmartScreen will stay quiet, and it does not document a SmartScreen exemption.

### Start

1. Open **Start** and launch **FramePilot** (or the shortcut the installer created).
2. The window title is `FramePilot`. You do not start uvicorn or open a browser.
3. The Python sidecar binds loopback only (`127.0.0.1`). Other devices on the LAN cannot open the API.
4. Default data directory: `%APPDATA%\FramePilot`. Uninstall does not always delete it.
5. **First launch after install** can take up to about two minutes while Windows scans the local API under `%LOCALAPPDATA%\FramePilot`. Wait for the window. Do not force-quit and immediately retry — that used to kill a still-booting sidecar (#190).

### Sidecar failed to start (Windows)

If the window says **FramePilot could not start the local API** / `timed out waiting for sidecar ready line`:

1. Confirm you launched the installed **FramePilot** shortcut, not the NSIS setup `.exe` again.
2. Wait a full two minutes on a brand-new install before deciding it failed.
3. Open `%APPDATA%\FramePilot\logs\sidecar.log` and `%APPDATA%\FramePilot\logs\sidecar.ready`. An empty log usually means the process was still in the PyInstaller bootloader / Defender scan. A ready file plus a later `/health` means the API did start.
4. Quit, start **FramePilot** once more, and wait again. After the first scan, later launches should be much faster.
5. Do not treat this as a signing, SmartScreen-exemption, or tray issue.

### Stop

1. With no import, processing, or export running: **File → Quit**, **Ctrl+Q**, or close the main window (**X**). Closing the window **quits** FramePilot; it does not hide to the tray.
2. If a job is still running, choose **Keep working**, **Quit and cancel** (import / processing / export), or **Quit anyway**. Details: [Desktop User Guide](desktop_user_guide.md#quit-while-work-is-running).
3. Tray **Quit** (when a tray icon exists) uses the same running-job dialog as **File → Quit**.

### Uninstall

Use **Settings → Apps → Installed apps → FramePilot → Uninstall**, or the uninstaller next to the installed app. The application binary is removed. **`%APPDATA%\FramePilot` may remain** so projects are not silently deleted.

---

## macOS (unsigned DMG)

### Install

1. Keep the `.dmg` from the unsigned Release (typical name `FramePilot_2.1.0-desktop_aarch64.dmg` on current `macos-latest`). If you used the Actions fallback, unzip `FramePilot-macos-dmg` first.
2. Double-click the DMG to attach it.
3. Drag **FramePilot** to **Applications** (or copy `FramePilot.app` there).
4. Eject the DMG. Launch from `/Applications/FramePilot.app`, not from the disk image.

An Intel Mac cannot use an Apple Silicon–only DMG. If you need a different architecture, a maintainer must produce that build; this tutorial does not invent a universal binary.

### Gatekeeper / unidentified developer

Unsigned DMGs are quarantined after download. First open often fails with **“FramePilot” cannot be opened because the developer cannot be verified** or Apple cannot check it for malicious software.

Use one of these, only for a DMG you downloaded from this repo’s unsigned Release or Actions:

**Control-click → Open (preferred)**

1. In **Applications**, Control-click (or right-click) **FramePilot**.
2. Choose **Open**.
3. In the warning dialog, choose **Open** again.

**System Settings → Allow**

1. Open **System Settings → Privacy & Security**.
2. Scroll to the message that FramePilot was blocked because it is not from an identified developer.
3. Click **Open Anyway**. Confirm with password or Touch ID if asked.

**Optional quarantine clear (trusted internal DMG only)**

```bash
xattr -d com.apple.quarantine /Applications/FramePilot.app
```

Do **not** turn Gatekeeper off globally. This page does **not** claim a Gatekeeper-clean or notarized Mac pass.

### Start

1. Open **FramePilot** from Applications or Spotlight.
2. The window title is `FramePilot`. You do not start uvicorn or open a browser.
3. The Python sidecar binds loopback only (`127.0.0.1`).
4. Default data directory: `~/Library/Application Support/FramePilot`. Uninstall does not always delete it.

### Stop

1. With no import, processing, or export running: **FramePilot → Quit FramePilot**, **File → Quit**, **Cmd+Q**, or close the main window. Closing the window **quits** FramePilot; it does not hide to the tray.
2. If a job is still running, choose **Keep working**, **Quit and cancel** (import / processing / export), or **Quit anyway**. Details: [Desktop User Guide](desktop_user_guide.md#quit-while-work-is-running).
3. Tray **Quit** (when a tray icon exists) uses the same running-job dialog as **File → Quit**.

### Uninstall

Drag `/Applications/FramePilot.app` to the Trash and empty it if you want the app gone. **`~/Library/Application Support/FramePilot` may remain** so projects are not silently deleted.

---

## QA path: get the package → install → open → close

Use this as the written path for a manual unsigned install check. Record date, OS, Release URL (or Actions run URL), and `APP_VERSION` from `GET /health` when you can reach the sidecar. Do not invent a pass.

### Windows

1. Download the NSIS `.exe` from [FramePilot 2.1.2-desktop (unsigned)](https://github.com/joe-cheung-cae/frame-pilot/releases) (`v2.1.2-desktop`). Fall back to unzipping `FramePilot-windows-nsis` from a green [desktop](https://github.com/joe-cheung-cae/frame-pilot/actions/workflows/desktop.yml) run if the Release is missing. Do not use `v2.1.0-desktop` for this check. Do not use `v2.1.1-desktop` to verify new-project Import/Export.
2. If FramePilot is already installed, quit it first (**Upgrade (close the app first)**). Handle SmartScreen / unknown publisher as above, then finish the NSIS wizard. If the wizard says the app is still running, Retry after **File → Quit**, or Cancel — do not Ignore locked-file errors.
3. Start **FramePilot** from the Start menu. On a **first** launch after NSIS, wait up to two minutes. Confirm the window title is `FramePilot` and that you see the project list (not “timed out waiting for sidecar ready line”).
4. Optional: from another terminal, `GET http://127.0.0.1:<port>/health` only if you already know the allocated loopback port from the sidecar ready file (`%APPDATA%\FramePilot\logs\sidecar.ready`). Expect `version` + `service`. Do not assume port `8000`.
5. Quit with **File → Quit** or the window close button. Confirm the window is gone (close is quit, not hide-to-tray).

### macOS

1. Download the `.dmg` from [FramePilot 2.1.2-desktop (unsigned)](https://github.com/joe-cheung-cae/frame-pilot/releases) (`v2.1.2-desktop`). Fall back to unzipping `FramePilot-macos-dmg` from a green [desktop](https://github.com/joe-cheung-cae/frame-pilot/actions/workflows/desktop.yml) run if the Release is missing.
2. Attach the DMG, drag **FramePilot** to Applications, eject the image.
3. Handle Gatekeeper as above, then open `/Applications/FramePilot.app`. Confirm the window title is `FramePilot`.
4. Quit with **FramePilot → Quit FramePilot**, **Cmd+Q**, or the window close button. Confirm the window is gone (close is quit, not hide-to-tray).

After this path works, follow the [Desktop User Guide](desktop_user_guide.md) for first launch, projects, import (copies, not moves), and export. Manual matrix rows: [Desktop Testing Matrix](desktop_testing.md).

---

## Out of scope on this page

- Code signing, notarization, SmartScreen exemption, or store listing
- Changing packaging scripts or `APP_VERSION`
- Claiming Gatekeeper-clean, SmartScreen-clean, or a store listing
- Tray hide-to-background behavior (window close is still quit)
- Phase 10 / new desktop feature gates

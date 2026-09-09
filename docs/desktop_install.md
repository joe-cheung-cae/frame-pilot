# Unsigned desktop install tutorial

> Language: **English** | [中文](desktop_install.zh.md)

How to download, install, start, and quit FramePilot from the current **unsigned** Windows NSIS and macOS DMG packages.

**Also see:** [Desktop User Guide](desktop_user_guide.md) · [Desktop Testing Matrix](desktop_testing.md) · [Desktop Development Plan](desktop_development_plan.md) · [Signing runbook](desktop_signing.md) · [Known limitations](v2_known_limitations.md) · [Desktop shell README](../apps/desktop/README.md)

---

## Current builds are unsigned

These installers are **unsigned**. They are **not** a notarized Mac build, **not** Authenticode-signed, **not** Gatekeeper-clean, **not** SmartScreen-clean, and **not** a store listing.

Windows may show **Windows protected your PC** / **Unknown publisher**. macOS may show **cannot be opened because the developer cannot be verified** / Apple cannot check the app for malicious software. Those dialogs are expected on this track. Do not treat an Actions artifact as a public release.

Signing-ready CI exists when secrets are provisioned; missing secrets keep the unsigned upload green. See [Desktop Code Signing Runbook](desktop_signing.md). Do not ask this tutorial to sign, notarize, or ship a release.

---

## Where to download

Until a tagged GitHub Release publishes installer assets, download from this repository’s **desktop** GitHub Actions workflow only:

1. Open [Actions → desktop](https://github.com/joe-cheung-cae/frame-pilot/actions/workflows/desktop.yml).
2. Open a **successful** run on `main` (green check). A maintainer can start a fresh build with **Run workflow** (`workflow_dispatch`) if the latest artifacts expired or you need a newer commit.
3. Sign in to GitHub if the run asks you to. Artifact download usually requires a GitHub account that can see the run.
4. In the run’s **Artifacts** list, download only:
   - Windows: `FramePilot-windows-nsis`
   - macOS: `FramePilot-macos-dmg`
5. Unzip the downloaded artifact zip on the machine that will install FramePilot. Inside you should see a single NSIS `.exe` or a single `.dmg`. The file name includes `FramePilot` and the `2.1.0-desktop` version string. The Windows runner produces an x64 NSIS installer. The `macos-latest` DMG matches that runner’s CPU (currently Apple Silicon / `aarch64`).
6. Do **not** install leftover GUI-evidence zips (`FramePilot-desktop-500-gui-*`, `FramePilot-desktop-quit-job-*`). Those are test logs, not installers.
7. Do **not** download from third-party mirrors. Confirm the URL is `github.com/joe-cheung-cae/frame-pilot`.

GitHub Actions artifacts expire. If the Artifacts section is empty, the run is still in progress, failed, or the zip aged out — use another green `main` run or ask a maintainer to dispatch `desktop.yml`.

**Help → Check for updates** does not download or install. Install a newer unsigned build the same way as this page.

---

## Windows (unsigned NSIS)

### Install

1. Unzip `FramePilot-windows-nsis` and keep the `.exe` (typical name `FramePilot_2.1.0-desktop_x64-setup.exe`).
2. Double-click the installer. NSIS is configured for **current user** (`installMode: currentUser`), so a normal install does not need an Administrator UAC prompt.
3. Complete the NSIS wizard. The app lands under the per-user install directory (typically `%LOCALAPPDATA%\FramePilot`). The wizard adds a Start menu shortcut named **FramePilot**.

### SmartScreen / unknown publisher

Unsigned NSIS builds often trigger Microsoft Defender SmartScreen.

If Windows shows **Windows protected your PC** (unrecognized app / **Unknown publisher**):

1. Click **More info**.
2. Confirm the file name is the FramePilot setup `.exe` you just unzipped from this repo’s Actions artifact.
3. Click **Run anyway**.

Optional unblock before the first run (same trusted artifact only):

1. Right-click the `.exe` → **Properties**.
2. If Windows shows **This file came from another computer and might be blocked to help protect this computer**, check **Unblock** → **Apply** → **OK**.
3. Run the installer again.

Bypass SmartScreen only when you trust that Actions run. This page does **not** claim SmartScreen will stay quiet, and it does not document a SmartScreen exemption.

### Start

1. Open **Start** and launch **FramePilot** (or the shortcut the installer created).
2. The window title is `FramePilot`. You do not start uvicorn or open a browser.
3. The Python sidecar binds loopback only (`127.0.0.1`). Other devices on the LAN cannot open the API.
4. Default data directory: `%APPDATA%\FramePilot`. Uninstall does not always delete it.

### Stop

1. With no import, processing, or export running: **File → Quit**, **Ctrl+Q**, or close the main window (**X**). Closing the window **quits** FramePilot; it does not hide to the tray.
2. If a job is still running, choose **Keep working**, **Quit and cancel** (import / processing / export), or **Quit anyway**. Details: [Desktop User Guide](desktop_user_guide.md#quit-while-work-is-running).
3. Tray **Quit** (when a tray icon exists) uses the same running-job dialog as **File → Quit**.

### Uninstall

Use **Settings → Apps → Installed apps → FramePilot → Uninstall**, or the uninstaller next to the installed app. The application binary is removed. **`%APPDATA%\FramePilot` may remain** so projects are not silently deleted.

---

## macOS (unsigned DMG)

### Install

1. Unzip `FramePilot-macos-dmg` and keep the `.dmg` (typical name `FramePilot_2.1.0-desktop_aarch64.dmg` on current `macos-latest`).
2. Double-click the DMG to attach it.
3. Drag **FramePilot** to **Applications** (or copy `FramePilot.app` there).
4. Eject the DMG. Launch from `/Applications/FramePilot.app`, not from the disk image.

An Intel Mac cannot use an Apple Silicon–only DMG. If you need a different architecture, a maintainer must produce that build; this tutorial does not invent a universal binary.

### Gatekeeper / unidentified developer

Unsigned DMGs are quarantined after download. First open often fails with **“FramePilot” cannot be opened because the developer cannot be verified** or Apple cannot check it for malicious software.

Use one of these, only for a DMG you downloaded from this repo’s Actions:

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

Use this as the written path for a manual unsigned install check. Record date, OS, Actions run URL, and `APP_VERSION` from `GET /health` when you can reach the sidecar. Do not invent a pass.

### Windows

1. Download `FramePilot-windows-nsis` from a green [desktop](https://github.com/joe-cheung-cae/frame-pilot/actions/workflows/desktop.yml) run and unzip the NSIS `.exe`.
2. Handle SmartScreen / unknown publisher as above, then finish the NSIS wizard.
3. Start **FramePilot** from the Start menu. Confirm the window title is `FramePilot`.
4. Quit with **File → Quit** or the window close button. Confirm the window is gone (close is quit, not hide-to-tray).

### macOS

1. Download `FramePilot-macos-dmg` from a green [desktop](https://github.com/joe-cheung-cae/frame-pilot/actions/workflows/desktop.yml) run and unzip the `.dmg`.
2. Attach the DMG, drag **FramePilot** to Applications, eject the image.
3. Handle Gatekeeper as above, then open `/Applications/FramePilot.app`. Confirm the window title is `FramePilot`.
4. Quit with **FramePilot → Quit FramePilot**, **Cmd+Q**, or the window close button. Confirm the window is gone (close is quit, not hide-to-tray).

After this path works, follow the [Desktop User Guide](desktop_user_guide.md) for first launch, projects, import (copies, not moves), and export. Manual matrix rows: [Desktop Testing Matrix](desktop_testing.md).

---

## Out of scope on this page

- Code signing, notarization, SmartScreen exemption, or store listing
- Changing packaging scripts or `APP_VERSION`
- Publishing a GitHub Release
- Tray hide-to-background behavior (window close is still quit)
- Phase 10 / new desktop feature gates

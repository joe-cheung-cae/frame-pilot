# Leftover: NSIS upgrade stop on locked sidecar `_internal` (2026-09-09)

> Language: **English** | [中文](2026-09-09-nsis-locked-internal-upgrade.zh.md)

**GitHub:** [joe-cheung-cae/frame-pilot#198](https://github.com/joe-cheung-cae/frame-pilot/issues/198). Joe’s Win11 upgrade of unsigned `v2.1.2-desktop` NSIS hit **Error opening file for writing** on `%LOCALAPPDATA%\FramePilot\framepilot-api\_internal\MSVCP140.dll`. Repeated **Ignore** left a half-written `_internal` tree; new-project Import/Export stayed blank. That is a broken install, not a [#195](https://github.com/joe-cheung-cae/frame-pilot/pull/195) regression. Do not reopen [#194](https://github.com/joe-cheung-cae/frame-pilot/issues/194), [#196](https://github.com/joe-cheung-cae/frame-pilot/issues/196), or [#190](https://github.com/joe-cheung-cae/frame-pilot/issues/190). Do not touch [#41](https://github.com/joe-cheung-cae/frame-pilot/issues/41) / D3.06 tray. Do not invent Phase 10.

**Branch:** `cursor/nsis-locked-internal-upgrade-b75d`. Do not merge to `main`. Implementer does not merge.

**Related:** `develop_plan.md` §1.1; [docs/desktop_install.md](../desktop_install.md); `apps/desktop/src-tauri/windows/hooks.nsh`; `apps/desktop/src-tauri/tauri.conf.json` (`bundle.windows.nsis.installerHooks`).

---

## 1. Why leftover, not Phase 10

Phase 9 remaining-stretch is closed. Tauri’s stock NSIS `CheckIfAppIsRunning` only stops `${MAINBINARYNAME}.exe` (`framepilot-desktop.exe`). The PyInstaller one-dir sidecar `framepilot-api.exe` keeps `_internal` DLLs locked. NSIS then offers Abort / Retry / **Ignore**. Ignore continues past locked files and ships a broken tree.

This leftover wires `NSIS_HOOK_PREINSTALL` / `NSIS_HOOK_PREUNINSTALL` so upgrade/install **stops** with Retry / Cancel (no Ignore) until the shell, sidecar, and known lock targets are free. Cancel Aborts **before** File copies, so the previous `_internal` tree is not half-overwritten.

Do **not** invent Phase 10 / S10 / 2.3. Product string stays `2.1.0-desktop`. Do not bump `APP_VERSION`. A new unsigned Release tag is a follow-up after merge — not this issue.

---

## 2. Locked decisions

1. **Local-first.** No cloud upload, login, payment, telemetry, or bundled neural models.
2. **Block, then retry.** Prompt to **File → Quit**. Retry may force-close `framepilot-desktop.exe` / `FramePilot.exe` / `framepilot-api.exe` (shell first, so the sidecar supervisor cannot respawn). Cancel / silent-still-locked **Abort**. Never `MB_ABORTRETRYIGNORE` / `IDIGNORE` / `SetOverwrite try`.
3. **Probe lock targets** that exist: main exe, `framepilot-api.exe`, `_internal\MSVCP140.dll`, `_internal\VCRUNTIME140.dll`.
4. **Unsigned only.** No Authenticode, notarize, staple, SmartScreen exemption, or store listing. Do not claim a Win11 GUI pass.
5. **No `APP_VERSION` bump.** No `tauri-action`. No tray / D3.06 / #41.
6. **One draft PR.** Body must include `Closes #198`. Implementer does not merge.
7. **Out:** new unsigned tag/Release, signing, Phase 10, treating blank Import/Export as a #195 regression when `_internal` is incomplete.

---

## 3. Status board

Leftover NSIS locked `_internal` upgrade

- [x] 需求拆解 — bilingual leftover plan + GitHub issue [#198](https://github.com/joe-cheung-cae/frame-pilot/issues/198)
- [x] 开发 — `installerHooks` PREINSTALL/PREUNINSTALL block on running shell/sidecar and locked `_internal` files; tutorial + matrix acceptance steps
- [x] 测试 — `scripts/check-nsis-locked-upgrade-hooks.sh`; `npm run test:scripts`
- [ ] 上线 — merge + new unsigned NSIS from `desktop.yml` (implementer does not merge)
- [ ] DoD-ticked — leftover-plan 上线 after a #198+ NSIS exists; do **not** invent a dated Win11 GUI pass / Phase 10 / re-tick §2.2

---

## 4. Tick rules

| When | Tick | Do not tick |
| ---- | ---- | ----------- |
| 需求拆解 | leftover board 需求拆解 | 上线; §2.2 |
| 开发 + script checks | leftover board 开发 + 测试 | 上线; Gatekeeper-clean; store listing; Win11 GUI pass |
| #198+ NSIS is published (Actions or a later Release) | leftover board 上线 + DoD-ticked; §1.1 leftover shipped | §2.2 re-tick; public signing checklist; Phase 10; invent Win11 pass |

---

## 5. Win11 acceptance: upgrade with the app still running

Do not invent a pass in this PR. Use this path on a real Win11 host after a #198+ NSIS exists.

1. Install a previous unsigned NSIS (`v2.1.2-desktop` is a valid baseline).
2. Start **FramePilot**. Wait until the project UI is up (sidecar has started). Do **not** quit.
3. Run the **new** NSIS (this leftover’s `desktop.yml` artifact, or a later unsigned Release — not the same `v2.1.2-desktop` setup that lacks the hooks).
4. **Pass:** the installer **stops** with Retry / Cancel telling you to close FramePilot / `framepilot-api`. There is no Ignore-through loop of **Error opening file for writing**. **Cancel** leaves the previous `%LOCALAPPDATA%\FramePilot` tree intact (no half-written `_internal`).
5. In FramePilot: **File → Quit** (or click **Retry** after quit so the hook can force-close leftovers). Finish the wizard.
6. **Pass:** `%LOCALAPPDATA%\FramePilot\framepilot-api\_internal\MSVCP140.dll` exists after install. Cold start → create a project → Import / Export open (same as #195).
7. **Fail:** Ignore is offered as a way to finish; Import/Export stay blank because `_internal` is incomplete.

Published `v2.1.2-desktop` NSIS does **not** include these hooks. If that older wizard shows **Error opening file for writing**, click **Abort**, quit FramePilot, and retry — never Ignore.

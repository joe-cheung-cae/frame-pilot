# Leftover: unsigned desktop Release with NSIS locked-file hooks (2026-09-09)

> Language: **English** | [中文](2026-09-09-unsigned-desktop-nsis-hooks-release.zh.md)

**GitHub:** [joe-cheung-cae/frame-pilot#200](https://github.com/joe-cheung-cae/frame-pilot/issues/200). Created after the Win11 NSIS locked `_internal` upgrade hooks landed on `main` ([#198](https://github.com/joe-cheung-cae/frame-pilot/issues/198) / [#199](https://github.com/joe-cheung-cae/frame-pilot/pull/199), SHA `d9d29e8e67fc9849f1878ba9f982b4211a94d76b`). Do not reopen [#198](https://github.com/joe-cheung-cae/frame-pilot/issues/198), [#196](https://github.com/joe-cheung-cae/frame-pilot/issues/196), or [#194](https://github.com/joe-cheung-cae/frame-pilot/issues/194). Do not touch [#41](https://github.com/joe-cheung-cae/frame-pilot/issues/41) / D3.06 tray. Do not invent Phase 10.

**Branch:** `cursor/unsigned-desktop-nsis-hooks-release-f2b9` from `d9d29e8e67fc9849f1878ba9f982b4211a94d76b`. Do not checkout `main` for commits. Do not merge to `main`. Implementer does not merge.

**Related:** `develop_plan.md` §1.1; [docs/desktop_install.md](../desktop_install.md); `.github/workflows/desktop.yml` (existing NSIS/DMG build); `.github/workflows/desktop-release.yml` (unsigned publish).

---

## 1. Why leftover, not Phase 10

Phase 9 remaining-stretch is closed. The #199 NSIS `installerHooks` / `hooks.nsh` locked-file stop is on `main`. Joe’s Win11 upgrade-while-running check still needs **new unsigned installers** — `v2.1.2-desktop` predates those hooks.

This leftover retargets the unsigned publish to `v2.1.3-desktop` and refuses pre-#198 artifacts so the published NSIS includes Retry/Cancel (no Ignore-through).

Do **not** invent Phase 10 / S10 / 2.3. Product string stays `2.1.0-desktop`. Do not bump `APP_VERSION`.

---

## 2. Locked decisions

1. **Local-first.** No cloud upload, login, payment, telemetry, or bundled neural models.
2. **Reuse `desktop.yml` packages.** Do not add signing, notarize, staple, or `tauri-action`. Do not launch packaged GUI from `verify.yml` or from the publish workflow.
3. **Unsigned only.** No Authenticode, Developer ID, notarize, staple, SmartScreen exemption, or store listing. Do not claim Gatekeeper-clean or SmartScreen-clean.
4. **Release notes** must say **unsigned**, name the #198/#199 locked-file stop (Retry/Cancel, no Ignore-through) plus the earlier #194/#195 Import/Export fix and #191 sidecar ready-line / 120s fix, and link [docs/desktop_install.md](../desktop_install.md) and [docs/desktop_install.zh.md](../desktop_install.zh.md).
5. **Tag** `v2.1.3-desktop`. Title includes `(unsigned)`. Attach only the NSIS `.exe` and macOS `.dmg`. Do not attach leftover GUI-evidence zips. Installer filenames stay `FramePilot_2.1.0-desktop_*` (no `APP_VERSION` bump).
6. **Refuse pre-#198 artifacts.** Publish only from a `desktop.yml` run whose `headSha` is `d9d29e8e67fc9849f1878ba9f982b4211a94d76b` or a descendant **and** that has both installer artifacts. Leftover GUI red after the uploads is allowed.
7. **No `APP_VERSION` bump.** No `tauri-action`. No `TAURI_SIGNING_PRIVATE_KEY`. No `latest.json` auto-download/install.
8. **One draft PR.** Body must include `Closes #200`. Implementer does not merge.
9. **Out:** #41 / D3.06 tray changes, Phase 10, signing, SHA256SUMS public-release checklist, claiming a signed store release.

---

## 3. Status board

Leftover unsigned desktop Release with NSIS locked-file hooks

- [x] 需求拆解 — bilingual leftover plan + GitHub issue [#200](https://github.com/joe-cheung-cae/frame-pilot/issues/200)
- [x] 开发 — `desktop-release.yml` publishes `v2.1.3-desktop` from a #198+ installer run; tutorial prefers that Release
- [x] 测试 — release-notes + workflow script checks; `npm run test:scripts`
- [ ] 上线 — GitHub Release `v2.1.3-desktop` with NSIS + DMG after merge (implementer does not merge)
- [ ] DoD-ticked — leftover-plan 上线 after the Release URL exists; do **not** re-tick §2.2 / invent Phase 10 / invent a Win11 GUI pass

---

## 4. Tick rules

| When | Tick | Do not tick |
| ---- | ---- | ----------- |
| 需求拆解 | leftover board 需求拆解 | 上线; §2.2 |
| 开发 + script checks | leftover board 开发 + 测试 | 上线; Gatekeeper-clean; store listing; Win11 GUI pass |
| `v2.1.3-desktop` Release has NSIS + DMG | leftover board 上线 + DoD-ticked; §1.1 leftover shipped | §2.2 re-tick; public signing checklist; Phase 10 |

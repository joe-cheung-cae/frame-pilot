# Leftover: unsigned desktop GitHub Release (2026-09-09)

> Language: **English** | [中文](2026-09-09-unsigned-desktop-release.zh.md)

**GitHub:** [joe-cheung-cae/frame-pilot#188](https://github.com/joe-cheung-cae/frame-pilot/issues/188). Created after the unsigned install tutorial shipped ([#186](https://github.com/joe-cheung-cae/frame-pilot/issues/186) / [#187](https://github.com/joe-cheung-cae/frame-pilot/pull/187), SHA `f0ad7fc00fb7d722d97c2d154116269d9abb6f68`). Do not reopen [#186](https://github.com/joe-cheung-cae/frame-pilot/issues/186). Do not touch [#41](https://github.com/joe-cheung-cae/frame-pilot/issues/41) / D3.06 tray. Do not invent Phase 10.

**Branch:** `cursor/unsigned-desktop-release-679f` from `f0ad7fc00fb7d722d97c2d154116269d9abb6f68`. Do not checkout `main` for commits. Do not merge to `main`. Implementer does not merge.

**Related:** `develop_plan.md` §1.1; [docs/desktop_install.md](../desktop_install.md); `.github/workflows/desktop.yml` (existing NSIS/DMG build); `.github/workflows/desktop-release.yml` (unsigned publish).

---

## 1. Why leftover, not Phase 10

Phase 9 remaining-stretch is closed. The install tutorial ([#186](https://github.com/joe-cheung-cae/frame-pilot/issues/186)) is on `main`. Joe standing order: signing / notarization / SmartScreen·store stay deferred. This leftover only publishes one **unsigned** GitHub Release so QA can download Windows NSIS + macOS DMG from a durable Release page.

Do **not** invent Phase 10 / S10 / 2.3. Product stays `2.1.0-desktop`. Do not bump `APP_VERSION`.

---

## 2. Locked decisions

1. **Local-first.** No cloud upload, login, payment, telemetry, or bundled neural models.
2. **Reuse existing `desktop.yml` packages.** Do not rebuild NSIS/DMG in this leftover. Do not change packaging scripts. Do not launch packaged GUI from `verify.yml` or from the publish workflow.
3. **Unsigned only.** No Authenticode, Developer ID, notarize, staple, SmartScreen exemption, or store listing. Do not claim Gatekeeper-clean or SmartScreen-clean.
4. **Release notes** must say **unsigned** and link [docs/desktop_install.md](../desktop_install.md) and [docs/desktop_install.zh.md](../desktop_install.zh.md).
5. **Tag** `v2.1.0-desktop`. Title includes `(unsigned)`. Attach only the NSIS `.exe` and macOS `.dmg`. Do not attach leftover GUI-evidence zips.
6. **No `APP_VERSION` bump.** No `tauri-action`. No `TAURI_SIGNING_PRIVATE_KEY`. No `latest.json` auto-download/install.
7. **One draft PR.** Body must include `Closes #188`. Implementer does not merge.
8. **Out:** #41 / D3.06 tray changes, Phase 10, signing, SHA256SUMS public-release checklist, claiming a signed store release.

---

## 3. Status board

Leftover unsigned desktop GitHub Release

- [x] 需求拆解 — bilingual leftover plan + GitHub issue [#188](https://github.com/joe-cheung-cae/frame-pilot/issues/188)
- [x] 开发 — `desktop-release.yml` publishes latest successful `desktop.yml` NSIS + DMG; tutorial prefers that Release
- [x] 测试 — release-notes + workflow script checks; `npm run test:scripts`
- [ ] 上线 — GitHub Release `v2.1.0-desktop` with NSIS + DMG after merge runs `desktop-release.yml` (implementer does not merge)
- [ ] DoD-ticked — leftover-plan 上线 after the Release URL exists; do **not** re-tick §2.2 / invent Phase 10

---

## 4. Tick rules

| When | Tick | Do not tick |
| ---- | ---- | ----------- |
| 需求拆解 | leftover board 需求拆解 | 上线; §2.2 |
| 开发 + script tests | leftover board 开发 + 测试 | 上线; Gatekeeper-clean; store listing |
| `v2.1.0-desktop` Release has NSIS + DMG | leftover board 上线 + DoD-ticked; §1.1 leftover shipped | §2.2 re-tick; public signing checklist; Phase 10 |

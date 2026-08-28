# Desktop Code Signing Runbook

> Language: **English** | [中文](desktop_signing.zh.md)

This runbook describes how FramePilot desktop installers are signed (Windows Authenticode) and notarized (macOS Developer ID), where secrets must live, and how internal testers should treat **unsigned** builds until certificates are configured.

It is documentation only. It does not add signing secrets to the repository or require certificates for the first release candidate.

## Current status

- Tauri product name: `FramePilot`
- Bundle identifier: `com.framepilot.app` (see `apps/desktop/src-tauri/tauri.conf.json`)
- Installer targets: Windows NSIS (`.exe`) and macOS DMG (`.dmg`)
- CI workflow: `.github/workflows/desktop.yml` builds and **uploads unsigned** installer artifacts on `windows-latest` and `macos-latest`
- No code-signing certificates or Apple notarization credentials are stored in this repository
- Missing certificates must **not** fail the first desktop RC; unsigned installers remain acceptable for internal testing

## Secrets and certificate storage

Never commit private keys, `.p12` / `.pfx` files, Apple API keys, notarization passwords, or base64-encoded cert blobs to Git.

When signing is enabled later, store credentials only as GitHub Actions secrets (or an equivalent CI secret store), for example:

| Platform | Typical secret material (examples only) |
| -------- | ---------------------------------------- |
| Windows  | Authenticode certificate (PFX) + password, or a cloud signing service token |
| macOS    | Developer ID Application certificate, Apple ID / App Store Connect API key, team ID, notarization credentials |

Local developer machines may use the OS keychain for one-off signed builds. Production release signing should run in CI so keys stay off laptops and out of the tree.

Do not paste secret values into issues, PRs, feasibility notes, or this runbook.

## Windows Authenticode (overview)

Authenticode signs the Windows installer (and optionally the nested app binaries) so SmartScreen and enterprise policies can trust the publisher.

High-level flow when certificates exist:

1. Obtain a code-signing certificate from a trusted CA (or an org-managed signing service).
2. Import the certificate into the CI secret store (not the repo).
3. During `tauri build` / post-build, sign the NSIS `.exe` with `signtool` or the Tauri Windows signing hooks.
4. Optionally timestamp the signature so it remains valid after the cert expires.
5. Verify the signature locally (`signtool verify` or Properties → Digital Signatures) before publishing.

Until those secrets exist, CI continues to upload **unsigned** NSIS installers. Windows may show SmartScreen / “Unknown publisher” warnings; that is expected for internal builds.

## macOS Developer ID and notarization (overview)

macOS distribution outside the Mac App Store uses a **Developer ID Application** signature plus **Apple notarization** so Gatekeeper accepts the app.

High-level flow when credentials exist:

1. Enroll in the Apple Developer Program and create a Developer ID Application certificate for team use with bundle id `com.framepilot.app`.
2. Store the signing identity and notarization credentials in CI secrets (not the repo).
3. Sign the `.app` during `tauri build`, package the DMG, then submit the DMG (or zip) to Apple’s notary service.
4. Staple the notarization ticket to the DMG / app so offline Gatekeeper checks succeed.
5. Verify with `spctl --assess` / `xcrun stapler validate` before publishing.

Until those credentials exist, CI continues to upload **unsigned** DMGs. macOS may block open with Gatekeeper (“cannot be opened because the developer cannot be verified”); that is expected for internal builds.

## Internal testers: unsigned installers

Unsigned Windows and macOS artifacts from the `desktop` workflow are intended for **internal testers and developers only**, not for public download pages.

Testers should:

- Download artifacts only from the project’s GitHub Actions runs or other maintainer-controlled channels
- Expect OS trust warnings (SmartScreen / Gatekeeper) on unsigned packages
- Prefer a disposable or dedicated test machine/account when possible
- Not redistribute unsigned installers as “official” releases
- Report install or launch failures separately from OS trust dialogs

On Windows, bypass SmartScreen only if you trust the build source (for example “More info” → “Run anyway” on a known Actions artifact).

On macOS, clear Gatekeeper quarantine only for a known-good internal DMG (for example remove the quarantine attribute on the downloaded app, or open via Control-click → Open). Prefer signed+notarized builds once available.

## First RC policy

The first desktop release candidate may ship or be validated with **unsigned** installers when certificates are not yet available. Do not block RC tagging or Phase 4 acceptance solely on missing Authenticode or Apple notarization credentials. Signing remains a follow-up once secrets are provisioned in CI.

## Related files

- `.github/workflows/desktop.yml` — unsigned Windows/macOS installer CI
- `apps/desktop/src-tauri/tauri.conf.json` — `identifier`, NSIS, and DMG bundle config
- `docs/plans/2026-08-18-desktop-packaging.md` — D4.05 task definition

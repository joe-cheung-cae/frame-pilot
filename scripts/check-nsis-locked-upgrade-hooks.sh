#!/usr/bin/env bash
# Static checks for leftover #198: NSIS must block on locked sidecar files.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
hooks="$repo_root/apps/desktop/src-tauri/windows/hooks.nsh"
conf="$repo_root/apps/desktop/src-tauri/tauri.conf.json"
fail=0

die() {
  echo "check-nsis-locked-upgrade-hooks: $*" >&2
  fail=1
}

[[ -f "$hooks" ]] || die "missing $hooks"
[[ -f "$conf" ]] || die "missing $conf"

if ! grep -q '"installerHooks": "./windows/hooks.nsh"' "$conf"; then
  die "tauri.conf.json must set bundle.windows.nsis.installerHooks to ./windows/hooks.nsh"
fi

if ! grep -q '"version": "2.1.0-desktop"' "$conf"; then
  die "do not bump tauri.conf.json version / APP_VERSION for this leftover"
fi

if ! grep -q '"installMode": "currentUser"' "$conf"; then
  die "NSIS installMode must stay currentUser"
fi

for needle in \
  "NSIS_HOOK_PREINSTALL" \
  "NSIS_HOOK_PREUNINSTALL" \
  "framepilot-api.exe" \
  "MAINBINARYNAME" \
  "MSVCP140.dll" \
  "_internal" \
  "MB_RETRYCANCEL" \
  "Abort" \
  "File -> Quit" \
  "not Ignore"
do
  if ! grep -q -F "$needle" "$hooks"; then
    die "hooks.nsh must contain: $needle"
  fi
done

if grep -q "MB_ABORTRETRYIGNORE" "$hooks" || grep -q "IDIGNORE" "$hooks"; then
  die "hooks.nsh must not offer Ignore (MB_ABORTRETRYIGNORE / IDIGNORE)"
fi

if grep -q "SetOverwrite try" "$hooks"; then
  die "hooks.nsh must not skip locked files with SetOverwrite try"
fi

if ! grep -q "KillProcessCurrentUser" "$hooks"; then
  die "hooks.nsh must stop the running shell/sidecar, not only prompt"
fi

if grep -q "NSIS_HOOK_POSTINSTALL" "$hooks"; then
  die "do not add unrelated POSTINSTALL scope"
fi

install_en="$repo_root/docs/desktop_install.md"
install_zh="$repo_root/docs/desktop_install.zh.md"
for doc in "$install_en" "$install_zh"; do
  [[ -f "$doc" ]] || die "missing $doc"
done

if ! grep -q "Upgrade (close the app first)" "$install_en"; then
  die "desktop_install.md must document close-app-before-upgrade"
fi
if ! grep -q "Win11 acceptance: upgrade while the app is still running" "$install_en"; then
  die "desktop_install.md must include Win11 upgrade-with-app-running acceptance steps"
fi
if ! grep -q "Abort -- not Ignore\|Abort — not Ignore\|click Abort" "$install_en"; then
  die "desktop_install.md must tell users not to Ignore locked-file errors"
fi
if ! grep -q "#198" "$install_en"; then
  die "desktop_install.md must cite leftover #198"
fi
if ! grep -q "先退出再升级\|先关进程再升级\|升级（先关掉应用）" "$install_zh"; then
  die "desktop_install.zh.md must document close-app-before-upgrade"
fi
if ! grep -q "不要点「忽略」\|不要点忽略\|不要点 Ignore" "$install_zh"; then
  die "desktop_install.zh.md must tell users not to Ignore locked-file errors"
fi

plan_en="$repo_root/docs/plans/2026-09-09-nsis-locked-internal-upgrade.md"
if [[ ! -f "$plan_en" ]] || ! grep -q "#198" "$plan_en"; then
  die "leftover plan 2026-09-09-nsis-locked-internal-upgrade.md must exist and cite #198"
fi
if ! grep -q "Closes #198" "$plan_en"; then
  die "leftover plan must require PR body Closes #198"
fi

exit "$fail"

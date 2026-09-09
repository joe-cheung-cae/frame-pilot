#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v rg > /dev/null 2>&1; then
  rg() {
    grep -E "$@"
  }
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

expect_success() {
  local name="$1"
  shift

  if output="$("$@" 2>&1)"; then
    echo "ok - $name"
    return
  fi

  echo "not ok - $name" >&2
  printf '%s\n' "$output" >&2
  exit 1
}

expect_failure() {
  local name="$1"
  local expected="$2"
  shift 2

  set +e
  output="$("$@" 2>&1)"
  status=$?
  set -e

  if [[ "$status" -eq 0 ]]; then
    echo "not ok - $name: command unexpectedly succeeded" >&2
    printf '%s\n' "$output" >&2
    exit 1
  fi

  if [[ "$output" != *"$expected"* ]]; then
    echo "not ok - $name: expected output to contain '$expected'" >&2
    printf '%s\n' "$output" >&2
    exit 1
  fi

  echo "ok - $name"
}

validation_notes="$tmpdir/validation-notes.md"
printf '# Test Validation Notes\n' > "$validation_notes"

validation_decision="$tmpdir/validation-decision.md"
cat > "$validation_decision" << EOF
# Test Validation Decision

Status: **accepted**.

## Validation Evidence

Validation notes file: $validation_notes.
Validation verdict: pass.
Release decision impact: accepted for rc2.

## Waiver Record

Waiver status: not waived.
EOF

expect_success \
  "validation evidence closes the decision gate" \
  bash scripts/check-validation-decision.sh "$validation_decision"

waiver_decision="$tmpdir/waiver-decision.md"
cat > "$waiver_decision" << 'EOF'
# Test Validation Decision

Status: **accepted**.

## Validation Evidence

Validation notes file: pending.
Validation verdict: pending.
Release decision impact: pending.

## Waiver Record

Waiver status: waived.

- Waiver owner: Release Owner
- Waiver date: 2026-06-05
- Reason: Test waiver reason.
- Accepted risk: Test accepted risk.
- Follow-up task: Record validation notes later.
EOF

expect_success \
  "explicit waiver closes the decision gate" \
  bash scripts/check-validation-decision.sh "$waiver_decision"

waiver_not_applicable_decision="$tmpdir/waiver-not-applicable-decision.md"
cat > "$waiver_not_applicable_decision" << 'EOF'
# Test Validation Decision

Status: waived.

## Validation Evidence

Validation notes file: not applicable.
Validation verdict: not completed.
Release decision impact: rc2 may proceed as an engineering pre-release.

## Waiver Record

Waiver status: waived.

- Waiver owner: Release Owner
- Waiver date: 2026-06-05
- Reason: Test waiver reason.
- Accepted risk: Test accepted risk.
- Follow-up task: Record validation notes later.
EOF

expect_success \
  "waiver allows not applicable validation notes file" \
  bash scripts/check-validation-decision.sh "$waiver_not_applicable_decision"

pending_decision="$tmpdir/pending-decision.md"
cat > "$pending_decision" << 'EOF'
# Test Validation Decision

Status: **pending**.

## Validation Evidence

Validation notes file: pending.
Validation verdict: pending.
Release decision impact: pending.

## Waiver Record

Waiver status: not waived.
EOF

expect_failure \
  "pending status keeps the decision gate open" \
  "still has pending status" \
  bash scripts/check-validation-decision.sh "$pending_decision"

missing_notes_decision="$tmpdir/missing-notes-decision.md"
cat > "$missing_notes_decision" << EOF
# Test Validation Decision

Status: **accepted**.

## Validation Evidence

Validation notes file: $tmpdir/missing-notes.md.
Validation verdict: pass.
Release decision impact: accepted for rc2.

## Waiver Record

Waiver status: not waived.
EOF

expect_failure \
  "missing validation notes file keeps the decision gate open" \
  "does not exist" \
  bash scripts/check-validation-decision.sh "$missing_notes_decision"

incomplete_waiver_decision="$tmpdir/incomplete-waiver-decision.md"
cat > "$incomplete_waiver_decision" << 'EOF'
# Test Validation Decision

Status: **accepted**.

## Validation Evidence

Validation notes file: pending.
Validation verdict: pending.
Release decision impact: pending.

## Waiver Record

Waiver status: waived.

- Waiver owner: Release Owner
- Waiver date: pending
- Reason: Test waiver reason.
- Accepted risk: Test accepted risk.
- Follow-up task: Record validation notes later.
EOF

expect_failure \
  "incomplete waiver keeps the decision gate open" \
  "Waiver date" \
  bash scripts/check-validation-decision.sh "$incomplete_waiver_decision"

photo_dir="$tmpdir/private-input"
mkdir -p "$photo_dir/nested"
touch \
  "$photo_dir/private-family-name.JPG" \
  "$photo_dir/nested/sensitive-place.png" \
  "$photo_dir/ignored.txt"

tier_a_notes="$tmpdir/tier-a-notes.md"
expect_success \
  "tier a validation runner writes sanitized notes" \
  python3 scripts/run_tier_a_validation.py \
  --photo-dir "$photo_dir" \
  --output "$tier_a_notes" \
  --tier A \
  --max-photos 50

expect_success \
  "tier a validation notes include anonymized ids" \
  rg "photo_0001" "$tier_a_notes"

expect_success \
  "tier a validation notes include file type counts" \
  rg "File Type Counts" "$tier_a_notes"

expect_failure \
  "tier a validation notes omit input path" \
  "" \
  rg "$photo_dir" "$tier_a_notes"

expect_failure \
  "tier a validation notes omit original filenames" \
  "" \
  rg "private-family-name|sensitive-place" "$tier_a_notes"

write_pair() {
  local path="$1"
  local title="$2"
  local extra="${3:-}"
  local dir
  dir="$(dirname "$path")"
  local base
  base="$(basename "$path" .md)"
  mkdir -p "$dir"
  printf '# %s\n\n> Language: **English** | [中文](%s.zh.md)\n\n%s' \
    "$title" "$base" "$extra" > "$path"
  printf '# %s\n\n> 语言：[English](%s.md) | **中文**\n\n%s' \
    "$title" "$base" "$extra" > "${path%.md}.zh.md"
}

link_root="$tmpdir/markdown-links"
mkdir -p "$link_root/docs"
write_pair "$link_root/README.md" "Root" "See [API](docs/api.md).\n"
write_pair "$link_root/AGENTS.md" "Agents"
write_pair "$link_root/develop_plan.md" "Plan"
write_pair "$link_root/implement_goals.md" "Goals"
write_pair "$link_root/docs/api.md" "API" \
  "See [Scoring](scoring.md) and [remote](https://example.com/missing.md).\n"
write_pair "$link_root/docs/scoring.md" "Scoring"

expect_success \
  "markdown link check accepts existing relative targets" \
  bash scripts/check-markdown-links.sh "$link_root"

extra_desktop="$tmpdir/extra-desktop"
cp -a "$link_root" "$extra_desktop"
mkdir -p "$extra_desktop/apps/desktop"
printf '# Desktop\n\n> Language: **English** | [中文](README.zh.md)\n\nShell.\n' \
  > "$extra_desktop/apps/desktop/README.md"

expect_failure \
  "markdown link check rejects a missing desktop README Chinese counterpart" \
  "missing Chinese counterpart" \
  bash scripts/check-markdown-links.sh "$extra_desktop"

write_pair "$extra_desktop/apps/desktop/README.md" "Desktop shell"
mkdir -p "$extra_desktop/tests/desktop"
write_pair "$extra_desktop/tests/desktop/workflow.md" "Workflow"

expect_success \
  "markdown link check accepts extra living desktop pages" \
  bash scripts/check-markdown-links.sh "$extra_desktop"

missing_zh="$tmpdir/missing-zh"
cp -a "$link_root" "$missing_zh"
rm -f "$missing_zh/README.zh.md"

expect_failure \
  "markdown link check rejects a missing Chinese counterpart" \
  "missing Chinese counterpart" \
  bash scripts/check-markdown-links.sh "$missing_zh"

missing_en="$tmpdir/missing-en"
cp -a "$link_root" "$missing_en"
rm -f "$missing_en/README.md"

expect_failure \
  "markdown link check rejects a missing English counterpart" \
  "missing English counterpart" \
  bash scripts/check-markdown-links.sh "$missing_en"

empty_zh="$tmpdir/empty-zh"
cp -a "$link_root" "$empty_zh"
printf '   \n' > "$empty_zh/README.zh.md"

expect_failure \
  "markdown link check rejects an empty Chinese counterpart" \
  "empty living page" \
  bash scripts/check-markdown-links.sh "$empty_zh"

empty_en="$tmpdir/empty-en"
cp -a "$link_root" "$empty_en"
printf '   \n' > "$empty_en/README.md"

expect_failure \
  "markdown link check rejects an empty English counterpart" \
  "empty living page" \
  bash scripts/check-markdown-links.sh "$empty_en"

missing_link="$tmpdir/missing-link"
cp -a "$link_root" "$missing_link"
printf '# Root\n\nSee [API](docs/api.md).\n' > "$missing_link/README.md"

expect_failure \
  "markdown link check rejects a missing counterpart link" \
  "missing counterpart link" \
  bash scripts/check-markdown-links.sh "$missing_link"

stale_handoff="$tmpdir/stale-handoff"
cp -a "$link_root" "$stale_handoff"
mkdir -p "$stale_handoff/docs/handoff"
printf '# stale\n' > "$stale_handoff/docs/handoff/STATUS.md"

expect_failure \
  "markdown link check rejects a stale handoff path" \
  "stale handoff path present" \
  bash scripts/check-markdown-links.sh "$stale_handoff"

stale_review="$tmpdir/stale-review"
cp -a "$link_root" "$stale_review"
mkdir -p "$stale_review/docs/plans"
printf '# stale review\n' > "$stale_review/docs/plans/2026-08-18-desktop-packaging-review.md"

expect_failure \
  "markdown link check rejects a stale packaging-review path" \
  "packaging-review" \
  bash scripts/check-markdown-links.sh "$stale_review"

printf '\nSee [Missing](docs/does-not-exist.md).\n' >> "$link_root/README.md"

expect_failure \
  "markdown link check rejects missing relative targets" \
  "does-not-exist.md" \
  bash scripts/check-markdown-links.sh "$link_root"

expect_success \
  "repository markdown links resolve" \
  bash scripts/check-markdown-links.sh

artifact_repo="$tmpdir/artifact-repo"
mkdir -p "$artifact_repo/apps/desktop/src-tauri/icons"
git -C "$artifact_repo" init -q
printf 'png' > "$artifact_repo/apps/desktop/src-tauri/icons/128x128.png"
git -C "$artifact_repo" add apps/desktop/src-tauri/icons/128x128.png
expect_success \
  "tracked tauri icons are allowed by the artifact check" \
  bash -c "cd '$artifact_repo' && bash '$repo_root/scripts/check-release-artifacts.sh'"

printf 'png' > "$artifact_repo/apps/desktop/other.png"
git -C "$artifact_repo" add apps/desktop/other.png
expect_failure \
  "tracked png outside tauri icons still fails the artifact check" \
  "apps/desktop/other.png" \
  bash -c "cd '$artifact_repo' && bash '$repo_root/scripts/check-release-artifacts.sh'"

expect_success \
  "verify.yml builds the frozen sidecar then runs test:sidecar" \
  bash -c "awk '
    /packaging:sidecar/ { saw_build = 1 }
    /test:sidecar/ { if (saw_build) found = 1 }
    END { exit found ? 0 : 1 }
  ' '$repo_root/.github/workflows/verify.yml'"

expect_success \
  "verify.yml keeps frozen sidecar /health as an independent job" \
  bash -c "grep -q '^  sidecar-health:' '$repo_root/.github/workflows/verify.yml'"

expect_success \
  "verify.yml runs npm run test:e2e as an independent job" \
  bash -c "awk '
    /^  e2e:/ { in_e2e = 1 }
    in_e2e && /^  [a-z]/ && !/^  e2e:/ { in_e2e = 0 }
    in_e2e && /playwright install/ { saw_install = 1 }
    in_e2e && /npm run test:e2e[[:space:]]*$/ { if (saw_install) found = 1 }
    END { exit found ? 0 : 1 }
  ' '$repo_root/.github/workflows/verify.yml'"

expect_success \
  "verify.yml runs npm run test:e2e:real-browser as an independent job" \
  bash -c "awk '
    /^  e2e-real-browser:/ { in_job = 1 }
    in_job && /^  [a-z]/ && !/^  e2e-real-browser:/ { in_job = 0 }
    in_job && /playwright install/ { saw_install = 1 }
    in_job && /npm run test:e2e:real-browser[[:space:]]*$/ { if (saw_install) found = 1 }
    END { exit found ? 0 : 1 }
  ' '$repo_root/.github/workflows/verify.yml'"

expect_success \
  "verify.yml default gate does not run large real-browser E2E" \
  bash -c "awk '
    /run:.*test:e2e:real-browser:large/ { found = 1 }
    /FRAMEPILOT_BROWSER_PERF_COUNT/ { found = 1 }
    END { exit found ? 1 : 0 }
  ' '$repo_root/.github/workflows/verify.yml'"

expect_success \
  "verify.yml runs npm run test:desktop:smoke as an independent job" \
  bash -c "awk '
    /^  desktop-smoke:/ { in_job = 1 }
    in_job && /^  [a-z]/ && !/^  desktop-smoke:/ { in_job = 0 }
    in_job && /npm run test:desktop:smoke[[:space:]]*$/ { found = 1 }
    END { exit found ? 0 : 1 }
  ' '$repo_root/.github/workflows/verify.yml'"

expect_success \
  "verify.yml desktop HTTP smoke job does not launch a packaged GUI" \
  bash -c "awk '
    /^  desktop-smoke:/ { in_job = 1 }
    in_job && /^  [a-z]/ && !/^  desktop-smoke:/ { in_job = 0 }
    in_job && /tauri build|nsis|dmg|codesign|notariz/ { found = 1 }
    END { exit found ? 1 : 0 }
  ' '$repo_root/.github/workflows/verify.yml'"

expect_success \
  "desktop.yml smokes frozen sidecar /health after PyInstaller" \
  bash -c "awk '
    /packaging:sidecar/ { saw_build = 1 }
    /test:sidecar/ { if (saw_build) found = 1 }
    END { exit found ? 0 : 1 }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "desktop.yml copies locked Windows signing secrets into env" \
  bash -c "awk '
    /secrets\\.WINDOWS_CERTIFICATE }}/ { saw_cert = 1 }
    /secrets\\.WINDOWS_CERTIFICATE_PASSWORD }}/ { saw_pass = 1 }
    END { exit (saw_cert && saw_pass) ? 0 : 1 }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "desktop.yml copies locked macOS signing secrets into env" \
  bash -c "awk '
    /secrets\\.APPLE_CERTIFICATE }}/ { saw_cert = 1 }
    /secrets\\.APPLE_CERTIFICATE_PASSWORD }}/ { saw_pass = 1 }
    /secrets\\.APPLE_SIGNING_IDENTITY }}/ { saw_id = 1 }
    /secrets\\.APPLE_TEAM_ID }}/ { saw_team = 1 }
    /secrets\\.APPLE_API_ISSUER }}/ { saw_issuer = 1 }
    /secrets\\.APPLE_API_KEY }}/ { saw_key = 1 }
    /secrets\\.APPLE_API_KEY_CONTENT }}/ { saw_content = 1 }
    END {
      exit (saw_cert && saw_pass && saw_id && saw_team && saw_issuer && saw_key && saw_content) ? 0 : 1
    }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "desktop.yml does not treat APPLE_API_KEY_PATH as a GitHub secret" \
  bash -c "awk '
    /secrets\\.APPLE_API_KEY_PATH/ { found = 1 }
    END { exit found ? 1 : 0 }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "desktop.yml Windows import and sign are gated on non-empty env" \
  bash -c "awk '
    /WINDOWS_CERTIFICATE:-/ { gated = 1 }
    /Import-PfxCertificate|certificateThumbprint/ { if (gated) saw_sign = 1 }
    /npx tauri build --bundles nsis/ && /--config/ { if (gated) saw_config = 1 }
    /npx tauri build --bundles nsis/ && !/--config/ { saw_unsigned = 1 }
    END { exit (gated && saw_sign && saw_config && saw_unsigned) ? 0 : 1 }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "desktop.yml macOS notarize is gated on non-empty env" \
  bash -c "awk '
    /APPLE_CERTIFICATE:-/ { gated = 1 }
    /APPLE_API_KEY_PATH|AuthKey_/ { if (gated) saw_key = 1 }
    /export APPLE_CERTIFICATE/ { if (gated) saw_export = 1 }
    /npx tauri build --bundles dmg/ { if (gated) saw_signed = 1 }
    END { exit (gated && saw_key && saw_export && saw_signed) ? 0 : 1 }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "desktop.yml missing-secret path has no exit 1" \
  bash -c "awk '
    /name: Build Tauri installer/ { in_step = 1 }
    in_step && /^      - name:/ && !/Build Tauri installer/ { in_step = 0 }
    in_step && /exit 1/ { found = 1 }
    END { exit found ? 1 : 0 }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "desktop.yml does not export empty APPLE_CERTIFICATE" \
  bash -c "awk '
    /unset APPLE_CERTIFICATE/ { saw_unset = 1 }
    /export APPLE_CERTIFICATE/ { saw_export = 1 }
    /APPLE_CERTIFICATE:-/ { saw_gate = 1 }
    END { exit (saw_unset && saw_export && saw_gate) ? 0 : 1 }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "desktop.yml rebuilds installers when bundled web UI changes" \
  bash -c "awk '
    /apps\\/web\\/\\*\\*/ { web = 1 }
    END { exit web ? 0 : 1 }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "desktop.yml keeps unsigned fallback and does not use tauri-action" \
  bash -c "awk '
    /tauri-apps\\/tauri-action/ { action = 1 }
    /TAURI_SIGNING_PRIVATE_KEY|secrets\\.APPLE_ID|secrets\\.APPLE_PASSWORD|KEYCHAIN_PASSWORD/ { extra = 1 }
    /contents: read/ { read_perm = 1 }
    END { exit (!action && !extra && read_perm) ? 0 : 1 }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "desktop.yml smokes packaged macOS DMG GUI after tauri dmg build" \
  bash -c "awk '
    /name: Build Tauri installer/ { in_build = 1 }
    in_build && /^      - name:/ && !/Build Tauri installer/ { in_build = 0 }
    in_build && /macos-dmg-gui-smoke|hdiutil attach/ { folded = 1 }
    /name: Smoke packaged macOS DMG GUI launch/ { in_smoke = 1 }
    in_smoke && /^      - / && !/Smoke packaged macOS DMG GUI launch/ { in_smoke = 0 }
    in_smoke && /runner.os == .macOS./ { gate = 1 }
    in_smoke && /macos-dmg-gui-smoke.sh/ { script = 1 }
    in_smoke && /bundle\\/dmg\\/\\*\\.dmg/ { dmg = 1 }
    in_smoke && /desktop-500-gui.sh|--count 500/ { folded_500 = 1 }
    END { exit (gate && script && dmg && !folded && !folded_500) ? 0 : 1 }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "desktop.yml launches packaged NSIS GUI via desktop-500-gui.sh" \
  bash -c "awk '
    /id: probe-windows/ { in_pw = 1 }
    in_pw && /^      - / && !/id: probe-windows/ { in_pw = 0 }
    in_pw && /runner.os == .Windows./ { pw_os = 1 }
    in_pw && /desktop-500-gui.sh/ { pw_script = 1 }
    in_pw && /--probe/ { pw_probe = 1 }
    in_pw && /timeout-minutes: 10/ { pw_t = 1 }
    in_pw && /macos-dmg-gui-smoke.sh/ { folded = 1 }
    /id: gui500-windows/ { in_gw = 1 }
    in_gw && /^      - / && !/id: gui500-windows/ { in_gw = 0 }
    in_gw && /always\(\)/ { gw_always = 1 }
    in_gw && /runner.os == .Windows./ { gw_os = 1 }
    in_gw && /steps\\.probe-windows\\.outcome == .success./ { gw_dep = 1 }
    in_gw && /desktop-500-gui.sh/ { gw_script = 1 }
    in_gw && /--count 500/ { gw_count = 1 }
    in_gw && /timeout-minutes: 45/ { gw_t = 1 }
    in_gw && /macos-dmg-gui-smoke.sh/ { folded = 1 }
    END {
      exit (pw_os && pw_script && pw_probe && pw_t && gw_always && gw_os && gw_dep && gw_script && gw_count && gw_t && !folded) ? 0 : 1
    }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "desktop.yml packaged ≥500 GUI probe and 500 sit after macOS DMG smoke" \
  bash -c "awk '
    /^  build:/ { in_job = 1 }
    in_job && /^    steps:/ { in_steps = 1 }
    in_job && !in_steps && /timeout-minutes: 180/ { job_t = 1 }
    /name: Smoke packaged macOS DMG GUI launch/ { smoke = NR }
    /id: probe-windows/ { pw = NR }
    /id: probe-macos/ { pm = NR }
    /id: gui500-windows/ { gw = NR }
    /id: gui500-macos/ { gm = NR }
    /id: probe-macos/ { in_pm = 1 }
    in_pm && /^      - / && !/id: probe-macos/ { in_pm = 0 }
    in_pm && /always\(\)/ { pm_always = 1 }
    in_pm && /runner.os == .macOS./ { pm_os = 1 }
    in_pm && /desktop-500-gui.sh/ { pm_script = 1 }
    in_pm && /--probe/ { pm_probe = 1 }
    in_pm && /timeout-minutes: 10/ { pm_t = 1 }
    /id: gui500-macos/ { in_gm = 1 }
    in_gm && /^      - / && !/id: gui500-macos/ { in_gm = 0 }
    in_gm && /always\(\)/ { gm_always = 1 }
    in_gm && /runner.os == .macOS./ { gm_os = 1 }
    in_gm && /steps\\.probe-macos\\.outcome == .success./ { gm_dep = 1 }
    in_gm && /desktop-500-gui.sh/ { gm_script = 1 }
    in_gm && /--count 500/ { gm_count = 1 }
    in_gm && /timeout-minutes: 40/ { gm_t = 1 }
    END {
      exit (job_t && smoke && pw > smoke && pm > smoke && gw > smoke && gm > smoke && pw < pm && pm < gw && gw < gm && pm_always && pm_os && pm_script && pm_probe && pm_t && gm_always && gm_os && gm_dep && gm_script && gm_count && gm_t) ? 0 : 1
    }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "desktop.yml header allows DMG smoke, desktop-500-gui.sh, and quit+job, not verify.yml GUI" \
  bash -c "awk '
    /^name:/ { after = 1 }
    !after && /macos-dmg-gui-smoke.sh/ { smoke = 1 }
    !after && /desktop-500-gui.sh/ { gui = 1 }
    !after && /desktop-quit-job-gui.sh/ { quit = 1 }
    !after && /Do not launch the packaged NSIS GUI/ { old = 1 }
    !after && /verify.yml/ { verify = 1 }
    END { exit (smoke && gui && quit && verify && !old) ? 0 : 1 }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "desktop.yml uploads distinct desktop-500-gui evidence artifacts from RUNNER_TEMP" \
  bash -c "awk '
    /name: FramePilot-desktop-500-gui-probe-windows/ { n1 = 1 }
    /name: FramePilot-desktop-500-gui-500-windows/ { n2 = 1 }
    /name: FramePilot-desktop-500-gui-probe-macos/ { n3 = 1 }
    /name: FramePilot-desktop-500-gui-500-macos/ { n4 = 1 }
    /desktop-500-gui\\/probe-windows/ { p1 = 1 }
    /desktop-500-gui\\/500-windows/ { p2 = 1 }
    /desktop-500-gui\\/probe-macos/ { p3 = 1 }
    /desktop-500-gui\\/500-macos/ { p4 = 1 }
    /if-no-files-found:.*probe-windows.outcome/ { e1 = 1 }
    /if-no-files-found:.*gui500-windows.outcome/ { e2 = 1 }
    /if-no-files-found:.*probe-macos.outcome/ { e3 = 1 }
    /if-no-files-found:.*gui500-macos.outcome/ { e4 = 1 }
    END { exit (n1 && n2 && n3 && n4 && p1 && p2 && p3 && p4 && e1 && e2 && e3 && e4) ? 0 : 1 }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "macos-dmg-gui-smoke.sh does not fold packaged 500 GUI import" \
  bash -c "awk '
    /desktop-500-gui\\.sh|--count[[:space:]]+500|importPhotosFromPaths/ { found = 1 }
    END { exit found ? 1 : 0 }
  ' '$repo_root/packaging/scripts/macos-dmg-gui-smoke.sh'"

expect_success \
  "desktop.yml packaged quit+job matrix is a distinct macOS step after 500" \
  bash -c "awk '
    /id: gui500-macos/ { gm = NR }
    /id: quit-job-macos/ { q = NR; in_q = 1 }
    in_q && /^      - / && !/id: quit-job-macos/ { in_q = 0 }
    in_q && /always\(\)/ { q_always = 1 }
    in_q && /runner.os == .macOS./ { q_os = 1 }
    in_q && /desktop-quit-job-gui.sh/ { q_script = 1 }
    in_q && /macos-dmg-gui-smoke.sh/ { folded_177 = 1 }
    in_q && /desktop-500-gui.sh/ { folded_179 = 1 }
    /name: FramePilot-desktop-quit-job-macos/ { art = 1 }
    /desktop-quit-job\\// { path = 1 }
    END {
      exit (gm && q > gm && q_always && q_os && q_script && art && path && !folded_177 && !folded_179) ? 0 : 1
    }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "desktop.yml packaged quit+job matrix is a distinct Windows step after 500" \
  bash -c "awk '
    /id: gui500-windows/ { gw = NR }
    /id: quit-job-windows/ { q = NR; in_q = 1 }
    in_q && /^      - / && !/id: quit-job-windows/ { in_q = 0 }
    in_q && /always\(\)/ { q_always = 1 }
    in_q && /runner.os == .Windows./ { q_os = 1 }
    in_q && /desktop-quit-job-gui.sh/ { q_script = 1 }
    in_q && /macos-dmg-gui-smoke.sh/ { folded_177 = 1 }
    in_q && /desktop-500-gui.sh/ { folded_179 = 1 }
    /name: FramePilot-desktop-quit-job-windows/ { art = 1 }
    END {
      exit (gw && q > gw && q_always && q_os && q_script && art && !folded_177 && !folded_179) ? 0 : 1
    }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "quit+job is not folded into #177/#179 scripts" \
  bash -c "awk '
    /desktop-quit-job-gui/ { found = 1 }
    END { exit found ? 1 : 0 }
  ' '$repo_root/packaging/scripts/macos-dmg-gui-smoke.sh' '$repo_root/packaging/scripts/desktop-500-gui.sh'"

expect_success \
  "verify.yml does not launch packaged quit+job GUI" \
  bash -c "awk '
    /desktop-quit-job-gui|macos-dmg-gui-smoke|hdiutil attach/ { found = 1 }
    END { exit found ? 1 : 0 }
  ' '$repo_root/.github/workflows/verify.yml'"

expect_success \
  "verify.yml does not launch packaged DMG GUI smoke" \
  bash -c "awk '
    /macos-dmg-gui-smoke|hdiutil attach/ { found = 1 }
    END { exit found ? 1 : 0 }
  ' '$repo_root/.github/workflows/verify.yml'"

expect_success \
  "non-Darwin macOS DMG GUI smoke host check" \
  bash tests/desktop/macos-dmg-gui-smoke-nondarwin.sh

expect_success \
  "Linux packaged desktop ≥500 GUI skip-not-pass host check" \
  bash tests/desktop/desktop-500-gui-linux.sh

expect_success \
  "Linux packaged macOS quit+job matrix skip-not-pass host check" \
  bash tests/desktop/desktop-quit-job-linux.sh

expect_success \
  "shipped desktop-quit-job Path B four-launch packaged path" \
  bash tests/desktop/desktop-quit-job-packaged-path.sh

expect_success \
  "Windows-safe python discovery prefers Scripts/python.exe" \
  bash tests/desktop/desktop-500-gui-python.sh

expect_success \
  "shipped desktop-500-gui Path B wait-done / macos exec / windows listen" \
  bash tests/desktop/desktop-500-gui-packaged-path.sh

expect_success \
  "desktop Vite index.html is Tauri custom-protocol safe" \
  bash tests/desktop/desktop-vite-tauri-html.sh

expect_success \
  "stamp-desktop-500-gui-docs dry-run no-ops without both-OS 500 JSON" \
  python3 packaging/scripts/stamp-desktop-500-gui-docs.py --dry-run

expect_success \
  "verify.yml still has no codesign or notarize" \
  bash -c "awk '
    /codesign|notariz|APPLE_CERTIFICATE|WINDOWS_CERTIFICATE|certificateThumbprint/ { found = 1 }
    END { exit found ? 1 : 0 }
  ' '$repo_root/.github/workflows/verify.yml'"

cert_repo="$tmpdir/cert-repo"
mkdir -p "$cert_repo"
git -C "$cert_repo" init -q
printf 'pfx' > "$cert_repo/secret.pfx"
git -C "$cert_repo" add secret.pfx
expect_failure \
  "tracked pfx fails the artifact check" \
  "secret.pfx" \
  bash -c "cd '$cert_repo' && bash '$repo_root/scripts/check-release-artifacts.sh'"

printf 'p12' > "$cert_repo/secret.p12"
git -C "$cert_repo" add secret.p12
expect_failure \
  "tracked p12 fails the artifact check" \
  "secret.p12" \
  bash -c "cd '$cert_repo' && bash '$repo_root/scripts/check-release-artifacts.sh'"

printf 'p8' > "$cert_repo/secret.p8"
git -C "$cert_repo" add secret.p8
expect_failure \
  "tracked p8 fails the artifact check" \
  "secret.p8" \
  bash -c "cd '$cert_repo' && bash '$repo_root/scripts/check-release-artifacts.sh'"

expect_success \
  "unsigned desktop release notes mark unsigned and link install tutorial" \
  bash -c "awk '
    /\\*\\*unsigned\\*\\*/ { unsigned = 1 }
    /Gatekeeper-clean/ { gk = 1 }
    /SmartScreen-clean/ { ss = 1 }
    /store listing/ { store = 1 }
    /desktop_install\\.md/ { en = 1 }
    /desktop_install\\.zh\\.md/ { zh = 1 }
    /Windows NSIS/ { nsis = 1 }
    /macOS DMG/ { dmg = 1 }
    /sidecar ready-line/ { sidecar = 1 }
    /120s/ { budget = 1 }
    /#191/ { sidecar_pr = 1 }
    /#195/ { ie_pr = 1 }
    /Import\\/Export/ { ie = 1 }
    /v2\\.1\\.2-desktop/ { tag = 1 }
    /Gatekeeper-clean pass|SmartScreen-clean pass|notarized Mac pass/ { claim = 1 }
    END { exit (unsigned && gk && ss && store && en && zh && nsis && dmg && sidecar && budget && sidecar_pr && ie_pr && ie && tag && !claim) ? 0 : 1 }
  ' '$repo_root/docs/desktop_unsigned_release_notes.md'"

expect_success \
  "unsigned desktop release notes Chinese counterpart matches" \
  bash -c "awk '
    /未签名/ { unsigned = 1 }
    /Gatekeeper 干净/ { gk = 1 }
    /SmartScreen 干净/ { ss = 1 }
    /商店上架/ { store = 1 }
    /desktop_install\\.md/ { en = 1 }
    /desktop_install\\.zh\\.md/ { zh = 1 }
    /sidecar ready-line/ { sidecar = 1 }
    /120 秒/ { budget = 1 }
    /#191/ { sidecar_pr = 1 }
    /#195/ { ie_pr = 1 }
    /导入\\/导出/ { ie = 1 }
    /v2\\.1\\.2-desktop/ { tag = 1 }
    END { exit (unsigned && gk && ss && store && en && zh && sidecar && budget && sidecar_pr && ie_pr && ie && tag) ? 0 : 1 }
  ' '$repo_root/docs/desktop_unsigned_release_notes.zh.md'"

expect_success \
  "desktop-release.yml publishes unsigned NSIS+DMG without signing or GUI" \
  bash -c "awk '
    /name: desktop-release/ { named = 1 }
    /workflow_dispatch:/ { dispatch = 1 }
    /workflow_run:/ { run_trigger = 1 }
    /desktop_unsigned_release_notes\\.md/ { notes = 1 }
    /v2\\.1\\.2-desktop/ { tag = 1 }
    /FramePilot 2.1.2-desktop \\(unsigned\\)/ { title = 1 }
    /6b147160e9dd46ca6eda1b9ad27f855b4d517852/ { min_sha = 1 }
    /sha_includes_import_export_fix/ { guard = 1 }
    /FramePilot-windows-nsis/ { nsis = 1 }
    /FramePilot-macos-dmg/ { dmg = 1 }
    /softprops\\/action-gh-release/ { release = 1 }
    /fail_on_unmatched_files: true/ { fail_missing = 1 }
    /contents: write/ { write_perm = 1 }
    /tauri-apps\\/tauri-action/ { action = 1 }
    /secrets\\.(WINDOWS_CERTIFICATE|APPLE_CERTIFICATE)|TAURI_SIGNING_PRIVATE_KEY/ { sign = 1 }
    /macos-dmg-gui-smoke|desktop-500-gui\\.sh|desktop-quit-job-gui|npx tauri build/ { gui = 1 }
    END {
      exit (named && dispatch && run_trigger && notes && tag && title && min_sha && guard && nsis && dmg && release && fail_missing && write_perm && !action && !sign && !gui) ? 0 : 1
    }
  ' '$repo_root/.github/workflows/desktop-release.yml'"

expect_success \
  "desktop-release.yml does not download leftover GUI-evidence artifacts" \
  bash -c "awk '
    /name: FramePilot-windows-nsis/ { nsis = 1 }
    /name: FramePilot-macos-dmg/ { dmg = 1 }
    /name: FramePilot-desktop-500-gui/ { evidence = 1 }
    /name: FramePilot-desktop-quit-job/ { evidence = 1 }
    END { exit (nsis && dmg && !evidence) ? 0 : 1 }
  ' '$repo_root/.github/workflows/desktop-release.yml'"

expect_success \
  "desktop.yml still does not publish GitHub Releases or use tauri-action" \
  bash -c "awk '
    /tauri-apps\\/tauri-action|softprops\\/action-gh-release/ { found = 1 }
    END { exit found ? 1 : 0 }
  ' '$repo_root/.github/workflows/desktop.yml'"

expect_success \
  "verify.yml does not publish unsigned desktop releases" \
  bash -c "awk '
    /desktop-release|action-gh-release|tauri-apps\\/tauri-action/ { found = 1 }
    END { exit found ? 1 : 0 }
  ' '$repo_root/.github/workflows/verify.yml'"

expect_success \
  "install tutorial prefers the unsigned GitHub Release" \
  bash -c "awk '
    /v2\\.1\\.2-desktop/ { tag = 1 }
    /github.com\\/joe-cheung-cae\\/frame-pilot\\/releases/ { rel = 1 }
    /Gatekeeper-clean/ { gk = 1 }
    /SmartScreen-clean/ { ss = 1 }
    /Publishing a GitHub Release/ { old = 1 }
    END { exit (tag && rel && gk && ss && !old) ? 0 : 1 }
  ' '$repo_root/docs/desktop_install.md'"

expect_success \
  "repository validation decision is closed" \
  bash scripts/check-validation-decision.sh

expect_success \
  "verify includes check:validation-decision" \
  bash -c "node -e '
    const p = require(\"./package.json\");
    if (!/check:validation-decision/.test(p.scripts.verify)) process.exit(1);
  '"

expect_success \
  "check:pretag still runs verify then validation-decision" \
  bash -c "node -e '
    const p = require(\"./package.json\");
    const s = p.scripts[\"check:pretag\"] || \"\";
    if (!s.includes(\"verify\") || !s.includes(\"check:validation-decision\")) process.exit(1);
  '"

echo "Release check script tests passed."

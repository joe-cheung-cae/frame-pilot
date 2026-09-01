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
  "desktop.yml smokes frozen sidecar /health after PyInstaller" \
  bash -c "awk '
    /packaging:sidecar/ { saw_build = 1 }
    /test:sidecar/ { if (saw_build) found = 1 }
    END { exit found ? 0 : 1 }
  ' '$repo_root/.github/workflows/desktop.yml'"

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

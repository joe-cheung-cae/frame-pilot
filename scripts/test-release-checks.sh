#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

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
printf '# Test Validation Notes\n' >"$validation_notes"

validation_decision="$tmpdir/validation-decision.md"
cat >"$validation_decision" <<EOF
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
cat >"$waiver_decision" <<'EOF'
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

pending_decision="$tmpdir/pending-decision.md"
cat >"$pending_decision" <<'EOF'
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
cat >"$missing_notes_decision" <<EOF
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
cat >"$incomplete_waiver_decision" <<'EOF'
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

echo "Release check script tests passed."

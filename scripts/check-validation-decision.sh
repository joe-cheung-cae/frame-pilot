#!/usr/bin/env bash
set -euo pipefail

decision_file="${1:-docs/v2_rc2_validation_decision.md}"

fail() {
  echo "Validation decision check failed: $1" >&2
  exit 1
}

clean_value() {
  printf '%s' "$1" \
    | sed -E 's/`//g; s/\*\*//g; s/[[:space:]]+$//; s/^[[:space:]]+//; s/[.]$//'
}

normalize_value() {
  clean_value "$1" | tr '[:upper:]' '[:lower:]'
}

field_value() {
  local label="$1"
  awk -v label="$label" '
    BEGIN { target = tolower(label) ":" }
    {
      line = $0
      sub(/^[[:space:]]*/, "", line)
      lower = tolower(line)
      if (index(lower, target) == 1) {
        sub(/^[^:]*:[[:space:]]*/, "", line)
        print line
        exit
      }
    }
  ' "$decision_file"
}

bullet_value() {
  local label="$1"
  awk -v label="$label" '
    BEGIN { target = "- " tolower(label) ":" }
    {
      line = $0
      sub(/^[[:space:]]*/, "", line)
      lower = tolower(line)
      if (index(lower, target) == 1) {
        sub(/^- [^:]*:[[:space:]]*/, "", line)
        print line
        exit
      }
    }
  ' "$decision_file"
}

is_unset() {
  local value
  value="$(normalize_value "$1")"
  [[ -z "$value" || "$value" == "pending" || "$value" == "tbd" || "$value" == "todo" || "$value" == "not applicable" ]]
}

[[ -f "$decision_file" ]] || fail "$decision_file is missing."

status="$(normalize_value "$(field_value "Status")")"
waiver_status="$(normalize_value "$(field_value "Waiver status")")"
validation_notes_file="$(clean_value "$(field_value "Validation notes file")")"
validation_verdict="$(clean_value "$(field_value "Validation verdict")")"
release_decision_impact="$(clean_value "$(field_value "Release decision impact")")"

if is_unset "$status"; then
  fail "$decision_file still has pending status."
fi

validation_complete=false
if ! is_unset "$validation_notes_file" \
  && ! is_unset "$validation_verdict" \
  && ! is_unset "$release_decision_impact"; then
  [[ -f "$validation_notes_file" ]] \
    || fail "validation notes file '$validation_notes_file' does not exist."
  validation_complete=true
fi

waiver_complete=false
if [[ "$waiver_status" == "waived" ]]; then
  for label in "Waiver owner" "Waiver date" "Reason" "Accepted risk" "Follow-up task"; do
    value="$(bullet_value "$label")"
    if is_unset "$value"; then
      fail "waiver is marked waived, but '$label' is missing or pending."
    fi
  done
  waiver_complete=true
fi

if [[ "$validation_complete" != true && "$waiver_complete" != true ]]; then
  fail "$decision_file must record completed validation evidence or an explicit waiver."
fi

echo "Validation decision gate is closed."

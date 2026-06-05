#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NEXT_ENV_FILE="$ROOT_DIR/apps/web/next-env.d.ts"

restore_next_env() {
  if [[ -f "$NEXT_ENV_FILE" ]]; then
    perl -0pi -e 's#/// <reference path="./\.next-e2e/types/routes\.d\.ts" />#/// <reference path="./.next/types/routes.d.ts" />#' "$NEXT_ENV_FILE"
  fi
}

trap restore_next_env EXIT

export NO_PROXY="127.0.0.1,localhost"
export no_proxy="127.0.0.1,localhost"
unset NO_COLOR

playwright test "$@"

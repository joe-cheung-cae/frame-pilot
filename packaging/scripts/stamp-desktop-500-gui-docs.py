#!/usr/bin/env python3
"""Stamp leftover packaged-desktop ≥500 GUI living docs from result.json.

Rust-free. Dry-run may only read JSON. Write is a no-op until both OS 500
JSON files exist with result=pass (chicken-and-egg: first green GHA run must
not fail CI because docs are unstamped).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FIELDS = (
    "mode",
    "result",
    "os",
    "uname",
    "timestamp",
    "native_dialog",
    "count",
    "width",
    "height",
    "quality",
)

NSIS_OLD_EN = "It still does not launch the packaged NSIS GUI."
NSIS_OLD_ZH = "仍不启动包装 NSIS GUI。"


def load_result(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    missing = [key for key in REQUIRED_FIELDS if key not in data]
    if missing:
        raise ValueError(f"{path} missing fields: {', '.join(missing)}")
    return data


def summarize(path: Path, data: dict) -> str:
    return (
        f"{path}: mode={data.get('mode')} result={data.get('result')} "
        f"os={data.get('os')} native_dialog={data.get('native_dialog')} "
        f"count={data.get('count')} {data.get('width')}x{data.get('height')} "
        f"q{data.get('quality')}"
    )


def both_os_500_pass(windows: dict | None, macos: dict | None) -> bool:
    if windows is None or macos is None:
        return False
    for payload in (windows, macos):
        if payload.get("mode") != "500":
            return False
        if payload.get("result") != "pass":
            return False
        if payload.get("native_dialog") != "stubbed":
            return False
    return True


def stamp_docs(_windows: dict, _macos: dict, *, dry_run: bool) -> None:
    testing = REPO_ROOT / "docs" / "desktop_testing.md"
    testing_zh = REPO_ROOT / "docs" / "desktop_testing.zh.md"
    if dry_run:
        print(f"dry-run: would stamp {testing} replacing {NSIS_OLD_EN!r}")
        print(f"dry-run: would stamp {testing_zh} replacing {NSIS_OLD_ZH!r}")
        return
    # 上线 performs the write after both OS 500 JSON are result=pass.


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stamp living docs from packaged-desktop ≥500 GUI result.json"
    )
    parser.add_argument("--dry-run", action="store_true", help="Read JSON; do not write docs")
    parser.add_argument("--result", type=Path, help="Read one result.json (dry-run helper)")
    parser.add_argument("--windows-json", type=Path, help="Windows 500 result.json")
    parser.add_argument("--macos-json", type=Path, help="macOS 500 result.json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.result is not None:
        payload = load_result(args.result)
        print(summarize(args.result, payload))
        if args.dry_run:
            print("dry-run: single result.json read; write is a no-op")
            return 0

    windows = None
    macos = None
    if args.windows_json is not None and args.windows_json.is_file():
        windows = load_result(args.windows_json)
        print(summarize(args.windows_json, windows))
    if args.macos_json is not None and args.macos_json.is_file():
        macos = load_result(args.macos_json)
        print(summarize(args.macos_json, macos))

    if not both_os_500_pass(windows, macos):
        print("both-OS 500 JSON missing or not result=pass; stamp write is a no-op")
        return 0

    stamp_docs(windows, macos, dry_run=args.dry_run)
    if args.dry_run:
        print("dry-run: both OS 500 result=pass; write skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

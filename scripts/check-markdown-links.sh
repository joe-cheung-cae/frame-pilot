#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
root="${1:-$repo_root}"

python3 - "$root" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
if not root.is_dir():
    print(f"Markdown link check failed: '{root}' is not a directory.", file=sys.stderr)
    raise SystemExit(1)

NAMED_FILES = ("README.md", "develop_plan.md", "implement_goals.md")
FENCE_RE = re.compile(
    r"^(?P<fence>`{3,}|~{3,})[^\n]*\n(?:.*?\n)?(?P=fence)[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
INLINE_CODE_RE = re.compile(r"`[^`]*`")
LINK_RE = re.compile(r"!?\[(?:[^\]]|\\.)*\]\(\s*([^)]+)\)")
REMOTE_PREFIXES = ("http://", "https://", "mailto:", "ftp://", "data:")


def living_markdown_files(base: Path) -> list[Path]:
    files: list[Path] = []
    for name in NAMED_FILES:
        path = base / name
        if path.is_file():
            files.append(path)
    docs = base / "docs"
    if docs.is_dir():
        files.extend(sorted(path for path in docs.rglob("*.md") if path.is_file()))
    return files


def blank_code_spans(text: str) -> str:
    def blank_match(match: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    text = FENCE_RE.sub(blank_match, text)
    return INLINE_CODE_RE.sub(blank_match, text)


def link_destination(raw: str) -> str | None:
    raw = raw.strip()
    if not raw:
        return None
    if raw.startswith("<"):
        end = raw.find(">")
        dest = raw[1:end] if end != -1 else raw[1:]
    else:
        dest = re.split(r"\s+", raw, maxsplit=1)[0]
    dest = dest.strip()
    if not dest or dest.startswith("#") or dest.lower().startswith(REMOTE_PREFIXES):
        return None
    dest = dest.split("#", 1)[0]
    return dest or None


errors: list[str] = []
scanned = living_markdown_files(root)
if not scanned:
    print(
        "Markdown link check failed: no README.md, develop_plan.md, "
        "implement_goals.md, or docs/**/*.md files found.",
        file=sys.stderr,
    )
    raise SystemExit(1)

for source in scanned:
    text = blank_code_spans(source.read_text(encoding="utf-8"))
    for match in LINK_RE.finditer(text):
        dest = link_destination(match.group(1))
        if dest is None:
            continue
        target = (source.parent / dest).resolve()
        if target.exists():
            continue
        rel_source = source.relative_to(root).as_posix()
        errors.append(f"{rel_source} -> {dest}")

if errors:
    print("Markdown link check failed: missing target file(s):", file=sys.stderr)
    for error in errors:
        print(error, file=sys.stderr)
    raise SystemExit(1)

print("Markdown links resolve.")
PY

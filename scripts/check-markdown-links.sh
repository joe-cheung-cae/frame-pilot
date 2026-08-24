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

NAMED_STEMS = ("README", "AGENTS", "develop_plan", "implement_goals")
FENCE_RE = re.compile(
    r"^(?P<fence>`{3,}|~{3,})[^\n]*\n(?:.*?\n)?(?P=fence)[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
INLINE_CODE_RE = re.compile(r"`[^`]*`")
LINK_RE = re.compile(r"!?\[(?:[^\]]|\\.)*\]\(\s*([^)]+)\)")
REMOTE_PREFIXES = ("http://", "https://", "mailto:", "ftp://", "data:")
STALE_FILES = ("docs/plans/2026-08-18-desktop-packaging-review.md",)


def living_markdown_files(base: Path) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for stem in NAMED_STEMS:
        for name in (f"{stem}.md", f"{stem}.zh.md"):
            path = base / name
            if path.is_file():
                resolved = path.resolve()
                files.append(path)
                seen.add(resolved)
    docs = base / "docs"
    if docs.is_dir():
        for path in sorted(p for p in docs.rglob("*.md") if p.is_file()):
            resolved = path.resolve()
            if resolved not in seen:
                files.append(path)
                seen.add(resolved)
    return files


def counterpart_path(path: Path) -> Path:
    name = path.name
    if name.endswith(".zh.md"):
        return path.with_name(name[: -len(".zh.md")] + ".md")
    return path.with_name(path.stem + ".zh.md")


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


def resolved_markdown_targets(source: Path, text: str) -> list[Path]:
    targets: list[Path] = []
    for match in LINK_RE.finditer(blank_code_spans(text)):
        dest = link_destination(match.group(1))
        if dest is None:
            continue
        targets.append((source.parent / dest).resolve())
    return targets


errors: list[str] = []

handoff = root / "docs" / "handoff"
if handoff.exists():
    errors.append("stale handoff path present: docs/handoff")
    if handoff.is_dir():
        for path in sorted(p for p in handoff.rglob("*") if p.is_file()):
            errors.append(f"stale handoff path present: {path.relative_to(root).as_posix()}")
    elif handoff.is_file():
        errors.append("stale handoff path present: docs/handoff")

for rel in STALE_FILES:
    stale = root / rel
    if stale.exists():
        errors.append(f"stale plan path present: {rel}")

scanned = living_markdown_files(root)
if not scanned:
    print(
        "Markdown link check failed: no README.md, AGENTS.md, develop_plan.md, "
        "implement_goals.md, or docs/**/*.md files found.",
        file=sys.stderr,
    )
    raise SystemExit(1)

for source in scanned:
    rel_source = source.relative_to(root).as_posix()
    text = source.read_text(encoding="utf-8")
    if not text.strip():
        errors.append(f"empty living page: {rel_source}")
        continue
    counterpart = counterpart_path(source)
    if not counterpart.is_file():
        kind = "Chinese" if source.name.endswith(".zh.md") else "English"
        other = "English" if kind == "Chinese" else "Chinese"
        errors.append(
            f"missing {other} counterpart for {rel_source}: "
            f"{counterpart.relative_to(root).as_posix()}"
        )
    elif not counterpart.read_text(encoding="utf-8").strip():
        errors.append(
            f"empty living page: {counterpart.relative_to(root).as_posix()}"
        )
    else:
        targets = resolved_markdown_targets(source, text)
        if counterpart.resolve() not in targets:
            errors.append(
                f"missing counterpart link: {rel_source} -> "
                f"{counterpart.relative_to(root).as_posix()}"
            )
    for dest in LINK_RE.finditer(blank_code_spans(text)):
        raw = link_destination(dest.group(1))
        if raw is None:
            continue
        target = (source.parent / raw).resolve()
        if target.exists():
            continue
        errors.append(f"{rel_source} -> {raw}")

if errors:
    print("Markdown link check failed:", file=sys.stderr)
    for error in errors:
        print(error, file=sys.stderr)
    raise SystemExit(1)

print("Markdown links resolve.")
PY

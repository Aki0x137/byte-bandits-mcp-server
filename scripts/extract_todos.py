#!/usr/bin/env python3
"""Scan repo for TODO/FIXME tags and emit JSON for tracking."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Iterable

TAG_PATTERN = re.compile(r"^[ \t]*# *(TODO|FIXME)\(([A-Za-z0-9_-]+)\): *(.*)$")

IGNORED_DIRS = {".git", "__pycache__", ".venv", "dist", "build"}
CODE_EXT = {".py", ".md", ".toml", ".txt", ".yml", ".yaml"}


def iter_files(root: Path) -> Iterable[Path]:
    for path, dirs, files in os.walk(root):
        # prune
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for f in files:
            p = Path(path) / f
            if p.suffix.lower() in CODE_EXT:
                yield p


def parse_file(path: Path):
    results = []
    try:
        for lineno, line in enumerate(path.read_text(errors="ignore").splitlines(), start=1):
            m = TAG_PATTERN.match(line)
            if m:
                tag, owner, text = m.groups()
                results.append(
                    {
                        "file": str(path),
                        "line": lineno,
                        "type": tag,
                        "owner": owner,
                        "text": text.strip(),
                    }
                )
    except Exception as e:  # noqa: BLE001
        results.append({"file": str(path), "error": str(e)})
    return results


def main():
    root = Path(__file__).resolve().parent.parent
    findings = []
    for f in iter_files(root):
        findings.extend(parse_file(f))
    print(json.dumps({"count": len(findings), "items": findings}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()

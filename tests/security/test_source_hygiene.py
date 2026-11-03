"""Trojan-Source guard: project sources must not contain hidden or bidi characters.

Attack strings in tests must be written as escape sequences (e.g. "\\u200b").
"""

from __future__ import annotations

import pathlib

from bera.text import detect_suspicious

ROOT = pathlib.Path(__file__).resolve().parents[2]
GLOBS = [
    "src/**/*.py",
    "tests/**/*.py",
    "scripts/**/*.py",
    "frontend/src/**/*.ts",
    "frontend/src/**/*.tsx",
    "docs/**/*.md",
    "*.md",
]


def test_no_hidden_characters_in_sources() -> None:
    offenders = []
    for pattern in GLOBS:
        for path in ROOT.glob(pattern):
            if "node_modules" in path.parts:
                continue
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                flags = detect_suspicious(line).flags - {"mixed_script"}
                if flags:
                    offenders.append(f"{path.relative_to(ROOT)}:{n} {sorted(flags)}")
    assert offenders == []

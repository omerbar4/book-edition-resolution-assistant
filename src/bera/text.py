"""Documented text normalization and suspicious-Unicode detection.

Rules (see docs/EVIDENCE_SPEC.md):
- Raw text is ALWAYS preserved. Normalized forms are used only for matching.
- `norm_text`: NFKC -> remove format/control characters -> casefold -> map a fixed
  punctuation set to spaces -> collapse whitespace -> strip.
- `detect_suspicious` reports characters that are commonly used to hide or reorder text
  (bidi controls, zero-width characters, Unicode tag characters, C0/C1 controls) and
  tokens that mix scripts (a common homoglyph trick). Detection never deletes evidence.
- `visible_escape` renders hidden characters as visible markers like ⟦U+200B⟧ so neither
  a human reviewer nor a model can be shown text that hides content.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from enum import StrEnum

BIDI_CONTROLS = frozenset([0x061C, 0x200E, 0x200F, *range(0x202A, 0x202F), *range(0x2066, 0x206A)])
ZERO_WIDTH = frozenset([0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x180E, 0x00AD])
TAG_RANGE = range(0xE0000, 0xE0080)

# Punctuation mapped to a space before comparison. Apostrophes are removed outright so
# "Hitchhiker's" == "Hitchhikers".
_PUNCT_TO_SPACE = frozenset(',.;:!?()[]{}"/\\|-_–—…·•&+*#@<>=~^`')
_PUNCT_DROP = frozenset("'’‘ʼ")


class UnicodeFlag(StrEnum):
    BIDI_CONTROL = "bidi_control"
    ZERO_WIDTH = "zero_width"
    TAG_CHARACTER = "tag_character"
    CONTROL_CHARACTER = "control_character"
    MIXED_SCRIPT = "mixed_script"


@dataclass(frozen=True)
class SuspiciousReport:
    flags: frozenset[UnicodeFlag]
    codepoints: tuple[str, ...]  # e.g. ("U+200B",), capped

    @property
    def suspicious(self) -> bool:
        return bool(self.flags)


def _is_hidden(cp: int) -> UnicodeFlag | None:
    if cp in BIDI_CONTROLS:
        return UnicodeFlag.BIDI_CONTROL
    if cp in ZERO_WIDTH:
        return UnicodeFlag.ZERO_WIDTH
    if cp in TAG_RANGE:
        return UnicodeFlag.TAG_CHARACTER
    cat = unicodedata.category(chr(cp))
    if cat == "Cc" and chr(cp) not in "\t\n\r":
        return UnicodeFlag.CONTROL_CHARACTER
    if cat == "Cf":
        return UnicodeFlag.ZERO_WIDTH
    return None


def _script_of(ch: str) -> str | None:
    """Coarse script bucket from the Unicode character name (stdlib has no Script prop)."""
    if not ch.isalpha():
        return None
    name = unicodedata.name(ch, "")
    for script in ("LATIN", "CYRILLIC", "GREEK", "ARMENIAN", "CHEROKEE"):
        if name.startswith(script):
            return script
    return "OTHER"


_CONFUSABLE_SCRIPTS = frozenset({"LATIN", "CYRILLIC", "GREEK", "ARMENIAN", "CHEROKEE"})


def detect_suspicious(text: str, max_codepoints: int = 16) -> SuspiciousReport:
    flags: set[UnicodeFlag] = set()
    cps: list[str] = []
    for ch in text:
        f = _is_hidden(ord(ch))
        if f is not None:
            flags.add(f)
            if len(cps) < max_codepoints:
                cps.append(f"U+{ord(ch):04X}")
    for token in text.split():
        scripts = {s for s in (_script_of(c) for c in token) if s is not None}
        if len(scripts & _CONFUSABLE_SCRIPTS) > 1:
            flags.add(UnicodeFlag.MIXED_SCRIPT)
            break
    return SuspiciousReport(frozenset(flags), tuple(cps))


def visible_escape(text: str) -> str:
    """Replace hidden characters with visible ⟦U+XXXX⟧ markers. Visible text is unchanged."""
    out = []
    for ch in text:
        if _is_hidden(ord(ch)) is not None:
            out.append(f"⟦U+{ord(ch):04X}⟧")
        else:
            out.append(ch)
    return "".join(out)


def norm_text(text: str | None) -> str:
    if text is None:
        return ""
    t = unicodedata.normalize("NFKC", text)
    t = "".join(ch for ch in t if _is_hidden(ord(ch)) is None)
    t = t.casefold()
    chars = []
    for ch in t:
        if ch in _PUNCT_DROP:
            continue
        chars.append(" " if ch in _PUNCT_TO_SPACE else ch)
    return " ".join("".join(chars).split())


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def norm_person(name: str | None) -> str:
    """Author-name key: accents stripped, 'Last, First' reordered, initials kept."""
    if not name:
        return ""
    n = name
    if "," in n:
        last, _, first = n.partition(",")
        n = f"{first} {last}"
    return strip_accents(norm_text(n))


_LEADING_ARTICLES = frozenset(
    "the a an le la les l el los las il lo gli der die das ein eine un une".split()
)


def fold_title(text: str | None) -> str:
    """Title key for matching across variants: norm_text + accent folding + leading-article
    removal. Used for selection/exclusion matching, never for display."""
    t = strip_accents(norm_text(text))
    words = t.split()
    while len(words) > 1 and words[0] in _LEADING_ARTICLES:
        words = words[1:]
    return " ".join(words)

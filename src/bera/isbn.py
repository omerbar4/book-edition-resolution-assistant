"""ISBN-10 / ISBN-13 normalization, checksum validation, conversion and repair hypotheses.

Facts encoded here:
- ISBN-10 check digit: weights 10..1, sum % 11 == 0; check character may be 'X' (=10).
  It detects every single-digit error and every transposition of two digits.
- ISBN-13 check digit: alternating weights 1,3; sum % 10 == 0. It detects every
  single-digit error but NOT adjacent transpositions of digits that differ by 5
  (e.g. ...05... vs ...50...), because 3a+b and a+3b differ by 2(a-b), which is 0 mod 10.
- Only 978-prefixed ISBN-13s have an ISBN-10 equivalent; 979-prefixed do not.

A checksum-valid ISBN is NOT a guarantee of a unique catalog mapping.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum

# Separators people commonly type or that OCR/barcode tools emit.
_SEPARATORS = frozenset(" -‐‑‒–—−._/\t")


class IsbnStatus(StrEnum):
    VALID_10 = "valid_isbn10"
    VALID_13 = "valid_isbn13"
    BAD_CHECKSUM = "bad_checksum"
    BAD_FORMAT = "bad_format"


@dataclass(frozen=True)
class IsbnParse:
    raw: str
    compact: str  # digits (and possibly trailing X) after separator removal
    status: IsbnStatus
    isbn13: str | None  # canonical ISBN-13 when valid
    isbn10: str | None  # ISBN-10 equivalent when one exists

    @property
    def valid(self) -> bool:
        return self.status in (IsbnStatus.VALID_10, IsbnStatus.VALID_13)


def compact(raw: str) -> str:
    """NFKC-normalize (folds full-width digits), drop separators, uppercase x."""
    text = unicodedata.normalize("NFKC", raw).strip()
    if text.upper().startswith("ISBN"):
        text = re.sub(r"^[:\s-]+", "", text[4:])
    out = []
    for ch in text:
        if ch in _SEPARATORS:
            continue
        out.append("X" if ch == "x" else ch)
    return "".join(out)


def isbn10_check_char(body9: str) -> str:
    total = sum((10 - i) * int(d) for i, d in enumerate(body9))
    check = (11 - total % 11) % 11
    return "X" if check == 10 else str(check)


def isbn13_check_digit(body12: str) -> str:
    total = sum((1 if i % 2 == 0 else 3) * int(d) for i, d in enumerate(body12))
    return str((10 - total % 10) % 10)


def is_valid_isbn10(s: str) -> bool:
    if len(s) != 10 or not s[:9].isdigit() or not (s[9].isdigit() or s[9] == "X"):
        return False
    return isbn10_check_char(s[:9]) == s[9]


def is_valid_isbn13(s: str) -> bool:
    if len(s) != 13 or not s.isdigit() or not s.isascii():
        return False
    return isbn13_check_digit(s[:12]) == s[12]


def isbn10_to_13(s: str) -> str:
    body = "978" + s[:9]
    return body + isbn13_check_digit(body)


def isbn13_to_10(s: str) -> str | None:
    if not s.startswith("978"):
        return None
    body = s[3:12]
    return body + isbn10_check_char(body)


def parse(raw: str) -> IsbnParse:
    c = compact(raw)
    if not c.isascii():
        return IsbnParse(raw, c, IsbnStatus.BAD_FORMAT, None, None)
    if len(c) == 10 and c[:9].isdigit() and (c[9].isdigit() or c[9] == "X"):
        if is_valid_isbn10(c):
            return IsbnParse(raw, c, IsbnStatus.VALID_10, isbn10_to_13(c), c)
        return IsbnParse(raw, c, IsbnStatus.BAD_CHECKSUM, None, None)
    if len(c) == 13 and c.isdigit():
        if is_valid_isbn13(c):
            return IsbnParse(raw, c, IsbnStatus.VALID_13, c, isbn13_to_10(c))
        return IsbnParse(raw, c, IsbnStatus.BAD_CHECKSUM, None, None)
    return IsbnParse(raw, c, IsbnStatus.BAD_FORMAT, None, None)


def repair_hypotheses(c: str, limit: int = 200) -> list[str]:
    """Checksum-valid ISBN-13s reachable by one substituted digit or one adjacent swap.

    These are HYPOTHESES for a damaged or mistyped ISBN, never exact matches.
    Returned as canonical ISBN-13 strings, deduplicated, in deterministic order.
    """
    out: list[str] = []
    seen: set[str] = set()

    def add(candidate: str) -> None:
        p = parse(candidate)
        if p.valid and p.isbn13 is not None and p.isbn13 not in seen:
            seen.add(p.isbn13)
            out.append(p.isbn13)

    if len(c) not in (10, 13):
        return out
    alphabet10 = "0123456789"
    for i in range(len(c)):
        allowed = alphabet10 + ("X" if len(c) == 10 and i == 9 else "")
        for d in allowed:
            if d != c[i]:
                add(c[:i] + d + c[i + 1 :])
    for i in range(len(c) - 1):
        if c[i] != c[i + 1]:
            add(c[:i] + c[i + 1] + c[i] + c[i + 2 :])
    return out[:limit]

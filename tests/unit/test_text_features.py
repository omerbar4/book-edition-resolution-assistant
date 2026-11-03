from __future__ import annotations

from bera.features import content_kind, edition_ordinal, parse_format, parse_language
from bera.models import PhysicalFormat
from bera.text import UnicodeFlag, detect_suspicious, norm_person, norm_text, visible_escape


def test_norm_text() -> None:
    assert norm_text("  The Lantern-Keeper’s   DAUGHTER! ") == "the lantern keepers daughter"
    assert norm_text("ﬁeld") == "field"  # NFKC ligature fold
    assert norm_text(None) == ""


def test_norm_person_reorders_and_strips_accents() -> None:
    assert norm_person("Natarajan, Priya") == "priya natarajan"
    assert norm_person("Inés Duarte-Lobo") == "ines duarte lobo"


def test_detects_hidden_and_mixed_script() -> None:
    assert UnicodeFlag.ZERO_WIDTH in detect_suspicious("Lan\u200btern").flags
    assert UnicodeFlag.BIDI_CONTROL in detect_suspicious("abc\u202edcb").flags
    assert UnicodeFlag.TAG_CHARACTER in detect_suspicious("x\U000e0041").flags
    assert UnicodeFlag.MIXED_SCRIPT in detect_suspicious("M\u0430ra").flags
    assert not detect_suspicious("Inés Duarte-Lobo").suspicious
    assert not detect_suspicious("Москв\u0430").suspicious  # single non-Latin script is fine


def test_visible_escape_preserves_visible_text() -> None:
    assert visible_escape("Lan\u200btern") == "Lan⟦U+200B⟧tern"
    assert visible_escape("plain") == "plain"


def test_parse_format_language() -> None:
    assert parse_format("Hardback") is PhysicalFormat.HARDCOVER
    assert parse_format("mass-market paperback") is PhysicalFormat.MASS_MARKET_PAPERBACK
    assert parse_format("signed first printing") is PhysicalFormat.UNKNOWN
    assert parse_language("Español") == "spa"
    assert parse_language("klingon") is None


def test_edition_ordinal_and_kind() -> None:
    assert edition_ordinal("2nd edition") == 2
    assert edition_ordinal("Third Edition") == 3
    assert edition_ordinal("10th anniversary edition") is None
    assert content_kind("Study Guide: The Lantern Keeper's Daughter") == "study_guide"
    assert content_kind("The Lantern Keeper Trilogy Box Set") == "box_set"
    assert content_kind("The Lantern Keeper's Daughter") == "standard"

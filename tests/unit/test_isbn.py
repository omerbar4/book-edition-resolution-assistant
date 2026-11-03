from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from bera import isbn

# Public example from Open Library's Books API docs: /isbn/9780140328721
OL_EXAMPLE_13 = "9780140328721"
OL_EXAMPLE_10 = "0140328726"


def test_valid_isbn13_and_conversion() -> None:
    p = isbn.parse(OL_EXAMPLE_13)
    assert p.status is isbn.IsbnStatus.VALID_13
    assert p.isbn10 == OL_EXAMPLE_10


def test_valid_isbn10_converts_to_13() -> None:
    p = isbn.parse(OL_EXAMPLE_10)
    assert p.status is isbn.IsbnStatus.VALID_10
    assert p.isbn13 == OL_EXAMPLE_13


def test_x_check_digit_and_lowercase() -> None:
    assert isbn.parse("080442957X").valid
    assert isbn.parse("080442957x").valid
    assert isbn.parse("0-8044-2957-X").isbn13 == "9780804429573"


def test_separators_prefix_and_fullwidth_digits() -> None:
    assert isbn.parse("ISBN: 978-0-14-032872-1").isbn13 == OL_EXAMPLE_13
    assert isbn.parse("978 0 14 032872 1").isbn13 == OL_EXAMPLE_13
    assert isbn.parse("９７８０１４０３２８７２１").isbn13 == OL_EXAMPLE_13  # full-width digits


def test_bad_checksum_and_bad_format() -> None:
    assert isbn.parse("9780140328722").status is isbn.IsbnStatus.BAD_CHECKSUM
    assert isbn.parse("0140328727").status is isbn.IsbnStatus.BAD_CHECKSUM
    assert isbn.parse("12345").status is isbn.IsbnStatus.BAD_FORMAT
    assert isbn.parse("97801403287X1").status is isbn.IsbnStatus.BAD_FORMAT
    # Arabic-Indic digits are not folded by NFKC; we reject rather than guess.
    assert isbn.parse("٩٧٨٠١٤٠٣٢٨٧٢١").status is isbn.IsbnStatus.BAD_FORMAT


def test_979_has_no_isbn10() -> None:
    body = "979100000001"
    code = body + isbn.isbn13_check_digit(body)
    p = isbn.parse(code)
    assert p.valid and p.isbn10 is None


body9 = st.text(alphabet="0123456789", min_size=9, max_size=9)
body12 = st.text(alphabet="0123456789", min_size=12, max_size=12)


@given(body9)
def test_isbn10_detects_every_single_substitution(b: str) -> None:
    code = b + isbn.isbn10_check_char(b)
    assert isbn.is_valid_isbn10(code)
    for i in range(10):
        alphabet = "0123456789" + ("X" if i == 9 else "")
        for d in alphabet:
            if d != code[i]:
                assert not isbn.is_valid_isbn10(code[:i] + d + code[i + 1 :])


@given(body9)
def test_isbn10_detects_every_adjacent_transposition(b: str) -> None:
    code = b + isbn.isbn10_check_char(b)
    for i in range(9):
        if code[i] != code[i + 1]:
            swapped = code[:i] + code[i + 1] + code[i] + code[i + 2 :]
            assert not isbn.is_valid_isbn10(swapped)


@given(body12)
def test_isbn13_detects_every_single_substitution(b: str) -> None:
    code = b + isbn.isbn13_check_digit(b)
    for i in range(13):
        for d in "0123456789":
            if d != code[i]:
                assert not isbn.is_valid_isbn13(code[:i] + d + code[i + 1 :])


def test_isbn13_documented_blind_spot_transposition_diff_5() -> None:
    body = "978000000050"  # adjacent '0','5' at positions 10,11 differ by 5
    code = body + isbn.isbn13_check_digit(body)
    swapped = code[:10] + code[11] + code[10] + code[12:]
    assert swapped != code
    assert isbn.is_valid_isbn13(swapped)  # checksum cannot catch this; documented limitation


@given(body12)
def test_10_13_round_trip(b: str) -> None:
    body = "978" + b[:9]
    code = body + isbn.isbn13_check_digit(body)
    ten = isbn.isbn13_to_10(code)
    assert ten is not None and isbn.is_valid_isbn10(ten)
    assert isbn.isbn10_to_13(ten) == code


def test_repair_hypotheses_recover_single_digit_error() -> None:
    damaged = "9780140328731"  # one digit changed
    assert OL_EXAMPLE_13 in isbn.repair_hypotheses(damaged)


def test_repair_hypotheses_recover_transposition() -> None:
    damaged = "0143028726"  # adjacent swap of OL_EXAMPLE_10
    assert OL_EXAMPLE_13 in isbn.repair_hypotheses(damaged)

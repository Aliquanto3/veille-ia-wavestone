"""Tests pour veille_ia.utils."""

from veille_ia.utils import format_date_range


def test_format_valid_dates():
    display, start, end = format_date_range("2025-12-19", "2026-01-05")
    assert "19/12" in display
    assert "05/01" in display
    assert start == "19-12"
    assert end == "05-01"


def test_format_invalid_dates():
    display, start, end = format_date_range("bad", "dates")
    assert "bad" in display
    assert "dates" in display

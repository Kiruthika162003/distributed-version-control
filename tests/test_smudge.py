from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.smudge import EndingFilter

UNIX = b"line one\nline two\n"
WINDOWS = b"line one\r\nline two\r\n"
MIXED = b"line one\r\nline two\n"
PNG = b"\x89PNG\x00\r\n"


class TestClean:
    def test_both_dialects_clean_to_one_truth(self):
        for style in ("lf", "crlf"):
            filt = EndingFilter(desk_style=style)
            cleaned, _ = filt.clean("a.txt", WINDOWS)
            assert cleaned == UNIX

    def test_mixed_endings_are_named_as_the_disease(self):
        filt = EndingFilter(desk_style="lf")
        _, receipt = filt.clean("a.txt", MIXED)
        assert "mixed endings (1 crlf, 1 lf)" in receipt
        assert "exists to cure" in receipt

    def test_binaries_are_exempt_by_sniff(self):
        filt = EndingFilter(desk_style="crlf")
        kept, receipt = filt.clean("logo.png", PNG)
        assert kept == PNG
        assert "interesting corruption" in receipt


class TestSmudge:
    def test_the_crlf_desk_gets_dressed_text(self):
        filt = EndingFilter(desk_style="crlf")
        dressed, _ = filt.smudge("a.txt", UNIX)
        assert dressed == WINDOWS

    def test_the_lf_desk_changes_nothing(self):
        filt = EndingFilter(desk_style="lf")
        kept, receipt = filt.smudge("a.txt", UNIX)
        assert kept == UNIX
        assert "speaks lf already" in receipt

    def test_the_round_trip_is_an_inverse(self):
        filt = EndingFilter(desk_style="crlf")
        cleaned, _ = filt.clean("a.txt", WINDOWS)
        dressed, _ = filt.smudge("a.txt", cleaned)
        recleaned, _ = filt.clean("a.txt", dressed)
        assert recleaned == cleaned

    def test_the_style_menu_is_closed(self):
        with pytest.raises(Invalid):
            EndingFilter(desk_style="cr")

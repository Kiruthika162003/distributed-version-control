from __future__ import annotations

import pytest

from keel.attributes import AttributesFile
from keel.errors import Invalid

RULES = AttributesFile.parse(
    "# endings and drivers\n"
    "* eol=lf\n"
    "*.bat eol=crlf\n"
    "*.png binary\n"
    "CHANGELOG merge=union\n"
    "secrets/ export-ignore\n"
)


class TestParsing:
    def test_unknown_attributes_are_refused_with_the_four(
        self,
    ):
        with pytest.raises(Invalid) as caught:
            AttributesFile.parse("*.txt sparkle")
        message = str(caught.value)
        assert "sparkle is not an attribute" in message
        assert "eol, binary, export-ignore, merge" in (
            message
        )

    def test_binary_takes_no_value(self):
        with pytest.raises(Invalid) as caught:
            AttributesFile.parse("*.png binary=yes")
        assert "two features wearing one name" in str(
            caught.value
        )

    def test_eol_accepts_only_the_two_endings(self):
        with pytest.raises(Invalid):
            AttributesFile.parse("*.txt eol=cr")

    def test_merge_needs_a_driver(self):
        with pytest.raises(Invalid):
            AttributesFile.parse("CHANGELOG merge=")

    def test_a_bare_pattern_declares_nothing(self):
        with pytest.raises(Invalid):
            AttributesFile.parse("*.txt")


class TestResolution:
    def test_later_rules_win_per_key_not_per_line(self):
        assert RULES.lookup("script.bat")["eol"] == "crlf"
        assert RULES.lookup("notes.txt")["eol"] == "lf"
        assert (
            RULES.lookup("CHANGELOG")["merge"] == "union"
        )
        assert RULES.lookup("CHANGELOG")["eol"] == "lf"

    def test_binary_and_driver_helpers_read_the_table(
        self,
    ):
        assert RULES.is_binary("logo.png")
        assert not RULES.is_binary("notes.txt")
        assert RULES.merge_driver("CHANGELOG") == "union"
        assert RULES.merge_driver("notes.txt") == "diff3"


class TestExplain:
    def test_the_decider_line_is_named(self):
        assert RULES.explain("script.bat", "eol") == (
            "script.bat: eol=crlf, decided by line 3 "
            "(*.bat)"
        )

    def test_unset_is_said_plainly(self):
        assert RULES.explain("notes.txt", "merge") == (
            "notes.txt: merge unset; the default is the "
            "absence, not a hidden rule"
        )


class TestExport:
    def test_held_back_paths_are_split_out(self):
        shipped, held_back = RULES.export_paths(
            [
                "notes.txt",
                "secrets/key.pem",
                "logo.png",
            ]
        )
        assert shipped == ["logo.png", "notes.txt"]
        assert held_back == ["secrets/key.pem"]

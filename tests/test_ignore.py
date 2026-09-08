from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.ignore import IgnoreFile

RULES = """
# build junk
*.log
build/
secrets.env
!shipping.log
"""


def ignores() -> IgnoreFile:
    return IgnoreFile.parse(RULES)


class TestTheGrammar:
    def test_wildcards_match_within_a_segment(self):
        chosen = ignores()
        assert chosen.is_ignored("debug.log")
        assert chosen.is_ignored("deep/nested/trace.log")
        assert not chosen.is_ignored("logbook.txt")

    def test_directory_patterns_swallow_everything_beneath(self):
        chosen = ignores()
        assert chosen.is_ignored("build/out.bin")
        assert chosen.is_ignored("sub/build/deep/artifact")
        assert not chosen.is_ignored("build")

    def test_bare_names_match_anywhere(self):
        chosen = ignores()
        assert chosen.is_ignored("secrets.env")
        assert chosen.is_ignored("config/secrets.env")

    def test_comments_and_blanks_vanish(self):
        assert len(ignores().rules) == 4

    def test_a_bare_bang_negates_nothing(self):
        with pytest.raises(Invalid):
            IgnoreFile.parse("!")


class TestNegation:
    def test_later_rules_win_the_argument(self):
        chosen = ignores()
        assert not chosen.is_ignored("shipping.log")
        assert chosen.is_ignored("other.log")

    def test_the_verdict_names_the_deciding_rule(self):
        chosen = ignores()
        assert chosen.explain("shipping.log") == (
            "shipping.log: tracked; re-admitted by line 6 "
            "(!shipping.log)"
        )
        assert chosen.explain("debug.log") == (
            "debug.log: ignored; ignored by line 3 (*.log)"
        )

    def test_the_unmatched_path_is_tracked_by_default(self):
        assert "no rule matched" in ignores().explain("src/main.py")

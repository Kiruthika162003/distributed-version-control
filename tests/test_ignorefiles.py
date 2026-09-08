from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.ignorefiles import IgnoreRules

RULES = IgnoreRules.parse(
    "# build outputs\n"
    "*.log\n"
    "build/\n"
    "secrets/*.key\n"
    "!keep.log\n"
)


class TestMatching:
    def test_basename_patterns_match_anywhere(self):
        assert RULES.is_ignored("debug.log")
        assert RULES.is_ignored("deep/nested/trace.log")

    def test_slashed_patterns_anchor_to_the_root(self):
        assert RULES.is_ignored("secrets/api.key")
        assert not RULES.is_ignored(
            "vendor/secrets/api.key"
        )

    def test_directory_rules_cover_everything_under(self):
        assert RULES.is_ignored("build/out.bin")
        assert RULES.is_ignored("build/deep/more.txt")
        assert not RULES.is_ignored("rebuild/out.bin")

    def test_negation_reincludes_and_order_wins(self):
        assert not RULES.is_ignored("keep.log")

    def test_the_bare_exclamation_is_refused(self):
        with pytest.raises(Invalid):
            IgnoreRules.parse("!")


class TestExplain:
    def test_the_decider_and_the_overridden_are_named(self):
        story = RULES.explain("keep.log")
        assert "re-included by line 5 (keep.log)" in story
        assert "overrides line 2 (*.log)" in story
        assert "the last matching rule wins" in story

    def test_the_free_file_is_stated(self):
        assert "arrives freely" in RULES.explain("main.py")


class TestTheGate:
    def test_arrivals_are_gated_and_named(self):
        admitted, refused = RULES.gate_arrivals(
            {
                "main.py": b"code",
                "debug.log": b"noise",
                "build/out.bin": b"artifact",
            },
            tracked=set(),
        )
        assert sorted(admitted) == ["main.py"]
        assert refused == ["build/out.bin", "debug.log"]

    def test_residents_are_never_evicted(self):
        admitted, refused = RULES.gate_arrivals(
            {"legacy.log": b"already tracked"},
            tracked={"legacy.log"},
        )
        assert "legacy.log" in admitted
        assert refused == []

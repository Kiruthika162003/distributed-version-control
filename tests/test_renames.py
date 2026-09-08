from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.renames import (
    detect_renames,
    line_similarity,
    narrate,
)


class TestSimilarity:
    def test_identical_content_scores_one(self):
        assert line_similarity(b"a\nb\nc", b"a\nb\nc") == 1.0

    def test_disjoint_content_scores_zero(self):
        assert line_similarity(b"a\nb", b"x\ny") == 0.0

    def test_the_score_is_shared_over_total(self):
        score = line_similarity(b"a\nb\nc\nd", b"a\nb\nx\ny")
        assert score == pytest.approx(0.5)


class TestDetection:
    def test_the_exact_pass_is_certain_and_free(self):
        renames, removed, added = detect_renames(
            removed={"old/name.py": b"same bytes"},
            added={"new/name.py": b"same bytes"},
        )
        assert len(renames) == 1
        assert renames[0].similarity == 1.0
        assert renames[0].describe() == (
            "old/name.py -> new/name.py (exact)"
        )
        assert removed == [] and added == []

    def test_the_similarity_pass_pairs_the_edited_move(self):
        renames, _, _ = detect_renames(
            removed={"util.py": b"a\nb\nc\nd\ne"},
            added={"helpers.py": b"a\nb\nc\nd\nCHANGED"},
        )
        assert len(renames) == 1
        assert 0.7 < renames[0].similarity < 1.0

    def test_below_the_floor_stays_a_delete_and_an_add(self):
        renames, removed, added = detect_renames(
            removed={"one.py": b"a\nb"},
            added={"two.py": b"x\ny\nz"},
        )
        assert renames == []
        assert removed == ["one.py"]
        assert added == ["two.py"]

    def test_greedy_pairing_takes_the_best_match_first(self):
        renames, _, added = detect_renames(
            removed={"core.py": b"a\nb\nc\nd"},
            added={
                "near.py": b"a\nb\nc\nx",
                "far.py": b"a\nb\nx\ny",
            },
        )
        assert len(renames) == 1
        assert renames[0].new_path == "near.py"
        assert added == ["far.py"]

    def test_the_floor_is_a_fraction(self):
        with pytest.raises(Invalid):
            detect_renames({}, {}, floor=0.0)


class TestNarration:
    def test_the_story_shows_score_not_just_verdict(self):
        renames, removed, added = detect_renames(
            removed={
                "moved.py": b"a\nb\nc\nd",
                "gone.py": b"deleted",
            },
            added={
                "moved2.py": b"a\nb\nc\nz",
                "born.py": b"created",
            },
        )
        story = narrate(renames, removed, added)
        assert story.startswith(
            "1 rename(s), 1 removal(s), 1 addition(s)"
        )
        assert "renamed moved.py -> moved2.py (75% similar)" in (
            story
        )
        assert "removed gone.py" in story
        assert "added born.py" in story

    def test_nothing_narrates_as_nothing(self):
        assert narrate([], [], []) == "no changes to narrate"

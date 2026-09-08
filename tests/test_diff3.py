from __future__ import annotations

from keel.diff3 import (
    conflict_count,
    is_clean,
    merge3,
    render,
)

BASE = "one\ntwo\nthree\nfour"


def merged_text(base: str, left: str, right: str) -> str:
    return render(merge3(base, left, right))


class TestCleanMerges:
    def test_untouched_text_passes_through(self):
        regions = merge3(BASE, BASE, BASE)
        assert is_clean(regions)
        assert render(regions) == BASE

    def test_one_side_moving_wins_without_ceremony(self):
        left = "one\nTWO\nthree\nfour"
        assert merged_text(BASE, left, BASE) == left
        assert merged_text(BASE, BASE, left) == left

    def test_edits_on_different_lines_both_land(self):
        left = "ONE\ntwo\nthree\nfour"
        right = "one\ntwo\nthree\nFOUR"
        assert merged_text(BASE, left, right) == (
            "ONE\ntwo\nthree\nFOUR"
        )

    def test_identical_moves_merge_without_conflict(self):
        both = "one\nSAME\nthree\nfour"
        regions = merge3(BASE, both, both)
        assert is_clean(regions)
        assert render(regions) == both


class TestConflicts:
    def test_different_moves_on_one_line_stay_loud(self):
        left = "one\nLEFT\nthree\nfour"
        right = "one\nRIGHT\nthree\nfour"
        regions = merge3(BASE, left, right)
        assert conflict_count(regions) == 1
        assert not is_clean(regions)

    def test_the_marker_shows_the_question_not_just_answers(self):
        left = "one\nLEFT\nthree\nfour"
        right = "one\nRIGHT\nthree\nfour"
        text = merged_text(BASE, left, right)
        assert "<<<<<<< ours" in text
        assert "||||||| base" in text
        assert "two" in text
        assert "=======" in text
        assert ">>>>>>> theirs" in text

    def test_a_delete_against_an_edit_conflicts(self):
        left = "one\nthree\nfour"
        right = "one\nEDITED\nthree\nfour"
        regions = merge3(BASE, left, right)
        assert conflict_count(regions) == 1

    def test_clean_lines_around_the_conflict_survive(self):
        left = "one\nLEFT\nthree\nfour"
        right = "one\nRIGHT\nthree\nfour"
        text = merged_text(BASE, left, right)
        assert text.startswith("one\n")
        assert text.endswith("three\nfour")

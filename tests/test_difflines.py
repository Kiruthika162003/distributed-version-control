from __future__ import annotations

import pytest

from keel.difflines import (
    apply_hunks,
    change_summary,
    diff_lines,
)
from keel.errors import Invalid

OLD = "alpha\nbeta\ngamma\ndelta\n"


class TestDiff:
    def test_identical_texts_produce_no_hunks(self):
        assert diff_lines(OLD, OLD) == []

    def test_an_insertion_is_one_hunk_with_coordinates(self):
        hunks = diff_lines(OLD, "alpha\nbeta\nnew\ngamma\ndelta\n")
        assert len(hunks) == 1
        assert hunks[0].kind() == "insert"
        assert hunks[0].describe() == (
            "insert at old:3 new:3 (-0 +1)"
        )

    def test_a_deletion_and_a_replace_classify(self):
        gone = diff_lines(OLD, "alpha\ngamma\ndelta\n")
        assert gone[0].kind() == "delete"
        swapped = diff_lines(OLD, "alpha\nBETA\ngamma\ndelta\n")
        assert swapped[0].kind() == "replace"

    def test_separated_edits_become_separate_hunks(self):
        hunks = diff_lines(
            OLD, "ALPHA\nbeta\ngamma\nDELTA\n"
        )
        assert len(hunks) == 2

    def test_the_guard_names_the_line_count(self):
        long_text = "\n".join(str(n) for n in range(2001))
        with pytest.raises(Invalid) as caught:
            diff_lines(long_text, "x")
        assert "teaches people to stop diffing" in str(
            caught.value
        )


class TestRoundTrip:
    def test_applying_the_hunks_rebuilds_the_new_text(self):
        new_text = "alpha\nBETA\ngamma\nextra\ndelta"
        hunks = diff_lines(OLD, new_text)
        assert apply_hunks(OLD, hunks) == new_text

    def test_a_hunk_applies_to_what_it_saw_or_not_at_all(self):
        hunks = diff_lines(OLD, "alpha\nBETA\ngamma\ndelta\n")
        drifted = "alpha\nchanged\ngamma\ndelta\n"
        with pytest.raises(Invalid) as caught:
            apply_hunks(drifted, hunks)
        assert "what they saw or not at all" in str(caught.value)


class TestSummary:
    def test_the_summary_counts_both_directions(self):
        assert change_summary(
            OLD, "alpha\ngamma\ndelta\nnew1\nnew2"
        ) == "2 hunk(s), -1 +2"

    def test_identical_is_a_word_not_a_zero(self):
        assert change_summary(OLD, OLD) == "identical"

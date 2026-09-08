from __future__ import annotations

from keel.difflines import Hunk, diff_lines
from keel.worddiff import (
    refine_hunk,
    tokenize,
    word_diff_line,
)


class TestTokens:
    def test_words_spaces_and_punctuation_split_apart(self):
        assert tokenize("total = a + b") == [
            "total", " ", "=", " ", "a", " ", "+", " ", "b",
        ]

    def test_operators_cluster_but_do_not_join_words(self):
        assert tokenize("x+=1") == ["x", "+=", "1"]


class TestWordDiff:
    def test_the_rename_claims_only_the_word(self):
        rendered = word_diff_line(
            "total = old_name + tax",
            "total = new_name + tax",
        )
        assert "[-old_name-]" in rendered
        assert "{+new_name+}" in rendered
        assert rendered.startswith("total = ")
        assert rendered.endswith(" + tax")

    def test_an_insertion_lands_between_the_words(self):
        rendered = word_diff_line(
            "return respond(request)",
            "return respond(request, retries)",
        )
        assert "{+" in rendered
        assert "retries" in rendered
        assert "[-" not in rendered


class TestRefinement:
    def test_similar_replaces_refine_to_word_level(self):
        hunks = diff_lines(
            "total = old_name + tax",
            "total = new_name + tax",
        )
        refined = refine_hunk(hunks[0])
        assert len(refined) == 1
        assert "[-old_name-]" in refined[0]

    def test_unrelated_lines_stay_blunt_not_confetti(self):
        hunk = Hunk(
            old_start=0,
            old_lines=("import os",),
            new_lines=("return 42 # unrelated",),
            new_start=0,
        )
        refined = refine_hunk(hunk)
        assert refined == [
            "-import os",
            "+return 42 # unrelated",
        ]

    def test_pure_inserts_pass_through_unrefined(self):
        hunk = Hunk(
            old_start=3,
            old_lines=(),
            new_lines=("brand new line",),
            new_start=3,
        )
        assert refine_hunk(hunk) == ["+brand new line"]

    def test_uneven_replaces_refine_pairs_and_list_the_rest(self):
        hunk = Hunk(
            old_start=0,
            old_lines=("total = a + b",),
            new_lines=("total = a + c", "extra = 1"),
            new_start=0,
        )
        refined = refine_hunk(hunk)
        assert "[-b-]" in refined[0]
        assert refined[1] == "+extra = 1"

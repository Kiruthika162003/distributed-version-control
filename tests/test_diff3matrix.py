from __future__ import annotations

from keel.witnesses.diff3matrix import run


class TestDiff3matrix:
    def test_the_testimony_holds(self):
        testimony = run()
        assert testimony.holds

    def test_all_nine_cells_are_graded(self):
        testimony = run()
        assert testimony.numbers["cases"] == 9
        assert testimony.numbers["agreed"] == 9

    def test_exactly_three_cells_conflict(self):
        testimony = run()
        assert testimony.numbers["total_conflicts"] == 3

    def test_the_seam_corrects_the_folklore(self):
        testimony = run()
        assert testimony.numbers["seam_conflicted"]

    def test_delete_versus_edit_asks_a_human(self):
        testimony = run()
        assert testimony.numbers[
            "delete_vs_edit_conflicted"
        ]

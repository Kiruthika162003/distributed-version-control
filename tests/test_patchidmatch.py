from __future__ import annotations

from keel.witnesses.patchidmatch import run


class TestPatchidmatch:
    def test_the_testimony_holds(self):
        testimony = run()
        assert testimony.holds

    def test_two_landed_one_pending(self):
        testimony = run()
        assert testimony.numbers["landed"] == 2
        assert testimony.numbers["pending"] == 1

    def test_identity_ignores_the_prose(self):
        testimony = run()
        assert testimony.numbers["reworded_still_matched"]

    def test_a_reshaped_diff_is_a_different_change(self):
        testimony = run()
        assert testimony.numbers["reshaped_honestly_missed"]

from __future__ import annotations

from keel.witnesses.renametrust import run


class TestRenametrust:
    def test_the_testimony_holds(self):
        testimony = run()
        assert testimony.holds

    def test_the_exact_column(self):
        testimony = run()
        assert testimony.numbers["exact_renames"] == 3

    def test_the_fuzzy_column_shows_its_scores(self):
        testimony = run()
        assert testimony.numbers["fuzzy_renames"] == 2
        for score in testimony.numbers["fuzzy_scores"]:
            assert 0.5 <= score < 1.0

    def test_the_impostor_stays_divorced(self):
        testimony = run()
        assert not testimony.numbers["impostor_married"]
        assert testimony.numbers["deletes"] == 1
        assert testimony.numbers["adds"] == 1

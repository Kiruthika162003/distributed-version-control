from __future__ import annotations

from keel.witnesses.survivorship import run


class TestSurvivorship:
    def test_the_testimony_holds(self):
        testimony = run()
        assert testimony.holds

    def test_the_present_is_fully_accounted_for(self):
        testimony = run()
        numbers = testimony.numbers
        assert numbers["lines_at_tip"] == 8
        assert (
            numbers["founding"]
            + numbers["expansion"]
            + numbers["rewrite"]
            + numbers["polish"]
        ) == 8

    def test_the_founder_owns_a_quarter(self):
        testimony = run()
        assert testimony.numbers["founding"] == 2

    def test_the_last_writer_owns_the_rewrite(self):
        testimony = run()
        assert testimony.numbers["rewrite"] == 2

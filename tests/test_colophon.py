from __future__ import annotations

from keel.colophon import page
from keel.organs import roster
from keel.voyages import names
from keel.witnesses import registry


class TestTheColophon:
    def test_every_number_is_computed_not_quoted(self):
        text = page()
        assert text.startswith("colophon:")
        assert (
            f"{len(roster())} organ(s), each opening "
            "with its own sentence"
        ) in text
        assert (
            f"{len(names())} voyage(s), each a day "
            "someone has actually had"
        ) in text
        assert (
            f"{len(registry.WITNESSES)} witness(es), "
            "0 broken, measured fresh for this page"
        ) in text

    def test_the_trial_runs_for_the_occasion(self):
        text = page()
        assert (
            "7 system(s) exercised, all answered"
        ) in text

    def test_the_habits_are_admitted(self):
        text = page()
        assert (
            "refusals that explain themselves"
        ) in text
        assert (
            "guesses corrected by measurement and "
            "kept"
        ) in text
        assert "receipts for everything loud" in text
        assert (
            "numbers said plainly, nothing promised "
            "beyond them"
        ) in text

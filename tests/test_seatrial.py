from __future__ import annotations

from keel.seatrial import run_trial


class TestTheTrial:
    def test_every_system_answers(self):
        page = run_trial()
        assert page.startswith("sea trial:")
        assert (
            "store: held and returned the bytes"
        ) in page
        assert "graph: ancestry holds" in page
        assert (
            "diff3: merged the clean, flagged the "
            "collision"
        ) in page
        assert (
            "shelf: held and returned the work"
        ) in page
        assert (
            "hunt: found the planted culprit"
        ) in page
        assert (
            "wire: shipped only what was lacking"
        ) in page
        assert (
            "rewrite: folded the fixup silently"
        ) in page

    def test_the_closing_line_counts_the_tour(self):
        page = run_trial()
        assert (
            "7 system(s) exercised, all answered"
        ) in page
        assert (
            "the whole ship, not the good deck"
        ) in page

    def test_the_trial_is_repeatable(self):
        assert run_trial() == run_trial()

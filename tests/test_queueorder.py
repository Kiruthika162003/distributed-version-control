from __future__ import annotations

from keel.witnesses.queueorder import run


class TestQueueorder:
    def test_the_testimony_holds(self):
        testimony = run()
        assert testimony.holds

    def test_the_contenders_swap_exactly(self):
        testimony = run()
        assert testimony.numbers["east_first"] == (
            "landed",
            "bounced",
        )
        assert testimony.numbers["west_first"] == (
            "bounced",
            "landed",
        )

    def test_the_bystanders_hold_still(self):
        testimony = run()
        assert testimony.numbers["docs_landed_both_runs"]
        assert testimony.numbers[
            "gated_bounced_both_runs"
        ]

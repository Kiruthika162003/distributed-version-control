from __future__ import annotations

from keel.witnesses.rererebill import run


class TestRererebill:
    def test_the_testimony_holds(self):
        testimony = run()
        assert testimony.holds

    def test_the_bill_splits_hand_from_free(self):
        testimony = run()
        assert testimony.numbers["recorded_by_hand"] == 1
        assert testimony.numbers["replayed_free"] == 4

    def test_the_different_base_is_an_honest_miss(self):
        testimony = run()
        assert testimony.numbers["different_base_missed"]

    def test_the_ledger_agrees_with_the_count(self):
        testimony = run()
        assert testimony.numbers["ledger_replays"] == 4

from __future__ import annotations

import pytest

from keel.errors import Conflict, Invalid, Missing
from keel.quorum import QuorumLedger


def proposed() -> QuorumLedger:
    ledger = QuorumLedger()
    ledger.propose(
        "rewrite-2026",
        "expunge the leaked key from history",
        3,
    )
    return ledger


class TestVoting:
    def test_the_deciding_voter_hears_it_now(self):
        ledger = proposed()
        ledger.approve("rewrite-2026", "priya")
        second = ledger.approve("rewrite-2026", "devi")
        assert second == (
            "rewrite-2026: 2 of 3, devi on record"
        )
        third = ledger.approve("rewrite-2026", "dana")
        assert "reaches quorum at 3 of 3" in third
        assert "dana, your vote decided it" in third

    def test_one_person_twice_is_one_person(self):
        ledger = proposed()
        ledger.approve("rewrite-2026", "priya")
        with pytest.raises(Invalid) as caught:
            ledger.approve("rewrite-2026", "priya")
        assert "one person twice is one person" in str(
            caught.value
        )

    def test_a_quorum_of_one_is_paperwork(self):
        with pytest.raises(Invalid) as caught:
            QuorumLedger().propose("tiny", "thing", 1)
        assert "reviewer with paperwork" in str(
            caught.value
        )


class TestVetoes:
    def test_the_veto_stops_the_count_with_a_reason(
        self,
    ):
        ledger = proposed()
        ledger.veto(
            "rewrite-2026",
            "asha",
            "the key is still in use downstream",
        )
        with pytest.raises(Conflict) as caught:
            ledger.approve("rewrite-2026", "priya")
        assert "stands vetoed by asha" in str(
            caught.value
        )

    def test_only_the_same_name_lifts_it(self):
        ledger = proposed()
        ledger.veto("rewrite-2026", "asha", "not yet")
        with pytest.raises(Invalid) as caught:
            ledger.lift_veto("rewrite-2026", "priya")
        assert "strongly worded comment" in str(
            caught.value
        )
        ledger.lift_veto("rewrite-2026", "asha")
        receipt = ledger.approve(
            "rewrite-2026", "priya"
        )
        assert "1 of 3" in receipt

    def test_a_reasonless_veto_is_a_mood(self):
        ledger = proposed()
        with pytest.raises(Invalid) as caught:
            ledger.veto("rewrite-2026", "asha", "  ")
        assert "a mood with authority" in str(
            caught.value
        )


class TestTheLedger:
    def test_withdrawal_is_announced_never_evaporated(
        self,
    ):
        ledger = proposed()
        ledger.approve("rewrite-2026", "priya")
        receipt = ledger.withdraw("rewrite-2026")
        assert (
            "withdrawn with 1 approval(s) on record"
        ) in receipt
        with pytest.raises(Missing):
            ledger.withdraw("rewrite-2026")

    def test_the_standing_page_shows_both_states(self):
        ledger = proposed()
        ledger.propose(
            "license-swap", "move to harbor v2", 2
        )
        ledger.approve("rewrite-2026", "priya")
        ledger.veto(
            "license-swap", "counsel", "review pending"
        )
        page = ledger.standing()
        assert page.startswith(
            "2 proposal(s) standing:"
        )
        assert (
            "rewrite-2026: expunge the leaked key "
            "from history (1 of 3)"
        ) in page
        assert (
            "license-swap: move to harbor v2 "
            "(VETOED by counsel)"
        ) in page

from __future__ import annotations

import pytest

from keel.errors import Conflict, Invalid, Missing
from keel.filelocks import LockOffice


def held_office() -> LockOffice:
    office = LockOffice()
    office.take(
        "design.sketch", "priya", "reworking the header"
    )
    return office


class TestTakingTurns:
    def test_a_lock_names_who_and_why(self):
        office = LockOffice()
        receipt = office.take(
            "design.sketch",
            "priya",
            "reworking the header",
        )
        assert receipt == (
            "design.sketch locked by priya: "
            "reworking the header"
        )

    def test_a_whyless_lock_teaches_stealing(self):
        with pytest.raises(Invalid) as caught:
            LockOffice().take("a.bin", "priya", " ")
        assert "steal early" in str(caught.value)

    def test_a_second_lock_quotes_both_facts(self):
        office = held_office()
        with pytest.raises(Conflict) as caught:
            office.take(
                "design.sketch", "devi", "my turn"
            )
        message = str(caught.value)
        assert "held by priya" in message
        assert "reworking the header" in message

    def test_release_belongs_to_the_holder(self):
        office = held_office()
        with pytest.raises(Invalid) as caught:
            office.release("design.sketch", "devi")
        assert "steal wearing politeness" in str(
            caught.value
        )
        receipt = office.release(
            "design.sketch", "priya"
        )
        assert "the turn is over" in receipt


class TestStealing:
    def test_the_steal_is_loud_and_recorded(self):
        office = held_office()
        entry = office.steal(
            "design.sketch",
            "devi",
            "priya is on leave and the release waits",
        )
        assert entry.startswith(
            "STOLEN: design.sketch from priya by devi"
        )
        assert entry in office.journal
        assert office.locks["design.sketch"].holder == (
            "devi"
        )

    def test_taking_the_unheld_is_just_taking(self):
        with pytest.raises(Missing):
            LockOffice().steal("a.bin", "devi", "why")

    def test_a_quiet_steal_is_refused(self):
        office = held_office()
        with pytest.raises(Invalid) as caught:
            office.steal("design.sketch", "devi", "")
        assert "quiet steal" in str(caught.value)


class TestLandings:
    def test_the_holder_lands_and_others_bounce(self):
        office = held_office()
        assert office.check_landing(
            "priya", ["design.sketch", "readme.md"]
        ).endswith("land away")
        with pytest.raises(Conflict) as caught:
            office.check_landing(
                "devi", ["design.sketch"]
            )
        message = str(caught.value)
        assert "held by priya" in message
        assert "one short conversation" in message

    def test_the_listing_reads_the_office(self):
        office = held_office()
        page = office.listing()
        assert "1 lock(s) held:" in page
        assert (
            "design.sketch: priya (reworking the "
            "header)"
        ) in page
        office.release("design.sketch", "priya")
        assert "no locks held" in office.listing()

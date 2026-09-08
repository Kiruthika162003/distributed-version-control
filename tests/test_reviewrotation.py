from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.reviewrotation import Wheel


def build() -> Wheel:
    wheel = Wheel()
    for member in ("asha", "binh", "chidi"):
        wheel.enroll("team-core", member)
    return wheel


class TestTheWheel:
    def test_strict_rotation_in_enrollment_order(self):
        wheel = build()
        first = wheel.assign("team-core")
        second = wheel.assign("team-core")
        third = wheel.assign("team-core")
        fourth = wheel.assign("team-core")
        assert first.startswith("team-core assigns asha")
        assert second.startswith(
            "team-core assigns binh"
        )
        assert third.startswith(
            "team-core assigns chidi"
        )
        assert fourth.startswith(
            "team-core assigns asha (load now 2)"
        )

    def test_double_enrollment_is_refused(self):
        wheel = build()
        with pytest.raises(Invalid):
            wheel.enroll("team-core", "asha")

    def test_an_unknown_team_has_no_wheel(self):
        with pytest.raises(Missing):
            Wheel().assign("team-ghost")


class TestAbsences:
    def test_skips_are_said_aloud(self):
        wheel = build()
        wheel.declare_away("asha", "back after v2 ships")
        receipt = wheel.assign("team-core")
        assert receipt.startswith(
            "team-core assigns binh"
        )
        assert (
            "skipped asha (back after v2 ships)"
        ) in receipt
        assert "a silent pass-over is a forgetting" in (
            receipt
        )

    def test_an_unexplained_absence_is_refused(self):
        wheel = build()
        with pytest.raises(Invalid) as caught:
            wheel.declare_away("asha", "  ")
        assert "permanent exemption" in str(caught.value)

    def test_the_returned_ride_again(self):
        wheel = build()
        wheel.declare_away("asha", "leave")
        assert wheel.declare_back("asha") == (
            "asha rides again"
        )
        assert wheel.assign("team-core").startswith(
            "team-core assigns asha"
        )

    def test_a_ghost_bench_is_refused_loudly(self):
        wheel = build()
        for member in ("asha", "binh", "chidi"):
            wheel.declare_away(member, "offsite week")
        with pytest.raises(Invalid) as caught:
            wheel.assign("team-core")
        assert "the whole team-core bench is away" in (
            str(caught.value)
        )
        assert "fails slower than work refused now" in (
            str(caught.value)
        )


class TestFairness:
    def test_the_audit_shows_loads_and_spread(self):
        wheel = build()
        wheel.assign("team-core")
        wheel.assign("team-core")
        wheel.declare_away("chidi", "jury duty")
        page = wheel.fairness("team-core")
        assert "asha: 1 assignment(s)" in page
        assert "binh: 1 assignment(s)" in page
        assert (
            "chidi: 0 assignment(s) [away: jury duty]"
        ) in page
        assert (
            "spread 1; fairness is auditable or it "
            "is folklore"
        ) in page

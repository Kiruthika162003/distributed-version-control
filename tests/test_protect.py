from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.protect import BranchGuard, Protection


def guarded() -> BranchGuard:
    guard = BranchGuard()
    guard.protect(Protection(pattern="main"))
    guard.protect(
        Protection(
            pattern="release/*", required_reviews=2
        )
    )
    return guard


class TestRestrictions:
    def test_deletion_of_the_load_bearing_name_is_refused(self):
        guard = guarded()
        with pytest.raises(Invalid) as caught:
            guard.check_delete("main")
        assert "other systems stand on this tip" in str(
            caught.value
        )
        assert len(guard.refusals) == 1

    def test_forced_movement_names_the_rule(self):
        guard = guarded()
        with pytest.raises(Invalid) as caught:
            guard.check_force("release/1.x")
        assert "refused by rule release/*" in str(caught.value)
        assert "nobody hunts an admin" in str(caught.value)

    def test_unprotected_branches_stay_fast_and_loose(self):
        guard = guarded()
        assert "may be deleted" in guard.check_delete(
            "topic/x"
        )
        assert "may move freely" in guard.check_force(
            "topic/x"
        )


class TestLanding:
    def test_reviews_are_checked_not_trusted(self):
        guard = guarded()
        message = (
            "land the fix\n\nbody\n\n"
            "Reviewed-by: Asha\nReviewed-by: Ben"
        )
        verdict = guard.check_landing(
            "release/1.x", message
        )
        assert "2 review(s) satisfy release/*" in verdict

    def test_the_shortfall_counts_both_numbers(self):
        guard = guarded()
        with pytest.raises(Invalid) as caught:
            guard.check_landing(
                "release/1.x",
                "land\n\nbody\n\nReviewed-by: Asha",
            )
        assert "1 review trailer(s) against 2 required" in (
            str(caught.value)
        )

    def test_zero_required_reviews_is_a_design_choice(self):
        guard = guarded()
        assert "fast and loose by design" in (
            guard.check_landing("topic/x", "anything")
        )

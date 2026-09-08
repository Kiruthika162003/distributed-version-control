from __future__ import annotations

import pytest

from keel.errors import Conflict, Invalid, Missing
from keel.freeze import FreezeBoard


def frozen_board() -> FreezeBoard:
    board = FreezeBoard()
    board.freeze("main", "the release cut", "priya")
    return board


class TestFreezing:
    def test_the_sign_says_why_and_whom(self):
        board = FreezeBoard()
        sign = board.freeze(
            "main", "the release cut", "priya"
        )
        assert sign == (
            "main frozen: the release cut (ask priya)"
        )

    def test_a_reasonless_freeze_is_refused(self):
        with pytest.raises(Invalid) as caught:
            FreezeBoard().freeze("main", "  ", "priya")
        assert "lockout, not a policy" in str(caught.value)

    def test_an_anonymous_freeze_is_refused(self):
        with pytest.raises(Invalid) as caught:
            FreezeBoard().freeze("main", "reasons", "")
        assert "cannot be respected" in str(caught.value)

    def test_double_freezing_is_refused_with_the_standing(
        self,
    ):
        board = frozen_board()
        with pytest.raises(Invalid) as caught:
            board.freeze("main", "another panic", "dev")
        assert "already frozen by priya" in str(
            caught.value
        )

    def test_lifting_warm_air_is_refused(self):
        with pytest.raises(Missing):
            FreezeBoard().lift("main", "priya")


class TestLandings:
    def test_an_open_branch_lands_away(self):
        board = FreezeBoard()
        assert board.check_landing("main", "dev") == (
            "main is open; land away"
        )

    def test_a_frozen_branch_refuses_with_the_reason(self):
        board = frozen_board()
        with pytest.raises(Conflict) as caught:
            board.check_landing("main", "dev")
        message = str(caught.value)
        assert "closed for the release cut" in message
        assert "ask priya" in message

    def test_lifting_reopens(self):
        board = frozen_board()
        board.lift("main", "priya")
        assert "land away" in board.check_landing(
            "main", "dev"
        )


class TestOverrides:
    def test_the_sanctioned_exception_is_loud(self):
        board = frozen_board()
        entry = board.override(
            "main", "dev", "priya", "HOT-42"
        )
        assert entry.startswith("OVERRIDE: dev landed")
        assert "approved by priya" in entry
        assert "ticket HOT-42" in entry

    def test_self_approval_is_refused(self):
        board = frozen_board()
        with pytest.raises(Invalid) as caught:
            board.override("main", "dev", "dev", "HOT-42")
        assert "extra steps removed" in str(caught.value)

    def test_a_ticketless_override_is_refused(self):
        board = frozen_board()
        with pytest.raises(Invalid) as caught:
            board.override("main", "dev", "priya", " ")
        assert "become the norm" in str(caught.value)

    def test_overriding_warm_air_is_refused(self):
        with pytest.raises(Invalid) as caught:
            FreezeBoard().override(
                "main", "dev", "priya", "HOT-42"
            )
        assert "story for the postmortem" in str(
            caught.value
        )


class TestTheReport:
    def test_the_policy_reports_its_own_cost(self):
        board = frozen_board()
        for _attempt in range(3):
            with pytest.raises(Conflict):
                board.check_landing("main", "dev")
        board.override("main", "dev", "priya", "HOT-42")
        page = board.report()
        assert page.startswith(
            "1 branch(es) frozen, 3 landing(s) stopped, "
            "1 override(s)"
        )
        assert "main: the release cut (ask priya)" in page
        assert "OVERRIDE: dev landed" in page

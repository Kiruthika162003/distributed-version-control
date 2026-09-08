from __future__ import annotations

from keel.budgets import BudgetBook
from keel.deprecations import DeprecationLedger
from keel.filelocks import LockOffice
from keel.freeze import FreezeBoard
from keel.repo import Repo
from keel.reviewrotation import Wheel
from keel.standingorders import board


def full_board() -> str:
    freezes = FreezeBoard()
    freezes.freeze("main", "the release cut", "priya")
    locks = LockOffice()
    locks.take("design.sketch", "devi", "recoloring")
    wheel = Wheel()
    wheel.enroll("team-core", "asha")
    wheel.declare_away("asha", "back after v2")
    repo = Repo.init()
    repo.commit(
        {"old_api.py": b"legacy\n"}, "base"
    )
    ledger = DeprecationLedger(repo=repo)
    ledger.declare("old_api.py", "new_api.py", 9)
    budgets = BudgetBook()
    budgets.set_allowance("assets/", 1000)
    return board(
        freezes=freezes,
        locks=locks,
        wheel=wheel,
        deprecations=ledger,
        budgets=budgets,
    )


class TestTheBoard:
    def test_every_binding_rule_gets_one_line(self):
        page = full_board()
        assert page.startswith(
            "5 standing order(s) in force:"
        )
        assert (
            "main is frozen: the release cut "
            "(ask priya)"
        ) in page
        assert (
            "design.sketch is locked by devi: "
            "recoloring"
        ) in page
        assert "asha is away: back after v2" in page
        assert (
            "old_api.py is deprecated for "
            "new_api.py, gone by sequence 9"
        ) in page
        assert (
            "assets/ is budgeted at 1000 byte(s)"
        ) in page

    def test_the_empty_board_frees_the_judgment(self):
        assert board() == (
            "no standing orders; act on judgment"
        )

    def test_absent_organs_need_no_line(self):
        freezes = FreezeBoard()
        freezes.freeze("main", "cut week", "priya")
        page = board(freezes=freezes)
        assert page.startswith(
            "1 standing order(s) in force:"
        )
        assert "not checked" not in page

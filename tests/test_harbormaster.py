from __future__ import annotations

import pytest

from keel.acl import AccessTable
from keel.budgets import BudgetBook
from keel.customs import Customs
from keel.departures import Departures
from keel.errors import Conflict
from keel.filelocks import LockOffice
from keel.freeze import FreezeBoard
from keel.gatekeeper import Gatekeeper, PushRequest
from keel.harbormaster import Harbormaster
from keel.protect import BranchGuard, Protection
from keel.repo import Repo

REVIEWED = (
    "Land the retry\n"
    "\n"
    "Reviewed-by: priya\n"
    "Reviewed-by: devi\n"
)

BASE = {"src/app.py": b"core\n"}


def build() -> Harbormaster:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    guard = BranchGuard()
    guard.protect(
        Protection(pattern="main", required_reviews=2)
    )
    keeper = Gatekeeper(
        guard=guard, board=FreezeBoard()
    )
    customs = Customs(
        repo=repo,
        access=AccessTable(),
        locks=LockOffice(),
        budgets=BudgetBook(),
    )
    return Harbormaster(
        gatekeeper=keeper,
        customs=customs,
        departures=Departures(),
    )


def request(**overrides) -> PushRequest:
    settings = {
        "branch": "main",
        "submitter": "dana",
        "messages": (REVIEWED,),
        "touched_paths": ("src/app.py",),
        "force": False,
    }
    settings.update(overrides)
    return PushRequest(**settings)


class TestTheOneDesk:
    def test_a_clean_landing_clears_in_one_visit(self):
        master = build()
        proposed = dict(
            BASE, **{"src/app.py": b"core\nretry\n"}
        )
        page = master.land(request(), proposed)
        assert page.startswith(
            "the harbor clears this landing: three "
            "gauntlets, one visit"
        )
        assert "push of main by dana: ACCEPTED" in page
        assert "customs clears dana" in page
        assert "cleared for departure" in page
        assert (
            "the argument for the office is arithmetic"
        ) in page

    def test_holds_arrive_in_each_gauntlets_own_words(
        self,
    ):
        master = build()
        master.gatekeeper.board.freeze(
            "main", "the release cut", "priya"
        )
        proposed = dict(
            BASE,
            **{
                "src/app.py": b"core\nretry\n",
                "conf.ini": b"password=hunter2\n",
            },
        )
        with pytest.raises(Conflict) as caught:
            master.land(
                request(
                    touched_paths=(
                        "src/app.py",
                        "conf.ini",
                    )
                ),
                proposed,
            )
        page = str(caught.value)
        assert (
            "the harbor holds this landing: 2 of 3 "
            "gauntlet(s) object"
        ) in page
        assert "closed for the release cut" in page
        assert "departure denied" in page
        assert "customs clears dana" in page
        assert "hunter2" not in page

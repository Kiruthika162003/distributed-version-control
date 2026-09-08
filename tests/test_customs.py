from __future__ import annotations

import pytest

from keel.acl import AccessTable
from keel.budgets import BudgetBook
from keel.customs import Customs
from keel.errors import Conflict
from keel.filelocks import LockOffice
from keel.repo import Repo

BASE = {
    "infra/deploy.sh": b"deploy\n",
    "assets/logo.bin": b"x" * 80,
    "src/app.py": b"core\n",
}


def build() -> Customs:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    access = AccessTable()
    access.enroll("team-infra", "priya")
    access.grant("infra/", "team-infra")
    locks = LockOffice()
    locks.take(
        "assets/logo.bin", "devi", "recoloring"
    )
    budgets = BudgetBook()
    budgets.set_allowance("assets/", 100)
    return Customs(
        repo=repo,
        access=access,
        locks=locks,
        budgets=budgets,
    )


class TestClearance:
    def test_a_clean_shipment_passes_all_three(self):
        customs = build()
        proposed = dict(
            BASE, **{"src/app.py": b"core\nmore\n"}
        )
        page = customs.clear("dana", proposed)
        assert page.startswith(
            "customs clears dana: 1 path(s)"
        )
        assert "access: [ok]" in page
        assert "locks: [ok]" in page
        assert "budgets: [ok]" in page

    def test_every_gate_speaks_even_when_all_object(
        self,
    ):
        customs = build()
        proposed = dict(
            BASE,
            **{
                "infra/deploy.sh": b"deploy\nrogue\n",
                "assets/logo.bin": b"x" * 200,
            },
        )
        with pytest.raises(Conflict) as caught:
            customs.clear("dana", proposed)
        page = str(caught.value)
        assert (
            "customs holds the shipment: 3 gate(s) "
            "object (access, locks, budgets)"
        ) in page
        assert "access: [HOLD]" in page
        assert "locks: [HOLD]" in page
        assert "budgets: [HOLD]" in page
        assert "every gate spoke either way" in page

    def test_the_lock_holder_passes_their_own_gate(self):
        customs = build()
        proposed = dict(
            BASE, **{"assets/logo.bin": b"x" * 90}
        )
        page = customs.clear("devi", proposed)
        assert "locks: [ok]" in page


class TestWavedGates:
    def test_absent_organs_are_named_not_silent(self):
        repo = Repo.init()
        repo.commit(dict(BASE), "base")
        customs = Customs(repo=repo)
        page = customs.clear(
            "dana",
            dict(BASE, **{"src/app.py": b"core\n2\n"}),
        )
        assert (
            "access: [ok] no table; waved through"
        ) in page
        assert (
            "locks: [ok] no office; waved through"
        ) in page
        assert (
            "budgets: [ok] no book; waved through"
        ) in page

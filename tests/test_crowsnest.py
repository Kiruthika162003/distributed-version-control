from __future__ import annotations

from keel.budgets import BudgetBook
from keel.crowsnest import watch
from keel.deprecations import DeprecationLedger
from keel.repo import Repo

BASE = {
    "old_api.py": b"legacy\n",
    "assets/logo.bin": b"x" * 85,
}


def build() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.branch_from_head("drifting")
    repo.refs.checkout("drifting")
    repo.commit(
        dict(BASE, **{"old_api.py": b"legacy\nd\n"}),
        "drifting work",
    )
    repo.refs.checkout("main")
    return repo


def advance(repo: Repo, steps: int) -> None:
    files = dict(BASE)
    for step in range(steps):
        files["trunkfile.py"] = (
            f"t{step}\n".encode()
        )
        repo.commit(dict(files), f"trunk {step}")


class TestApproaches:
    def test_the_drifting_branch_is_called_early(self):
        repo = build()
        advance(repo, 4)
        page = watch(repo, window=5)
        assert (
            "drifting is 4 of 5 toward stale"
        ) in page
        assert (
            "while its author still remembers"
        ) in page

    def test_a_fresh_branch_is_not_called(self):
        repo = build()
        advance(repo, 1)
        page = watch(repo, window=5)
        assert "drifting" not in page
        assert "clear horizons" in page

    def test_the_burning_deadline_is_called(self):
        repo = build()
        ledger = DeprecationLedger(repo=repo)
        ledger.declare("old_api.py", "new_api.py", 7)
        advance(repo, 5)
        page = watch(
            repo, window=50, deprecations=ledger
        )
        assert (
            "old_api.py has burned 6 of 7 toward its "
            "deadline"
        ) in page
        assert "visible before it misses" in page

    def test_the_thinning_budget_is_called(self):
        repo = build()
        budgets = BudgetBook()
        budgets.set_allowance("assets/", 100)
        page = watch(repo, window=50, budgets=budgets)
        assert (
            "assets/ stands at 85 of 100 byte(s)"
        ) in page
        assert "15 of headroom" in page

    def test_clear_horizons_keep_the_lookout_credible(
        self,
    ):
        repo = build()
        page = watch(repo, window=50)
        assert (
            "a lookout who only ever cries alarm is "
            "a lookout nobody believes"
        ) in page

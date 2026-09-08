from __future__ import annotations

from keel.branchpolicy import NamingPolicy
from keel.budgets import BudgetBook
from keel.codeowners import OwnersFile
from keel.deprecations import DeprecationLedger
from keel.nightwatch import NightWatch
from keel.repo import Repo

BASE = {
    "src/app.py": b"core\n",
    "docs/guide.md": b"g\n",
}


def tidy_watch() -> NightWatch:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.branch_from_head("feature/dark-mode")
    owners = OwnersFile.parse(
        "src/ team-core\ndocs/ team-docs\n"
    )
    budgets = BudgetBook()
    budgets.set_allowance("src/", 1000)
    return NightWatch(
        repo=repo,
        owners=owners,
        policy=NamingPolicy(),
        deprecations=DeprecationLedger(repo=repo),
        budgets=budgets,
    )


class TestQuietRounds:
    def test_a_tidy_repo_keeps_its_promises(self):
        page = tidy_watch().rounds()
        assert page.startswith("the night watch:")
        assert "0 orphan(s) for adoption" in page
        assert "0 unlabeled" in page
        assert "nothing here is dying" in page
        assert "planned diet" in page
        assert (
            "every ledger walked, none drifting"
        ) in page

    def test_absent_organs_are_logged_not_skipped(self):
        repo = Repo.init()
        repo.commit(dict(BASE), "base")
        page = NightWatch(repo=repo).rounds()
        assert (
            page.count("not on the rounds tonight") == 4
        )
        assert "none drifting" in page


class TestDriftingLedgers:
    def test_drifts_are_counted_by_ledger_not_finding(
        self,
    ):
        watch = tidy_watch()
        watch.repo.branch_from_head("junkdrawer")
        watch.repo.refs.checkout("main")
        files = dict(
            BASE, **{"scripts/deploy.sh": b"sh\n"}
        )
        watch.repo.commit(files, "unowned arrival")
        page = watch.rounds()
        assert "orphan: scripts/deploy.sh" in page
        assert "junkdrawer" in page
        assert (
            "2 ledger(s) drifting; one is a chore"
        ) in page
        assert (
            "the number tells you which meeting to "
            "book"
        ) in page

from __future__ import annotations

from keel.gc import Collector
from keel.maintenance import MaintenanceRun
from keel.repo import Repo


def busy_repo(commits: int = 6) -> Repo:
    repo = Repo.init()
    for number in range(commits):
        repo.commit(
            {
                "app.py": f"version {number}\n".encode() * 20,
                "lib.py": b"stable helper\n" * 10,
            },
            f"c{number}",
        )
    return repo


class TestTheRun:
    def test_the_receipts_reconcile(self):
        repo = busy_repo()
        report = MaintenanceRun(repo=repo).run()
        assert report.startswith(
            "maintenance complete, receipts reconciled:"
        )
        assert "repack:" in report
        assert "collect:" in report

    def test_a_clean_repo_frees_nothing(self):
        repo = busy_repo()
        run = MaintenanceRun(repo=repo)
        run.collect()
        assert "0 freed" in run.receipts[-1]

    def test_the_abandoned_commit_is_freed_after_trim(self):
        repo = busy_repo()
        abandoned = repo.refs.current()
        repo.refs.move(
            "main",
            repo.graph.get(abandoned).parents[0],
            reason="reset",
            force=True,
        )
        repo.refs.checkout("main")
        Collector(repo=repo).trim_reflog(keep_last=1)
        run = MaintenanceRun(repo=repo)
        run.collect()
        assert "0 freed" not in run.receipts[-1]

    def test_the_budget_admits_an_unfinished_desk(self):
        repo = busy_repo(commits=8)
        run = MaintenanceRun(repo=repo, effort_budget=3)
        run.repack()
        assert "left on the desk" in run.receipts[-1]
        assert "the budget ran out before the desk did" in (
            run.receipts[-1]
        )

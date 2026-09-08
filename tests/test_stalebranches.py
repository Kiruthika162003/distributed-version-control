from __future__ import annotations

import pytest

from keel.errors import Invalid, Missing
from keel.repo import Repo
from keel.stalebranches import census, report, sweep


def build() -> Repo:
    repo = Repo.init()
    repo.commit({"app.py": b"1\n"}, "c1")
    repo.branch_from_head("merged-work")
    repo.commit({"app.py": b"1\n2\n"}, "c2")
    repo.branch_from_head("doomed")
    repo.refs.checkout("doomed")
    repo.commit({"app.py": b"1\n2\nside\n"}, "side work")
    repo.refs.checkout("main")
    for step in range(7):
        repo.commit(
            {"app.py": f"1\n2\nmain{step}\n".encode()},
            f"trunk step {step}",
        )
    repo.branch_from_head("fresh")
    repo.refs.checkout("fresh")
    repo.commit(
        {"app.py": b"1\n2\nmain6\nfresh\n"}, "fresh work"
    )
    repo.refs.checkout("main")
    return repo


class TestCensus:
    def test_each_branch_gets_its_verdict(self):
        repo = build()
        verdicts = {
            verdict.branch: verdict.verdict
            for verdict in census(repo)
        }
        assert verdicts == {
            "merged-work": "merged",
            "doomed": "stale",
            "fresh": "active",
        }

    def test_the_trunk_judges_without_being_judged(self):
        repo = build()
        branches = [
            verdict.branch for verdict in census(repo)
        ]
        assert "main" not in branches

    def test_ages_count_in_sequence_numbers(self):
        repo = build()
        ages = {
            verdict.branch: verdict.age
            for verdict in census(repo)
        }
        assert ages["merged-work"] == 9
        assert ages["doomed"] == 7
        assert ages["fresh"] == 0

    def test_a_missing_trunk_is_refused(self):
        repo = build()
        with pytest.raises(Missing):
            census(repo, trunk="develop")

    def test_a_zero_window_is_refused(self):
        repo = build()
        with pytest.raises(Invalid) as caught:
            census(repo, window=0)
        assert "including the trunk" in str(caught.value)


class TestReport:
    def test_the_headline_counts_all_three(self):
        repo = build()
        page = report(repo)
        assert page.startswith(
            "1 merged, 1 stale, 1 active (window 5)"
        )

    def test_prescriptions_name_the_verb(self):
        repo = build()
        page = report(repo)
        assert "delete; the trunk already holds" in page
        assert "leave it alone" in page
        assert "ask its owner" in page
        assert "no algorithm can tell which" in page

    def test_a_lonely_trunk_has_nothing_to_judge(self):
        repo = Repo.init()
        repo.commit({"app.py": b"1\n"}, "c1")
        assert "nothing to judge" in report(repo)


class TestSweep:
    def test_merged_branches_go_and_stale_ones_stay(self):
        repo = build()
        page = sweep(repo)
        assert "swept 1 merged branch(es)" in page
        assert "spared 1 stale one(s)" in page
        assert "gone: merged-work" in page
        assert "merged-work" not in repo.refs.branches
        assert "doomed" in repo.refs.branches
        assert "fresh" in repo.refs.branches

    def test_a_sweep_with_nothing_merged_deletes_nothing(
        self,
    ):
        repo = build()
        sweep(repo)
        second = sweep(repo)
        assert "swept 0 merged branch(es)" in second
        assert "gone:" not in second

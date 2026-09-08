from __future__ import annotations

import pytest

from keel.backport import execute, narrate, plan
from keel.errors import Invalid
from keel.repo import Repo


def build() -> tuple[Repo, str]:
    repo = Repo.init()
    repo.commit(
        {"app.py": b"core\nbug\n", "lib.py": b"lib\n"},
        "base",
    )
    repo.branch_from_head("release-1.0")
    repo.branch_from_head("release-1.1")
    repo.refs.checkout("release-1.0")
    repo.commit(
        {
            "app.py": b"core\nbug\nlegacy\n",
            "lib.py": b"lib\n",
        },
        "legacy hack on the old line",
    )
    repo.refs.checkout("main")
    repo.commit(
        {
            "app.py": b"core\nbug\n",
            "lib.py": b"lib\nextra\n",
        },
        "unrelated growth",
    )
    fix = repo.commit(
        {
            "app.py": b"core\nfixed\n",
            "lib.py": b"lib\nextra\n",
        },
        "fix: stop the crash on empty input",
    )
    repo.branch_from_head("release-2.0")
    return repo, fix.address


class TestThePlan:
    def test_oldest_patient_first_with_three_verdicts(
        self,
    ):
        repo, fix = build()
        verdicts = plan(
            repo,
            fix,
            ["release-2.0", "release-1.0", "release-1.1"],
        )
        assert [v.branch for v in verdicts] == [
            "release-1.1",
            "release-1.0",
            "release-2.0",
        ]
        by_branch = {v.branch: v for v in verdicts}
        assert by_branch["release-1.1"].verdict == (
            "applies cleanly"
        )
        assert by_branch["release-1.0"].verdict == (
            "diverged"
        )
        assert by_branch["release-2.0"].verdict == (
            "already there"
        )

    def test_divergence_names_the_path_and_the_truth(
        self,
    ):
        repo, fix = build()
        verdicts = plan(repo, fix, ["release-1.0"])
        assert "app.py moved on" in verdicts[0].detail
        assert (
            "a new change wearing the old message"
        ) in verdicts[0].detail

    def test_a_merge_fix_is_refused(self):
        repo, fix = build()
        side = repo.graph.create(
            tree=repo.graph.get(fix).tree,
            parents=(fix,),
            message="side",
        )
        merged = repo.commit_with_parents(
            {"app.py": b"m\n"},
            "merge",
            (fix, side.address),
        )
        with pytest.raises(Invalid) as caught:
            plan(repo, merged.address, ["release-1.1"])
        assert "a meeting, not a fix" in str(caught.value)

    def test_a_backport_to_nowhere_is_refused(self):
        repo, fix = build()
        with pytest.raises(Invalid) as caught:
            plan(repo, fix, [])
        assert "admiring itself" in str(caught.value)


class TestExecution:
    def test_only_the_clean_verdict_lands(self):
        repo, fix = build()
        receipt = execute(
            repo,
            fix,
            ["release-2.0", "release-1.0", "release-1.1"],
        )
        assert receipt.startswith(
            "landed on 1 branch(es): release-1.1"
        )
        assert "2 left with their verdicts" in receipt
        tip = repo.refs.branches["release-1.1"]
        files = repo.files_at(tip)
        assert files["app.py"] == b"core\nfixed\n"
        assert files["lib.py"] == b"lib\n"
        message = repo.graph.get(tip).message
        assert message.startswith(
            "fix: stop the crash on empty input"
        )
        assert "backported from" in message

    def test_the_narration_reads_as_a_ward_round(self):
        repo, fix = build()
        page = narrate(
            repo, fix, ["release-1.0", "release-1.1"]
        )
        assert page.startswith("backport of ")
        assert "oldest patient first:" in page
        assert "release-1.1: applies cleanly" in page
        assert "release-1.0: diverged" in page

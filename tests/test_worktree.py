from __future__ import annotations

import pytest

from keel.errors import Conflict
from keel.repo import Repo
from keel.worktree import checkout, plan_checkout

MAIN_FILES = {"app.py": b"main version", "keep.txt": b"same"}
TOPIC_FILES = {
    "app.py": b"topic version",
    "keep.txt": b"same",
    "topic.txt": b"new",
}


def two_branches() -> Repo:
    repo = Repo.init()
    repo.commit(dict(MAIN_FILES), "on main")
    repo.branch_from_head("topic")
    repo.refs.checkout("topic")
    repo.commit(dict(TOPIC_FILES), "on topic")
    repo.refs.checkout("main")
    return repo


class TestPlanning:
    def test_the_three_sets_are_computed_before_touching(self):
        repo = two_branches()
        plan = plan_checkout(
            repo,
            dict(MAIN_FILES),
            repo.refs.branches["main"],
            repo.refs.branches["topic"],
        )
        assert plan.writes == ("app.py", "topic.txt")
        assert plan.deletions == ()
        assert plan.is_safe()

    def test_dirty_files_in_the_crossfire_are_dangers(self):
        repo = two_branches()
        working = dict(
            MAIN_FILES, **{"app.py": b"uncommitted edit"}
        )
        plan = plan_checkout(
            repo,
            working,
            repo.refs.branches["main"],
            repo.refs.branches["topic"],
        )
        assert plan.dangers == ("app.py",)

    def test_the_untracked_file_outranks_history(self):
        repo = two_branches()
        working = dict(
            MAIN_FILES, **{"topic.txt": b"my local notes"}
        )
        plan = plan_checkout(
            repo,
            working,
            repo.refs.branches["main"],
            repo.refs.branches["topic"],
        )
        assert "topic.txt" in plan.dangers


class TestSwitching:
    def test_the_clean_switch_lands_with_a_receipt(self):
        repo = two_branches()
        updated, receipt = checkout(
            repo, dict(MAIN_FILES), "topic"
        )
        assert updated["app.py"] == b"topic version"
        assert updated["topic.txt"] == b"new"
        assert "untracked files left standing" in receipt
        assert repo.refs.current_branch() == "topic"

    def test_the_dirty_switch_aborts_whole(self):
        repo = two_branches()
        working = dict(
            MAIN_FILES,
            **{
                "app.py": b"uncommitted",
                "scratch.md": b"untracked survives",
            },
        )
        with pytest.raises(Conflict) as caught:
            checkout(repo, working, "topic")
        assert "every casualty named: app.py" in str(
            caught.value
        )
        assert repo.refs.current_branch() == "main"

    def test_untracked_bystanders_survive_the_switch(self):
        repo = two_branches()
        working = dict(
            MAIN_FILES, **{"scratch.md": b"notes"}
        )
        updated, _ = checkout(repo, working, "topic")
        assert updated["scratch.md"] == b"notes"

    def test_a_matching_dirty_file_is_not_a_danger(self):
        repo = two_branches()
        working = dict(
            MAIN_FILES, **{"app.py": b"topic version"}
        )
        plan = plan_checkout(
            repo,
            working,
            repo.refs.branches["main"],
            repo.refs.branches["topic"],
        )
        assert plan.is_safe()

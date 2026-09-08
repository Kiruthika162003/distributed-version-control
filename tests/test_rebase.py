from __future__ import annotations

import pytest

from keel.errors import Conflict, Invalid
from keel.merge import commit_merge, merge_commits
from keel.rebase import rebase_branch
from keel.repo import Repo

BASE = {"app.py": b"one\ntwo\nthree", "docs.md": b"start"}


def diverged() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.branch_from_head("feature")
    repo.commit(
        dict(BASE, **{"docs.md": b"start\nmain grew"}),
        "main work",
    )
    repo.refs.checkout("feature")
    repo.commit(
        dict(BASE, **{"feat1.txt": b"first"}), "feature one"
    )
    repo.commit(
        dict(BASE, **{"feat1.txt": b"first", "feat2.txt": b"second"}),
        "feature two",
    )
    repo.refs.checkout("main")
    return repo


class TestReplay:
    def test_each_commit_becomes_a_small_story(self):
        repo = diverged()
        narration = rebase_branch(repo, "feature", "main")
        assert narration[0].startswith("replaying 2 commit(s)")
        assert "owns a divergence" in narration[0]
        assert narration[1].startswith("replayed ")
        assert narration[1].endswith("feature one")
        assert narration[-1].startswith("rebase complete: 2")

    def test_the_rebased_branch_carries_both_histories(self):
        repo = diverged()
        rebase_branch(repo, "feature", "main")
        repo.refs.checkout("feature")
        files = repo.head_files()
        assert files["docs.md"] == b"start\nmain grew"
        assert files["feat2.txt"] == b"second"

    def test_every_address_changes_and_the_move_is_forced(self):
        repo = diverged()
        old_tip = repo.refs.branches["feature"]
        rebase_branch(repo, "feature", "main")
        assert repo.refs.branches["feature"] != old_tip
        assert "force-moved" in repo.refs.reflog[-1]


class TestStops:
    def test_the_conflict_names_the_commit_and_the_queue(self):
        repo = Repo.init()
        repo.commit(dict(BASE), "base")
        repo.branch_from_head("feature")
        repo.commit(
            dict(BASE, **{"app.py": b"MAIN\ntwo\nthree"}),
            "main edit",
        )
        repo.refs.checkout("feature")
        repo.commit(
            dict(BASE, **{"app.py": b"FEATURE\ntwo\nthree"}),
            "feature edit",
        )
        repo.commit(
            dict(
                BASE,
                **{
                    "app.py": b"FEATURE\ntwo\nthree",
                    "later.txt": b"queued",
                },
            ),
            "queued work",
        )
        with pytest.raises(Conflict) as caught:
            rebase_branch(repo, "feature", "main")
        story = str(caught.value)
        assert "stopped at" in story
        assert "conflict in app.py" in story
        assert "1 commit(s) still queued behind it" in story

    def test_a_fast_forward_is_not_a_rebase(self):
        repo = Repo.init()
        repo.commit(dict(BASE), "base")
        repo.branch_from_head("feature")
        repo.commit(
            dict(BASE, **{"x.txt": b"x"}), "main moves on"
        )
        with pytest.raises(Invalid) as caught:
            rebase_branch(repo, "feature", "main")
        assert "a fast-forward, not a rebase" in str(caught.value)

    def test_merges_are_not_replayed_by_design(self):
        repo = diverged()
        left = repo.refs.branches["main"]
        right = repo.refs.branches["feature"]
        outcome = merge_commits(repo, left, right)
        commit_merge(repo, outcome, "merge feature into main")
        with pytest.raises(Invalid) as caught:
            rebase_branch(repo, "main", "feature")
        assert "flattens a decision someone made" in str(
            caught.value
        )

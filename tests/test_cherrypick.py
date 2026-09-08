from __future__ import annotations

import pytest

from keel.cherrypick import cherry_pick, revert
from keel.errors import Conflict, Invalid
from keel.merge import commit_merge, merge_commits
from keel.repo import Repo

BASE = {"app.py": b"stable", "hotfix.txt": b"old"}


def repo_with_fix() -> tuple[Repo, str]:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.branch_from_head("release")
    fix = repo.commit(
        dict(BASE, **{"hotfix.txt": b"patched"}), "the fix"
    ).address
    repo.refs.checkout("release")
    repo.commit(
        dict(BASE, **{"app.py": b"release work"}),
        "release work",
    )
    return repo, fix


class TestCherryPick:
    def test_the_fix_moves_with_its_provenance(self):
        repo, fix = repo_with_fix()
        picked = cherry_pick(repo, fix)
        assert "cherry-picked from" in picked.message
        files = repo.head_files()
        assert files["hotfix.txt"] == b"patched"
        assert files["app.py"] == b"release work"

    def test_moved_ground_stops_the_pick(self):
        repo, fix = repo_with_fix()
        repo.commit(
            dict(
                BASE,
                **{
                    "app.py": b"release work",
                    "hotfix.txt": b"drifted",
                },
            ),
            "release touched the same file",
        )
        with pytest.raises(Conflict) as caught:
            cherry_pick(repo, fix)
        assert "the ground moved under hotfix.txt" in str(
            caught.value
        )
        assert "this machine does not" in str(caught.value)

    def test_merges_do_not_cherry_pick(self):
        repo, _fix = repo_with_fix()
        outcome = merge_commits(
            repo,
            repo.refs.branches["release"],
            repo.refs.branches["main"],
        )
        merged = commit_merge(repo, outcome, "merge main")
        with pytest.raises(Invalid):
            cherry_pick(repo, merged.address)


class TestRevert:
    def test_the_revert_unmakes_and_names_its_target(self):
        repo = Repo.init()
        repo.commit(dict(BASE), "base")
        bad = repo.commit(
            dict(BASE, **{"app.py": b"regression"}),
            "bad change",
        )
        undone = revert(repo, bad.address)
        assert undone.message.startswith("Revert: bad change")
        assert repo.head_files()["app.py"] == b"stable"

    def test_reverting_a_merge_needs_a_mainline(self):
        repo, _ = repo_with_fix()
        outcome = merge_commits(
            repo,
            repo.refs.branches["release"],
            repo.refs.branches["main"],
        )
        merged = commit_merge(repo, outcome, "merge main")
        with pytest.raises(Invalid) as caught:
            revert(repo, merged.address)
        assert "nobody has ever wanted that twice" in str(
            caught.value
        )

    def test_reverting_under_moved_ground_stops(self):
        repo = Repo.init()
        repo.commit(dict(BASE), "base")
        bad = repo.commit(
            dict(BASE, **{"app.py": b"regression"}),
            "bad change",
        )
        repo.commit(
            dict(BASE, **{"app.py": b"rebuilt since"}),
            "later rewrite",
        )
        with pytest.raises(Conflict):
            revert(repo, bad.address)

from __future__ import annotations

import pytest

from keel.cherrypick import cherry_pick
from keel.errors import Invalid
from keel.merge import commit_merge, merge_commits
from keel.patchid import cherry_report, narrate_cherry, patch_id
from keel.repo import Repo

BASE = {"app.py": b"stable", "lib.py": b"quiet"}


def picked_landscape() -> tuple[Repo, str, str]:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.branch_from_head("release")
    fix = repo.commit(
        dict(BASE, **{"app.py": b"fixed"}), "the fix"
    ).address
    extra = repo.commit(
        dict(
            BASE,
            **{"app.py": b"fixed", "lib.py": b"tuned"},
        ),
        "the tuning",
    ).address
    repo.refs.checkout("release")
    cherry_pick(repo, fix)
    return repo, fix, extra


class TestTheId:
    def test_the_same_change_shares_an_id_across_addresses(self):
        repo, fix, _ = picked_landscape()
        picked_tip = repo.refs.branches["release"]
        assert picked_tip != fix
        assert patch_id(repo, picked_tip) == patch_id(repo, fix)

    def test_different_changes_have_different_ids(self):
        repo, fix, extra = picked_landscape()
        assert patch_id(repo, fix) != patch_id(repo, extra)

    def test_the_id_is_blind_on_merges_by_design(self):
        repo, _, _ = picked_landscape()
        outcome = merge_commits(
            repo,
            repo.refs.branches["release"],
            repo.refs.branches["main"],
        )
        merged = commit_merge(repo, outcome, "land main")
        with pytest.raises(Invalid) as caught:
            patch_id(repo, merged.address)
        assert "changes with the question" in str(caught.value)


class TestCherry:
    def test_landed_and_pending_split_by_identity(self):
        repo, _, _extra = picked_landscape()
        report = cherry_report(
            repo,
            repo.refs.branches["main"],
            repo.refs.branches["release"],
        )
        landed_msgs = [
            repo.graph.get(a).message
            for a in report["landed"]
        ]
        pending_msgs = [
            repo.graph.get(a).message
            for a in report["pending"]
        ]
        assert landed_msgs == ["the fix"]
        assert pending_msgs == ["the tuning"]

    def test_the_narration_answers_the_release_manager(self):
        repo, _, _ = picked_landscape()
        story = narrate_cherry(
            repo,
            repo.refs.branches["main"],
            repo.refs.branches["release"],
        )
        assert story.startswith(
            "1 landed upstream under other addresses, 1 pending"
        )
        assert "- " in story and "+ " in story

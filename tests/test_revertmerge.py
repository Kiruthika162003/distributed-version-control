from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.merge import commit_merge, merge_commits
from keel.repo import Repo
from keel.revertmerge import remerge_warning, revert_merge

BASE = {"core.py": b"shared", "docs.md": b"start"}


def merged_world() -> tuple[Repo, str, str]:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.branch_from_head("feature")
    repo.refs.checkout("feature")
    branch_tip = repo.commit(
        dict(BASE, **{"feature.py": b"the feature"}),
        "build the feature",
    ).address
    repo.refs.checkout("main")
    repo.commit(
        dict(BASE, **{"docs.md": b"start\nmain"}),
        "main moves",
    )
    outcome = merge_commits(
        repo, repo.refs.branches["main"], branch_tip
    )
    merge = commit_merge(repo, outcome, "land the feature")
    return repo, merge.address, branch_tip


class TestTheRevert:
    def test_mainline_one_backs_out_the_feature(self):
        repo, merge_address, _ = merged_world()
        commit, receipt = revert_merge(
            repo, merge_address, mainline=1
        )
        files = repo.files_at(commit.address)
        assert "feature.py" not in files
        assert files["docs.md"] == b"start\nmain"
        assert "FLAG:" in receipt
        assert "revert the revert first" in receipt

    def test_the_mainline_is_demanded_explicitly(self):
        repo, merge_address, _ = merged_world()
        with pytest.raises(Invalid) as caught:
            revert_merge(repo, merge_address, mainline=5)
        assert "aiming at the feature" in str(caught.value)

    def test_ordinary_commits_use_a_different_tool(self):
        repo, _, branch_tip = merged_world()
        with pytest.raises(Invalid) as caught:
            revert_merge(repo, branch_tip, mainline=1)
        assert "a different tool" in str(caught.value)


class TestTheLandmine:
    def test_the_warning_names_the_eaten_changes(self):
        repo, merge_address, branch_tip = merged_world()
        revert_merge(repo, merge_address, mainline=1)
        warning = remerge_warning(
            repo,
            repo.refs.branches["main"],
            branch_tip,
        )
        assert "merging again brings back nothing" in warning

    def test_fresh_branch_commits_lift_the_warning(self):
        repo, merge_address, _ = merged_world()
        revert_merge(repo, merge_address, mainline=1)
        repo.refs.checkout("feature")
        fresh = repo.commit(
            dict(
                BASE,
                **{"feature.py": b"the feature, revived"},
            ),
            "revive",
        ).address
        repo.refs.checkout("main")
        assert "a merge will carry them" in remerge_warning(
            repo, repo.refs.branches["main"], fresh
        )

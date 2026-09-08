from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.rangediff import narrate_range_diff, range_diff
from keel.rebase import rebase_branch
from keel.repo import Repo

BASE = {"app.py": b"core", "docs.md": b"start"}


def rebased_world() -> tuple[Repo, str, str, str]:
    repo = Repo.init()
    base = repo.commit(dict(BASE), "base").address
    repo.branch_from_head("feature")
    repo.commit(
        dict(BASE, **{"docs.md": b"start\nmain"}),
        "main work",
    )
    repo.refs.checkout("feature")
    repo.commit(
        dict(BASE, **{"one.txt": b"first"}), "patch one"
    )
    repo.commit(
        dict(BASE, **{"one.txt": b"first", "two.txt": b"second"}),
        "patch two",
    )
    old_tip = repo.refs.branches["feature"]
    main_tip = repo.refs.branches["main"]
    rebase_branch(repo, "feature", "main")
    new_tip = repo.refs.branches["feature"]
    return repo, old_tip, new_tip, base, main_tip


class TestBuckets:
    def test_the_intact_rebase_survives_by_patch_id(self):
        repo, old_tip, new_tip, base, main_tip = (
            rebased_world()
        )
        buckets = range_diff(
            repo, old_tip, new_tip, base, main_tip
        )
        assert len(buckets["survived"]) == 2
        assert buckets["modified"] == []
        assert buckets["dropped"] == []
        assert buckets["added"] == []

    def test_the_edited_patch_lands_in_the_reread_bucket(self):
        repo, old_tip, _, base, _main = rebased_world()
        repo.refs.create_branch("v2", base)
        repo.refs.checkout("v2")
        repo.commit(
            dict(BASE, **{"one.txt": b"first EDITED"}),
            "patch one",
        )
        repo.commit(
            dict(
                BASE,
                **{
                    "one.txt": b"first EDITED",
                    "two.txt": b"second",
                },
            ),
            "patch two",
        )
        new_tip = repo.refs.branches["v2"]
        buckets = range_diff(
            repo, old_tip, new_tip, base, base
        )
        assert len(buckets["survived"]) == 1
        assert any(
            "paired by message, the weaker hint" in entry
            for entry in buckets["modified"]
        )

    def test_merges_compare_as_themselves(self):
        repo, old_tip, _, base, _main = rebased_world()
        with pytest.raises(Invalid):
            range_diff(repo, base, old_tip, old_tip, base)


class TestNarration:
    def test_the_gradient_of_surprise_is_stated(self):
        repo, old_tip, new_tip, base, main_tip = (
            rebased_world()
        )
        story = narrate_range_diff(
            repo, old_tip, new_tip, base, main_tip
        )
        assert story.startswith("2 survived, 0 modified")
        assert "gradient of surprise" in story

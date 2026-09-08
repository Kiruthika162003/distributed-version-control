from __future__ import annotations

import pytest

from keel.errors import Conflict, Invalid
from keel.octopus import describe_octopus, octopus_merge
from keel.repo import Repo

BASE = {"core.py": b"shared", "docs.md": b"start"}


def three_topics() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    for name, path in (
        ("topic-a", "a.txt"),
        ("topic-b", "b.txt"),
        ("topic-c", "c.txt"),
    ):
        repo.branch_from_head(name)
        repo.refs.checkout(name)
        repo.commit(
            dict(BASE, **{path: b"topic work"}),
            f"work on {name}",
        )
        repo.refs.checkout("main")
    return repo


class TestTheFold:
    def test_three_clean_topics_land_as_one_commit(self):
        repo = three_topics()
        merged = octopus_merge(
            repo,
            ["topic-a", "topic-b", "topic-c"],
            "land the batch",
        )
        assert len(merged.parents) == 4
        files = repo.head_files()
        assert files["a.txt"] == b"topic work"
        assert files["c.txt"] == b"topic work"

    def test_parent_order_records_the_fold(self):
        repo = three_topics()
        merged = octopus_merge(
            repo,
            ["topic-b", "topic-a", "topic-c"],
            "land the batch",
        )
        assert merged.parents[1] == (
            repo.refs.branches["topic-b"]
        )
        assert "only narrative an octopus has" in (
            describe_octopus(repo, merged.address)
        )

    def test_one_head_is_a_costume(self):
        repo = three_topics()
        with pytest.raises(Invalid) as caught:
            octopus_merge(repo, ["topic-a"], "solo")
        assert "wearing a costume" in str(caught.value)


class TestTheRefusal:
    def test_the_first_conflict_stops_and_prescribes(self):
        repo = Repo.init()
        repo.commit(dict(BASE), "base")
        for name, content in (
            ("left", b"LEFT"),
            ("right", b"RIGHT"),
        ):
            repo.branch_from_head(name)
            repo.refs.checkout(name)
            repo.commit(
                dict(BASE, **{"core.py": content}),
                f"{name} edits core",
            )
            repo.refs.checkout("main")
        with pytest.raises(Conflict) as caught:
            octopus_merge(
                repo, ["left", "right"], "doomed batch"
            )
        message = str(caught.value)
        assert "the octopus stops at right" in message
        assert "the fold of [left]" in message
        assert "merge right alone first" in message

    def test_the_two_parent_commit_is_not_an_octopus(self):
        repo = three_topics()
        assert "not an octopus" in describe_octopus(
            repo, repo.refs.current()
        )

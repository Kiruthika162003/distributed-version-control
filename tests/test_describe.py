from __future__ import annotations

from keel.describe import describe, describe_head
from keel.repo import Repo
from keel.tags import TagStore

BASE = {"a.txt": b"v"}


def storied() -> tuple[Repo, TagStore, str]:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    tagged = repo.commit(
        dict(BASE, **{"a.txt": b"v1.4"}), "the release"
    ).address
    tags = TagStore(graph=repo.graph)
    tags.place("v1.4", tagged, "shipped")
    repo.commit(dict(BASE, **{"a.txt": b"post1"}), "after 1")
    repo.commit(dict(BASE, **{"a.txt": b"post2"}), "after 2")
    return repo, tags, tagged


class TestDescribe:
    def test_the_tagged_commit_is_exact(self):
        repo, tags, tagged = storied()
        assert describe(repo, tags, tagged) == "exactly v1.4"

    def test_the_distance_counts_first_parent_steps(self):
        repo, tags, _ = storied()
        verdict = describe_head(repo, tags)
        assert verdict.startswith("v1.4+2 (")
        assert "how far into it" in verdict

    def test_the_untagged_era_admits_it(self):
        repo = Repo.init()
        repo.commit(dict(BASE), "young")
        tags = TagStore(graph=repo.graph)
        verdict = describe_head(repo, tags)
        assert "no tagged ancestor" in verdict
        assert "confidently and wrongly" in verdict

    def test_the_nearest_tag_wins_over_the_older_one(self):
        repo, tags, _ = storied()
        newer = repo.refs.current()
        tags.place("v1.5", newer, "next release")
        assert describe_head(repo, tags) == "exactly v1.5"

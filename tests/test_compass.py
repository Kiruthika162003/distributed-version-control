from __future__ import annotations

import pytest

from keel.compass import orient
from keel.errors import Missing
from keel.repo import Repo
from keel.tags import TagStore

BASE = {"app.py": b"core\n"}


def build() -> tuple[Repo, list[str], TagStore]:
    repo = Repo.init()
    first = repo.commit(dict(BASE), "the shared past")
    repo.branch_from_head("feature")
    second = repo.commit(
        dict(BASE, **{"app.py": b"core\nmain\n"}),
        "main moves",
    )
    tags = TagStore(graph=repo.graph)
    tags.place("v1.0", second.address, "the cut")
    return (
        repo,
        [first.address, second.address],
        tags,
    )


class TestOrientation:
    def test_carriers_sort_by_distance(self):
        repo, addresses, tags = build()
        page = orient(repo, addresses[0], tags)
        lines = page.splitlines()
        assert lines[1] == (
            "  carried by feature, at the tip"
        )
        assert lines[2] == (
            "  carried by main, 1 commit(s) below "
            "the tip"
        )

    def test_eras_are_named(self):
        repo, addresses, tags = build()
        page = orient(repo, addresses[0], tags)
        assert (
            "part of the era(s) sealed by v1.0"
        ) in page
        tip_page = orient(repo, addresses[1], tags)
        assert "carried by main, at the tip" in tip_page

    def test_the_wanderer_is_sent_to_lost_and_found(
        self,
    ):
        repo, addresses, tags = build()
        repo.refs.move(
            "main",
            addresses[0],
            reason="reset away",
            force=True,
        )
        repo.refs.reflog.clear()
        page = orient(repo, addresses[1], tags)
        assert "reachable from no name; wandering" in (
            page
        )
        assert "lost and found" in page

    def test_a_stranger_cannot_be_oriented(self):
        repo, _addresses, _tags = build()
        with pytest.raises(Missing):
            orient(repo, "0" * 20)

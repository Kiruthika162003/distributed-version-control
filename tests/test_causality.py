from __future__ import annotations

import pytest

from keel.causality import enforce, scars
from keel.commits import Commit
from keel.errors import Corrupt
from keel.gc import Collector
from keel.repo import Repo


def build() -> Repo:
    repo = Repo.init()
    text = b""
    for step in range(5):
        text += f"{step}\n".encode()
        repo.commit({"log.txt": text}, f"step {step}")
    return repo


class TestTheArrow:
    def test_an_honest_graph_obeys(self):
        repo = build()
        assert enforce(repo) == (
            "5 commit(s) obey the arrow of time"
        )

    def test_a_time_traveler_stops_the_audit(self):
        repo = build()
        tip = repo.refs.current()
        honest = repo.graph.get(tip)
        repo.graph.commits[tip] = Commit(
            address=honest.address,
            tree=honest.tree,
            parents=honest.parents,
            message=honest.message,
            sequence=0,
        )
        with pytest.raises(Corrupt) as caught:
            enforce(repo)
        message = str(caught.value)
        assert "arrow-of-time violation(s)" in message
        assert (
            "a corruption, not an anomaly"
        ) in message


class TestTheScars:
    def test_an_unbroken_history_says_so(self):
        repo = build()
        assert scars(repo) == (
            "5 commit(s), sequences unbroken; nothing "
            "has been let go"
        )

    def test_collections_leave_countable_scars(self):
        repo = build()
        second = next(
            commit
            for commit in repo.graph.commits.values()
            if commit.sequence == 1
        )
        repo.refs.move(
            "main",
            second.address,
            reason="reset far back",
            force=True,
        )
        collector = Collector(repo=repo)
        collector.trim_reflog(keep_last=1)
        repo.commit(
            {"log.txt": b"0\n1\nnew\n"}, "new line"
        )
        collector.trim_reflog(keep_last=1)
        collector.collect()
        page = scars(repo)
        assert "digested and let go (2-4)" in page
        assert "scars are history, not findings" in page

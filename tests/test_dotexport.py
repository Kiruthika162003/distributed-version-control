from __future__ import annotations

import pytest

from keel.dotexport import export_dot
from keel.errors import Invalid
from keel.repo import Repo
from keel.tags import TagStore

BASE = {"a.txt": b"v"}


def storied() -> tuple[Repo, TagStore]:
    repo = Repo.init()
    repo.commit(dict(BASE), "base commit")
    tagged = repo.commit(
        dict(BASE, **{"a.txt": b"r"}), "the release"
    ).address
    tags = TagStore(graph=repo.graph)
    tags.place("v1.0", tagged, "shipped")
    repo.commit(dict(BASE, **{"a.txt": b"x"}), "after")
    return repo, tags


class TestTheDrawing:
    def test_edges_point_backward_and_names_decorate(self):
        repo, tags = storied()
        dot = export_dot(repo, repo.refs.current(), tags)
        assert "digraph history {" in dot
        assert "[main]" in dot
        assert "<v1.0>" in dot
        assert dot.count("->") == 2

    def test_messages_truncate_and_quotes_escape(self):
        repo = Repo.init()
        repo.commit(
            dict(BASE), 'say "hello" ' + "x" * 60
        )
        dot = export_dot(repo, repo.refs.current())
        assert "'hello'" in dot
        assert "x" * 41 not in dot


class TestTheBudget:
    def test_truncation_never_masquerades_as_the_root(self):
        repo = Repo.init()
        for number in range(8):
            repo.commit(
                {"a.txt": f"v{number}".encode()}, f"c{number}"
            )
        dot = export_dot(
            repo, repo.refs.current(), node_budget=3
        )
        assert "5 older commit(s) cut by the budget" in dot
        assert "not the root" in dot
        assert '-> "beyond"' in dot

    def test_a_dot_is_not_a_graph(self):
        repo, _ = storied()
        with pytest.raises(Invalid):
            export_dot(
                repo, repo.refs.current(), node_budget=1
            )

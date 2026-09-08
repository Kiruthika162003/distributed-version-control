from __future__ import annotations

import pytest

from keel.errors import Conflict, Invalid
from keel.repo import Repo
from keel.transplant import gather, transplant

BASE = {
    "search.py": b"s0\n",
    "auth.py": b"a0\n",
    "docs.md": b"d0\n",
}


def build() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    repo.branch_from_head("release")
    files = dict(BASE)
    files["search.py"] = b"s1\n"
    repo.commit(dict(files), "[search] index the titles")
    files["auth.py"] = b"a1\n"
    repo.commit(dict(files), "harden the tokens")
    files["search.py"] = b"s1\ns2\n"
    repo.commit(dict(files), "[search] rank the results")
    return repo


class TestGathering:
    def test_the_topic_is_gathered_in_order(self):
        repo = build()
        members = gather(repo, "main", "[search]")
        assert [
            member.message for member in members
        ] == [
            "[search] index the titles",
            "[search] rank the results",
        ]

    def test_an_empty_marker_is_not_a_topic(self):
        repo = build()
        with pytest.raises(Invalid):
            gather(repo, "main", "  ")


class TestTransplanting:
    def test_the_topic_moves_whole_with_origins(self):
        repo = build()
        receipt = transplant(
            repo, "main", "release", "[search]"
        )
        assert receipt.startswith(
            "transplanted 2 commit(s) carrying "
            "'[search]'"
        )
        tip = repo.refs.branches["release"]
        files = repo.files_at(tip)
        assert files["search.py"] == b"s1\ns2\n"
        assert files["auth.py"] == b"a0\n"
        message = repo.graph.get(tip).message
        assert message.startswith(
            "[search] rank the results"
        )
        assert "transplanted from" in message

    def test_divergence_refuses_the_whole_topic(self):
        repo = build()
        repo.refs.checkout("release")
        release_files = dict(BASE)
        release_files["search.py"] = b"release own\n"
        repo.commit(
            dict(release_files),
            "release touched search first",
        )
        repo.refs.checkout("main")
        before = repo.refs.branches["release"]
        with pytest.raises(Conflict) as caught:
            transplant(
                repo, "main", "release", "[search]"
            )
        message = str(caught.value)
        assert "refused whole" in message
        assert "finds search.py diverged" in message
        assert repo.refs.branches["release"] == before

    def test_a_topicless_transplant_is_refused(self):
        repo = build()
        with pytest.raises(Invalid) as caught:
            transplant(
                repo, "main", "release", "[billing]"
            )
        assert "needs a topic to move" in str(
            caught.value
        )

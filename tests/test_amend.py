from __future__ import annotations

import pytest

from keel.amend import amend, squash
from keel.errors import Invalid
from keel.repo import Repo

BASE = {"a.txt": b"v1"}


def seeded() -> Repo:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    return repo


class TestAmend:
    def test_the_old_tip_lands_in_the_reflog_first(self):
        repo = seeded()
        old_tip = repo.refs.current()
        amend(repo, message="base, but spelled right")
        assert repo.refs.current() != old_tip
        assert any(
            old_tip[:8] in entry
            for entry in repo.refs.reflog
        )

    def test_amending_nothing_is_cosplay(self):
        with pytest.raises(Invalid) as caught:
            amend(seeded())
        assert "cosplaying as work" in str(caught.value)

    def test_published_tips_need_a_signature(self):
        repo = seeded()
        tip = repo.refs.current()
        with pytest.raises(Invalid) as caught:
            amend(
                repo,
                message="rewrite",
                pushed_tips={tip},
            )
        assert "a signature on a form" in str(caught.value)
        amended = amend(
            repo,
            message="rewrite",
            pushed_tips={tip},
            published_anyway=True,
        )
        assert amended.message == "rewrite"

    def test_amending_files_keeps_the_parents(self):
        repo = seeded()
        repo.commit(dict(BASE, **{"b.txt": b"x"}), "second")
        old = repo.graph.get(repo.refs.current())
        amended = amend(
            repo, files={"a.txt": b"v1", "b.txt": b"fixed"}
        )
        assert amended.parents == old.parents
        assert repo.head_files()["b.txt"] == b"fixed"


class TestSquash:
    def test_the_fold_keeps_place_and_newest_tree(self):
        repo = seeded()
        repo.commit(dict(BASE, **{"a.txt": b"v2"}), "wip 1")
        repo.commit(dict(BASE, **{"a.txt": b"v3"}), "wip 2")
        folded = squash(repo, count=2)
        assert repo.head_files()["a.txt"] == b"v3"
        assert folded.message.startswith("wip 1")
        assert "folded: wip 2" in folded.message
        assert len(repo.graph.get(
            folded.address
        ).parents) == 1

    def test_mystery_meat_is_prevented_by_the_message(self):
        repo = seeded()
        repo.commit(dict(BASE, **{"a.txt": b"v2"}), "wip 1")
        repo.commit(dict(BASE, **{"a.txt": b"v3"}), "wip 2")
        folded = squash(repo, count=2, message="feature done")
        assert folded.message == "feature done"

    def test_one_commit_is_the_wrong_tool(self):
        with pytest.raises(Invalid) as caught:
            squash(seeded(), count=1)
        assert "use the right tool" in str(caught.value)

    def test_the_root_bounds_the_fold(self):
        repo = seeded()
        repo.commit(dict(BASE, **{"a.txt": b"v2"}), "second")
        with pytest.raises(Invalid) as caught:
            squash(repo, count=5)
        assert "above the root" in str(caught.value)

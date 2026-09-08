from __future__ import annotations

import pytest

from keel.autostash import with_autostash
from keel.errors import Conflict
from keel.repo import Repo
from keel.stash import Stash

BASE = {"a.py": b"alpha\n", "b.py": b"beta\n"}


def build() -> tuple[Repo, Stash]:
    repo = Repo.init()
    repo.commit(dict(BASE), "base")
    return repo, Stash()


class TestCleanCopies:
    def test_a_clean_copy_skips_the_shelf_and_says_so(
        self,
    ):
        repo, shelf = build()

        def operation() -> str:
            repo.commit(
                dict(BASE, **{"b.py": b"beta\nmore\n"}),
                "advance b",
            )
            return "advanced b"

        outcome = with_autostash(
            repo, shelf, dict(BASE), operation
        )
        assert outcome.receipt.startswith(
            "clean copy, no shelf needed"
        )
        assert "advanced b" in outcome.receipt
        assert shelf.entries == []
        assert outcome.files["b.py"] == b"beta\nmore\n"


class TestTheDance:
    def test_dirty_work_survives_a_disjoint_operation(
        self,
    ):
        repo, shelf = build()
        working = dict(
            BASE,
            **{
                "a.py": b"alpha\nhalf-done\n",
                "c.py": b"new file\n",
            },
        )

        def operation() -> str:
            repo.commit(
                dict(BASE, **{"b.py": b"beta\nmore\n"}),
                "advance b",
            )
            return "advanced b"

        outcome = with_autostash(
            repo, shelf, working, operation
        )
        assert outcome.files["a.py"] == (
            b"alpha\nhalf-done\n"
        )
        assert outcome.files["b.py"] == b"beta\nmore\n"
        assert outcome.files["c.py"] == b"new file\n"
        assert shelf.entries == []
        assert "one intention, one receipt" in (
            outcome.receipt
        )

    def test_a_local_deletion_stays_deleted(self):
        repo, shelf = build()
        working = {"a.py": b"alpha\n"}

        def operation() -> str:
            repo.commit(
                dict(BASE, **{"a.py": b"alpha\nop\n"}),
                "advance a",
            )
            return "advanced a"

        outcome = with_autostash(
            repo, shelf, working, operation
        )
        assert "b.py" not in outcome.files
        assert outcome.files["a.py"] == b"alpha\nop\n"


class TestTheRefusal:
    def test_a_collision_keeps_the_shelf_and_names_paths(
        self,
    ):
        repo, shelf = build()
        working = dict(
            BASE, **{"a.py": b"alpha\nhalf-done\n"}
        )

        def operation() -> str:
            repo.commit(
                dict(BASE, **{"a.py": b"alpha\nop\n"}),
                "advance a",
            )
            return "advanced a"

        with pytest.raises(Conflict) as caught:
            with_autostash(repo, shelf, working, operation)
        message = str(caught.value)
        assert "rewrote a.py under the shelf" in message
        assert "the work stays shelved" in message
        assert len(shelf.entries) == 1
        assert shelf.entries[0].label == (
            "autostash of 1 dirty path(s)"
        )

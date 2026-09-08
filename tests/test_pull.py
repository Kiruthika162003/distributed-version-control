from __future__ import annotations

import pytest

from keel.errors import Conflict, Invalid
from keel.pull import pull
from keel.push import PushGate
from keel.remotes import RemoteSet
from keel.repo import Repo

BASE = {"a.py": b"a1\n", "b.py": b"b1\n"}


def build():
    shared = Repo.init()
    alice = Repo.init()
    alice.commit(dict(BASE), "c1")
    gate = PushGate(remote=shared)
    gate.push(alice, "main")
    local = Repo.init()
    remotes = RemoteSet(local=local)
    remotes.add("origin", shared)
    return shared, alice, gate, local, remotes


class TestSimplePulls:
    def test_adoption_current_and_fast_forward(self):
        _shared, alice, gate, local, remotes = build()
        first = pull(
            local, remotes, "origin", "main", "ff_only"
        )
        assert first.startswith("[ff_only] main adopted")
        again = pull(
            local, remotes, "origin", "main", "ff_only"
        )
        assert "the fetch was the whole errand" in again
        alice.commit(
            dict(BASE, **{"a.py": b"a2\n"}), "c2"
        )
        gate.push(alice, "main")
        third = pull(
            local, remotes, "origin", "main", "ff_only"
        )
        assert (
            "[ff_only] main fast-forwarded by "
            "1 commit(s)"
        ) in third

    def test_an_invisible_policy_is_not_a_policy(self):
        _shared, _alice, _gate, local, remotes = build()
        with pytest.raises(Invalid) as caught:
            pull(local, remotes, "origin", "main", "")
        assert "invisible policies" in str(caught.value)


def diverge():
    shared, alice, gate, local, remotes = build()
    pull(local, remotes, "origin", "main", "ff_only")
    local.refs.checkout("main")
    local.commit(
        dict(BASE, **{"b.py": b"b2 local\n"}), "local b"
    )
    alice.commit(
        dict(BASE, **{"a.py": b"a2 remote\n"}), "remote a"
    )
    gate.push(alice, "main")
    return shared, alice, gate, local, remotes


class TestDivergence:
    def test_ff_only_refuses_with_the_numbers(self):
        _s, _a, _g, local, remotes = diverge()
        with pytest.raises(Conflict) as caught:
            pull(
                local, remotes, "origin", "main",
                "ff_only",
            )
        message = str(caught.value)
        assert "ahead 1 behind 1" in message
        assert "refuses to invent a merge" in message

    def test_ask_reports_and_takes_no_verb(self):
        _s, _a, _g, local, remotes = diverge()
        tip_before = local.refs.branches["main"]
        receipt = pull(
            local, remotes, "origin", "main", "ask"
        )
        assert receipt.startswith(
            "[ask] main has diverged, ahead 1 behind 1"
        )
        assert local.refs.branches["main"] == tip_before

    def test_merge_reconciles_in_one_commit(self):
        _s, _a, _g, local, remotes = diverge()
        receipt = pull(
            local, remotes, "origin", "main", "merge"
        )
        assert receipt.startswith(
            "[merge] main reconciled as"
        )
        files = local.files_at(
            local.refs.branches["main"]
        )
        assert files["a.py"] == b"a2 remote\n"
        assert files["b.py"] == b"b2 local\n"

    def test_a_conflicted_merge_hands_over_to_a_person(
        self,
    ):
        _shared, alice, gate, local, remotes = build()
        pull(local, remotes, "origin", "main", "ff_only")
        local.refs.checkout("main")
        local.commit(
            dict(BASE, **{"a.py": b"a2 local\n"}),
            "local a",
        )
        alice.commit(
            dict(BASE, **{"a.py": b"a2 remote\n"}),
            "remote a",
        )
        gate.push(alice, "main")
        with pytest.raises(Conflict) as caught:
            pull(
                local, remotes, "origin", "main",
                "merge",
            )
        message = str(caught.value)
        assert "conflicts on a.py" in message
        assert (
            "a person finishes what the policy started"
        ) in message

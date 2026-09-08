from __future__ import annotations

import pytest

from keel.errors import Invalid
from keel.push import PushGate
from keel.repo import Repo

BASE = {"a.txt": b"shared"}


def pair() -> tuple[PushGate, Repo, Repo]:
    remote = Repo.init()
    remote.commit(dict(BASE), "base")
    local = Repo.init()
    local.commit(dict(BASE), "base")
    return PushGate(remote=remote), local, remote


class TestPlainPush:
    def test_the_fast_forward_lands(self):
        gate, local, remote = pair()
        local.commit(dict(BASE, **{"b.txt": b"x"}), "ours")
        verdict = gate.push(local, "main")
        assert "fast-forwarded" in verdict
        assert remote.refs.branches["main"] == (
            local.refs.branches["main"]
        )

    def test_the_current_branch_ships_nothing(self):
        gate, local, _ = pair()
        assert "shipped nothing" in gate.push(local, "main")

    def test_the_non_ancestor_push_bounces(self):
        gate, local, remote = pair()
        remote.commit(dict(BASE, **{"r.txt": b"r"}), "theirs")
        local.commit(dict(BASE, **{"l.txt": b"l"}), "ours")
        with pytest.raises(Invalid) as caught:
            gate.push(local, "main")
        assert "someone may be standing on" in str(caught.value)
        assert len(gate.bounces) == 1

    def test_a_new_branch_is_created_remotely(self):
        gate, local, remote = pair()
        local.refs.create_branch(
            "topic", local.refs.current()
        )
        verdict = gate.push(local, "topic")
        assert "created on the remote" in verdict
        assert "topic" in remote.refs.branches


class TestForceAndLease:
    def test_the_bare_force_is_honest_about_the_reflog(self):
        gate, local, remote = pair()
        remote.commit(dict(BASE, **{"r.txt": b"r"}), "theirs")
        local.commit(dict(BASE, **{"l.txt": b"l"}), "ours")
        verdict = gate.push(local, "main", force=True)
        assert "FORCED" in verdict
        assert "survives only in the remote's reflog" in verdict

    def test_the_lease_bounces_the_race(self):
        gate, local, remote = pair()
        believed = remote.refs.branches["main"]
        remote.commit(
            dict(BASE, **{"r.txt": b"r"}), "colleague pushed"
        )
        local.commit(dict(BASE, **{"l.txt": b"l"}), "ours")
        with pytest.raises(Invalid) as caught:
            gate.push_with_lease(local, "main", believed)
        assert "someone pushed in your gap" in str(caught.value)
        assert "not a bigger hammer" in str(caught.value)

    def test_the_true_lease_lands_the_force(self):
        gate, local, remote = pair()
        believed = remote.refs.branches["main"]
        local.commit(dict(BASE, **{"l.txt": b"l"}), "ours")
        local.refs.move(
            "main",
            local.graph.get(
                local.refs.branches["main"]
            ).address,
            reason="hold",
        )
        verdict = gate.push_with_lease(local, "main", believed)
        assert "fast-forwarded" in verdict or "FORCED" in verdict

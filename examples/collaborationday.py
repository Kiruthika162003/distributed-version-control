"""A collaboration day: two people, one shared repository, no lost work.

Alice publishes, Bob fetches and builds on it, Alice pushes
into the gap and bounces, and the tools narrate every step:
the divergence report names the verb, the merge lands both
lines of work, and the broken lease catches Bob believing a
tip that moved. Run with: python -m examples.collaborationday
"""

from __future__ import annotations

from keel.errors import Invalid
from keel.merge import commit_merge, merge_commits
from keel.push import PushGate
from keel.remotes import RemoteSet
from keel.repo import Repo


def main() -> int:
    shared = Repo.init()
    gate = PushGate(remote=shared)

    alice = Repo.init()
    alice.commit(
        {"app.py": b"start\n", "notes.md": b"plan\n"},
        "first light",
    )
    alice.commit(
        {"app.py": b"start\nserve\n", "notes.md": b"plan\n"},
        "wire the server",
    )
    print(f"push:    {gate.push(alice, 'main')}")

    bob = Repo.init()
    bobs_remotes = RemoteSet(local=bob)
    bobs_remotes.add("origin", shared)
    print(f"fetch:   {bobs_remotes.fetch('origin')}")
    observed = bobs_remotes.remotes["origin"].observed["main"]
    bob.refs.create_branch("main", observed)
    bob.refs.checkout("main")
    bob_files = dict(bob.head_files())
    bob_files["tests.py"] = b"def test_serve(): ...\n"
    bob_tip = bob.commit(bob_files, "cover the server")
    print(f"push:    {gate.push(bob, 'main')}")

    alice_files = dict(alice.head_files())
    alice_files["app.py"] = b"start\nserve\nlog\n"
    alice.commit(alice_files, "log requests")
    try:
        gate.push(alice, "main")
    except Invalid as bounce:
        print(f"bounce:  {bounce}")

    alices_remotes = RemoteSet(local=alice)
    alices_remotes.add("origin", shared)
    alices_remotes.fetch("origin")
    print(
        "diverge: "
        + alices_remotes.divergence("main", "origin")
    )
    their_tip = (
        alices_remotes.remotes["origin"].observed["main"]
    )
    outcome = merge_commits(
        alice, alice.refs.branches["main"], their_tip
    )
    commit_merge(alice, outcome, "merge bob's coverage")
    print(f"push:    {gate.push(alice, 'main')}")

    try:
        gate.push_with_lease(bob, "main", bob_tip.address)
    except Invalid as broken:
        print(f"lease:   {broken}")
    print(f"fetch:   {bobs_remotes.fetch('origin')}")
    print(
        "diverge: "
        + bobs_remotes.divergence("main", "origin")
    )

    landing = shared.graph.get(shared.refs.branches["main"])
    print(
        f"shared:  main holds {landing.message!r} with "
        f"{len(landing.parents)} parents"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

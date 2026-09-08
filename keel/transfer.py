"""Transfer: want and have, and only the difference crosses the wire.

Fetching is a negotiation, not a download: the receiver names
the tips it wants and the tips it already has, the sender
computes the frontier, every object reachable from the wants
but not from the haves, and ships exactly that, because the
whole point of content addressing on a network is that both
sides can agree about what the other holds without shipping
anything to find out. The frontier walk collects commits,
their trees, and their blobs, deduplicating shared subtrees
on the way, and the receipt prices the negotiation: objects
shipped against objects the naive full clone would have sent.
Receiving verifies every object at its address before
admitting it, and a received object that fails its digest
poisons the whole batch, not just itself, because a sender
that ships one wrong object has forfeited the benefit of the
doubt on the rest.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Corrupt, Invalid
from keel.objects import COMMIT, ObjectStore, digest_bytes
from keel.repo import Repo


@dataclass
class TransferBatch:
    objects: dict[str, tuple[str, bytes]] = field(
        default_factory=dict
    )

    def size(self) -> int:
        return len(self.objects)


def _reachable_objects(repo: Repo, tip: str) -> set[str]:
    found: set[str] = set()
    for commit_address in repo.graph.ancestors(tip):
        found.add(commit_address)
        commit = repo.graph.get(commit_address)
        _collect_tree(repo, commit.tree, found)
    return found


def _collect_tree(
    repo: Repo, tree: str, found: set[str]
) -> None:
    if tree in found:
        return
    found.add(tree)
    for path, blob in repo.trees.read_tree(tree).items():
        del path
        found.add(blob)


def negotiate(
    sender: Repo, wants: list[str], haves: list[str]
) -> TransferBatch:
    if not wants:
        raise Invalid("a fetch that wants nothing is a ping")
    wanted: set[str] = set()
    for tip in wants:
        wanted |= _reachable_objects(sender, tip)
    held: set[str] = set()
    for tip in haves:
        if sender.store.has(tip):
            held |= _reachable_objects(sender, tip)
    frontier = wanted - held
    batch = TransferBatch()
    for address in frontier:
        kind = sender.store.kind_of(address)
        payload = sender.store.get(address)
        batch.objects[address] = (kind, payload)
    return batch


def receive(
    receiver: ObjectStore, batch: TransferBatch
) -> str:
    for address, (kind, payload) in batch.objects.items():
        if digest_bytes(kind, payload) != address:
            raise Corrupt(
                f"{address[:8]} arrived with different bytes; "
                "one wrong object poisons the whole batch, "
                "because that sender has forfeited the benefit "
                "of the doubt"
            )
    admitted = 0
    for address, (kind, payload) in batch.objects.items():
        if not receiver.has(address):
            receiver.put(kind, payload)
            admitted += 1
    return (
        f"{admitted} object(s) admitted, "
        f"{batch.size() - admitted} already held"
    )


def receipt(
    sender: Repo, wants: list[str], batch: TransferBatch
) -> str:
    full: set[str] = set()
    for tip in wants:
        full |= _reachable_objects(sender, tip)
    saved = len(full) - batch.size()
    commits = sum(
        1
        for kind, _ in batch.objects.values()
        if kind == COMMIT
    )
    return (
        f"shipped {batch.size()} object(s) "
        f"({commits} commit(s)) where a full clone ships "
        f"{len(full)}; the negotiation saved {saved}"
    )

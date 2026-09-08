"""The object store: content is its own address, and the address is checked twice.

Everything this system remembers, file contents, directory
shapes, commits, lives in one store keyed by the digest of its
own bytes. That single decision buys the three properties the
rest of the system leans on: identical content stored once
however many files share it, history that cannot be edited
without changing every address downstream, and equality checks
that cost one string comparison however large the objects. The
store verifies on both doors: a write returns the address it
actually stored, and a read re-digests the bytes before
handing them over, because a corrupt store that answers
quickly is worse than a dead one, and the read-side check is
the only audit that runs on every access instead of on the
night someone remembers to run it.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from keel.errors import Corrupt, Invalid, Missing

BLOB = "blob"
TREE = "tree"
COMMIT = "commit"
KINDS = (BLOB, TREE, COMMIT)


def digest_bytes(kind: str, payload: bytes) -> str:
    header = f"{kind}:{len(payload)}|".encode()
    return hashlib.sha256(header + payload).hexdigest()[:20]


@dataclass
class ObjectStore:
    objects: dict[str, tuple[str, bytes]] = field(
        default_factory=dict
    )
    writes: int = 0
    dedup_hits: int = 0

    def put(self, kind: str, payload: bytes) -> str:
        if kind not in KINDS:
            raise Invalid(
                f"{kind} is not a kind this store holds; the "
                f"menu is {', '.join(KINDS)}"
            )
        address = digest_bytes(kind, payload)
        if address in self.objects:
            self.dedup_hits += 1
            return address
        self.objects[address] = (kind, payload)
        self.writes += 1
        return address

    def get(self, address: str, expect: str | None = None) -> bytes:
        held = self.objects.get(address)
        if held is None:
            raise Missing(
                f"{address} is not in the store; either it was "
                "never written or someone is holding a stale "
                "address"
            )
        kind, payload = held
        if expect is not None and kind != expect:
            raise Invalid(
                f"{address} is a {kind}, not the {expect} the "
                "caller expected; addresses do not lie about "
                "kind"
            )
        if digest_bytes(kind, payload) != address:
            raise Corrupt(
                f"{address} no longer matches its own bytes; a "
                "corrupt store that answers quickly is worse "
                "than a dead one"
            )
        return payload

    def kind_of(self, address: str) -> str:
        held = self.objects.get(address)
        if held is None:
            raise Missing(f"{address} is not in the store")
        return held[0]

    def has(self, address: str) -> bool:
        return address in self.objects

    def ledger(self) -> str:
        return (
            f"{self.writes} object(s) stored, "
            f"{self.dedup_hits} duplicate write(s) collapsed "
            "by content addressing"
        )

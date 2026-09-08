"""Packfiles: near-identical blobs ship as instructions, not copies.

A history full of edited files is a history full of blobs
that differ by a few lines, and shipping each one whole pays
for the same bytes over and over. The pack stores a chosen
few as full bases and everything similar as a delta, a list
of copy-from-base and insert-literal instructions, and the
economics are measured per object: a delta is only kept when
it is actually smaller than the blob it encodes, because a
delta format applied religiously to incompressible pairs
produces packs larger than the naive store, a failure mode
with a long history in the wild. Chains are bounded: a delta
may point at a base which is itself a delta, but only to a
fixed depth, since reconstruction cost climbs with every
link and a pack that saved bytes by spending every reader's
time bought the wrong thing. Unpacking verifies the digest
of every reconstructed blob against its address, so a bug in
the delta encoder is caught at the door instead of shipped
into history.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Corrupt, Invalid
from keel.objects import BLOB, digest_bytes

MAX_CHAIN_DEPTH = 3
MIN_COPY_LENGTH = 8


@dataclass(frozen=True)
class CopyOp:
    offset: int
    length: int


@dataclass(frozen=True)
class InsertOp:
    payload: bytes


DeltaOp = CopyOp | InsertOp


def make_delta(base: bytes, target: bytes) -> list[DeltaOp]:
    ops: list[DeltaOp] = []
    index = 0
    pending: list[int] = []
    while index < len(target):
        best_offset = -1
        best_length = 0
        probe = target[index : index + MIN_COPY_LENGTH]
        if len(probe) == MIN_COPY_LENGTH:
            search_from = 0
            while True:
                found = base.find(probe, search_from)
                if found < 0:
                    break
                length = MIN_COPY_LENGTH
                while (
                    index + length < len(target)
                    and found + length < len(base)
                    and base[found + length]
                    == target[index + length]
                ):
                    length += 1
                if length > best_length:
                    best_offset = found
                    best_length = length
                search_from = found + 1
        if best_length >= MIN_COPY_LENGTH:
            if pending:
                ops.append(
                    InsertOp(payload=bytes(pending))
                )
                pending = []
            ops.append(
                CopyOp(offset=best_offset, length=best_length)
            )
            index += best_length
        else:
            pending.append(target[index])
            index += 1
    if pending:
        ops.append(InsertOp(payload=bytes(pending)))
    return ops


def apply_delta(base: bytes, ops: list[DeltaOp]) -> bytes:
    parts: list[bytes] = []
    for op in ops:
        if isinstance(op, CopyOp):
            if op.offset + op.length > len(base):
                raise Corrupt(
                    "a copy op reaches past its base; the "
                    "delta and the base disagree about history"
                )
            parts.append(
                base[op.offset : op.offset + op.length]
            )
        else:
            parts.append(op.payload)
    return b"".join(parts)


def delta_size(ops: list[DeltaOp]) -> int:
    total = 0
    for op in ops:
        if isinstance(op, CopyOp):
            total += 9
        else:
            total += 1 + len(op.payload)
    return total


@dataclass
class Pack:
    full: dict[str, bytes] = field(default_factory=dict)
    deltas: dict[str, tuple[str, tuple[DeltaOp, ...]]] = field(
        default_factory=dict
    )
    rejected_deltas: int = 0

    def _depth(self, address: str) -> int:
        depth = 0
        cursor = address
        while cursor in self.deltas:
            cursor = self.deltas[cursor][0]
            depth += 1
        return depth

    def add(
        self, payload: bytes, base_address: str | None = None
    ) -> str:
        address = digest_bytes(BLOB, payload)
        if address in self.full or address in self.deltas:
            return address
        if base_address is not None:
            if (
                base_address not in self.full
                and base_address not in self.deltas
            ):
                raise Invalid(
                    f"base {base_address[:8]} is not in this "
                    "pack; deltas point inward, never out"
                )
            if self._depth(base_address) >= MAX_CHAIN_DEPTH:
                base_address = None
        if base_address is not None:
            base = self.restore(base_address)
            ops = make_delta(base, payload)
            if delta_size(ops) < len(payload):
                self.deltas[address] = (
                    base_address,
                    tuple(ops),
                )
                return address
            self.rejected_deltas += 1
        self.full[address] = payload
        return address

    def restore(self, address: str) -> bytes:
        if address in self.full:
            payload = self.full[address]
        elif address in self.deltas:
            base_address, ops = self.deltas[address]
            base = self.restore(base_address)
            payload = apply_delta(base, list(ops))
        else:
            raise Invalid(
                f"{address[:8]} is not in this pack"
            )
        if digest_bytes(BLOB, payload) != address:
            raise Corrupt(
                f"{address[:8]} reconstructed to different "
                "bytes; the encoder bug is caught at the door "
                "instead of shipped into history"
            )
        return payload

    def stored_bytes(self) -> int:
        total = sum(
            len(payload) for payload in self.full.values()
        )
        for _, ops in self.deltas.values():
            total += delta_size(list(ops))
        return total

    def naive_bytes(self) -> int:
        total = sum(
            len(payload) for payload in self.full.values()
        )
        for address in self.deltas:
            total += len(self.restore(address))
        return total

    def ledger(self) -> str:
        saved = self.naive_bytes() - self.stored_bytes()
        return (
            f"{len(self.full)} full object(s), "
            f"{len(self.deltas)} delta(s), "
            f"{self.rejected_deltas} delta(s) rejected for "
            f"being larger than their blob; {saved} byte(s) "
            "saved against the naive store"
        )

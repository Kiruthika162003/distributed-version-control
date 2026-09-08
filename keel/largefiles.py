"""Large files: history keeps a business card, the warehouse keeps the crate.

History remembers forever, which is exactly wrong for a
four-gigabyte dataset that changes weekly: every clone would
carry every version to the end of time. The pointer scheme
splits custody: the repository commits a small pointer file,
digest, size, and nothing else, while the bytes live in a
warehouse keyed by that digest, fetched on demand and
verified on arrival. The threshold is policy, not physics,
and the intake is honest about near misses: a file just
under the line is admitted with a note naming how close it
came, because thresholds without visibility breed the
folklore that the limit is broken. Missing warehouse entries
fail with the digest and the pointer's path, never a bare
not-found, since the whole point of a pointer is knowing
exactly what is missing.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from keel.errors import Corrupt, Invalid, Missing

THRESHOLD_BYTES = 10_000
NEAR_MISS_MARGIN = 0.9


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()[:20]


def make_pointer(payload: bytes) -> bytes:
    return (
        f"keel-pointer-v1\ndigest {_digest(payload)}\n"
        f"size {len(payload)}"
    ).encode()


def is_pointer(content: bytes) -> bool:
    return content.startswith(b"keel-pointer-v1\n")


def parse_pointer(content: bytes) -> tuple[str, int]:
    if not is_pointer(content):
        raise Invalid("not a pointer file")
    lines = content.decode().splitlines()
    digest = lines[1].split(" ", 1)[1]
    size = int(lines[2].split(" ", 1)[1])
    return digest, size


@dataclass
class Warehouse:
    crates: dict[str, bytes] = field(default_factory=dict)
    fetches: int = 0

    def store(self, payload: bytes) -> str:
        digest = _digest(payload)
        self.crates[digest] = payload
        return digest

    def fetch(self, digest: str, pointer_path: str) -> bytes:
        payload = self.crates.get(digest)
        if payload is None:
            raise Missing(
                f"{pointer_path} points at {digest[:8]} and "
                "the warehouse has no such crate; a pointer's "
                "whole point is knowing exactly what is "
                "missing"
            )
        if _digest(payload) != digest:
            raise Corrupt(
                f"crate {digest[:8]} does not match its label"
            )
        self.fetches += 1
        return payload


@dataclass
class Intake:
    warehouse: Warehouse
    pointered: int = 0
    near_misses: list[str] = field(default_factory=list)

    def admit(
        self, path: str, content: bytes
    ) -> tuple[bytes, str]:
        if len(content) > THRESHOLD_BYTES:
            digest = self.warehouse.store(content)
            self.pointered += 1
            return make_pointer(content), (
                f"{path}: {len(content)} bytes crated as "
                f"{digest[:8]}; history keeps the business "
                "card"
            )
        if len(content) > THRESHOLD_BYTES * NEAR_MISS_MARGIN:
            self.near_misses.append(path)
            return content, (
                f"{path}: admitted whole at {len(content)} "
                f"bytes, {THRESHOLD_BYTES - len(content)} "
                "under the line; thresholds without "
                "visibility breed folklore"
            )
        return content, f"{path}: admitted whole"

    def materialize(
        self, path: str, content: bytes
    ) -> bytes:
        if not is_pointer(content):
            return content
        digest, size = parse_pointer(content)
        payload = self.warehouse.fetch(digest, path)
        if len(payload) != size:
            raise Corrupt(
                f"{path}: the crate is {len(payload)} bytes "
                f"against a card saying {size}"
            )
        return payload

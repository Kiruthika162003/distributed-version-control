"""Rerere: resolve a conflict once, and the recording resolves its twins.

Long-lived branches meet the same conflicts repeatedly, at
every merge from main, at the rebase, at the final landing,
and re-resolving the identical collision by hand each time is
copy work with an error rate. The recorder keys each conflict
by the digest of its three texts, base, ours, theirs, in
exactly that role order, and stores the human's resolution;
when the same three texts collide again in any file at any
time, the recording replays. The key deliberately includes
all three sides, because two conflicts with the same ours and
theirs but different bases are different questions wearing
the same clothes, and replaying an answer across different
questions is how rerere earns horror stories. Replays are
labeled in the receipt, never silent, so a wrong recording is
discoverable the day it first lies rather than the month
after.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from keel.errors import Invalid


def conflict_key(
    base: bytes, ours: bytes, theirs: bytes
) -> str:
    folded = b"|base|" + base + b"|ours|" + ours + (
        b"|theirs|" + theirs
    )
    return hashlib.sha256(folded).hexdigest()[:20]


@dataclass
class Recorder:
    recordings: dict[str, bytes] = field(default_factory=dict)
    replays: int = 0
    recordings_made: int = 0

    def record(
        self,
        base: bytes,
        ours: bytes,
        theirs: bytes,
        resolution: bytes,
    ) -> str:
        if resolution in (ours, theirs):
            key = conflict_key(base, ours, theirs)
            self.recordings[key] = resolution
            self.recordings_made += 1
            return (
                "recorded a side-take; even trivial answers "
                "are worth not retyping"
            )
        if not resolution.strip():
            raise Invalid(
                "an empty resolution is a deletion, and "
                "deletions are decided at the tree, not "
                "recorded at the text"
            )
        key = conflict_key(base, ours, theirs)
        self.recordings[key] = resolution
        self.recordings_made += 1
        return f"recorded under {key[:8]}"

    def replay(
        self, base: bytes, ours: bytes, theirs: bytes
    ) -> tuple[bytes, str] | None:
        key = conflict_key(base, ours, theirs)
        recording = self.recordings.get(key)
        if recording is None:
            return None
        self.replays += 1
        return recording, (
            f"REPLAYED recording {key[:8]}; labeled so a "
            "wrong recording is discoverable the day it "
            "first lies"
        )

    def different_base_is_a_different_question(
        self,
        base_one: bytes,
        base_two: bytes,
        ours: bytes,
        theirs: bytes,
    ) -> bool:
        return conflict_key(
            base_one, ours, theirs
        ) != conflict_key(base_two, ours, theirs)

    def forget(self, base: bytes, ours: bytes, theirs: bytes) -> str:
        key = conflict_key(base, ours, theirs)
        if key not in self.recordings:
            raise Invalid(
                f"{key[:8]} was never recorded; forgetting it "
                "is already done"
            )
        del self.recordings[key]
        return (
            f"recording {key[:8]} forgotten; the next "
            "collision asks a human again"
        )

    def ledger(self) -> str:
        return (
            f"{self.recordings_made} recording(s), "
            f"{self.replays} replay(s); every replay is a "
            "hand-resolution not retyped"
        )

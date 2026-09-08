"""Binary diff: bytes compared by weight and shape, never by story.

Line tools lie about binaries politely, showing nothing and
calling it a diff, and this module replaces the nothing
with the four measurements that exist without lines: how
the weight changed, how much is shared at the head, how
much at the tail, and how big the changed middle is on each
side, because a ten-megabyte asset that grew by twelve
bytes in the middle is a very different event from one
rewritten end to end, and both render as Binary files
differ in the polite tools. The shared-tail measurement is
capped so the head and tail never overlap and claim the
same bytes twice, an easy lie when the new file contains
the old one whole. Similarity is the shared weight over
the total, a number for sorting and never for merging,
since the one honest merge strategy for binaries is a
human choosing a side on purpose.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BinaryDelta:
    old_size: int
    new_size: int
    shared_head: int
    shared_tail: int

    def weight_change(self) -> int:
        return self.new_size - self.old_size

    def old_core(self) -> int:
        return (
            self.old_size
            - self.shared_head
            - self.shared_tail
        )

    def new_core(self) -> int:
        return (
            self.new_size
            - self.shared_head
            - self.shared_tail
        )

    def similarity(self) -> float:
        total = self.old_size + self.new_size
        if total == 0:
            return 1.0
        shared = 2 * (
            self.shared_head + self.shared_tail
        )
        return shared / total


def compare(old: bytes, new: bytes) -> BinaryDelta:
    head = 0
    limit = min(len(old), len(new))
    while head < limit and old[head] == new[head]:
        head += 1
    tail = 0
    tail_room = limit - head
    while (
        tail < tail_room
        and old[len(old) - 1 - tail]
        == new[len(new) - 1 - tail]
    ):
        tail += 1
    return BinaryDelta(
        old_size=len(old),
        new_size=len(new),
        shared_head=head,
        shared_tail=tail,
    )


def narrate(path: str, old: bytes, new: bytes) -> str:
    if old == new:
        return f"{path}: byte-identical; nothing moved"
    if not old:
        return (
            f"{path}: born at {len(new)} byte(s)"
        )
    if not new:
        return (
            f"{path}: emptied from {len(old)} byte(s); "
            "a deletion by another name"
        )
    delta = compare(old, new)
    sign = "+" if delta.weight_change() >= 0 else ""
    return (
        f"{path}: {delta.old_size} -> "
        f"{delta.new_size} byte(s) "
        f"({sign}{delta.weight_change()}); "
        f"{delta.shared_head} shared at the head, "
        f"{delta.shared_tail} at the tail; the middle "
        f"{delta.old_core()} -> {delta.new_core()} is "
        "where the story hides, and binaries do not "
        "tell stories"
    )

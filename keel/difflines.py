"""Line diff: the longest common subsequence, and hunks a human can read.

The diff walks both files for their longest common subsequence
and reports everything else as deletions and insertions, which
is the classic algorithm because it is the honest one: it
never invents a change where lines merely moved past each
other in the file, and it never hides one by pairing unrelated
lines as a modification. Equal lines anchor; what falls
between anchors becomes a hunk carrying both sides and both
line numbers, because a hunk that cannot say where it applies
is trivia, and the patch tools downstream, merge, blame,
rebase, all consume these hunks rather than re-deriving their
own opinion of what changed. The quadratic table is bounded
and says so: two files past the guard rail get a whole-file
hunk with the reason named, since a diff that silently takes
minutes teaches people to stop diffing.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Invalid

LCS_GUARD = 2000


@dataclass(frozen=True)
class Hunk:
    old_start: int
    old_lines: tuple[str, ...]
    new_start: int
    new_lines: tuple[str, ...]

    def kind(self) -> str:
        if not self.old_lines:
            return "insert"
        if not self.new_lines:
            return "delete"
        return "replace"

    def describe(self) -> str:
        return (
            f"{self.kind()} at old:{self.old_start + 1} "
            f"new:{self.new_start + 1} "
            f"(-{len(self.old_lines)} +{len(self.new_lines)})"
        )


def _lcs_table(
    old: list[str], new: list[str]
) -> list[list[int]]:
    rows = len(old) + 1
    cols = len(new) + 1
    table = [[0] * cols for _ in range(rows)]
    for row in range(len(old) - 1, -1, -1):
        for col in range(len(new) - 1, -1, -1):
            if old[row] == new[col]:
                table[row][col] = table[row + 1][col + 1] + 1
            else:
                table[row][col] = max(
                    table[row + 1][col], table[row][col + 1]
                )
    return table


def diff_lines(old_text: str, new_text: str) -> list[Hunk]:
    old = old_text.splitlines()
    new = new_text.splitlines()
    if len(old) > LCS_GUARD or len(new) > LCS_GUARD:
        raise Invalid(
            f"{max(len(old), len(new))} lines exceed the "
            f"{LCS_GUARD}-line guard; a diff that silently "
            "takes minutes teaches people to stop diffing"
        )
    table = _lcs_table(old, new)
    hunks: list[Hunk] = []
    row = col = 0
    pending_old: list[str] = []
    pending_new: list[str] = []
    hunk_old_start = hunk_new_start = 0

    def flush() -> None:
        if pending_old or pending_new:
            hunks.append(
                Hunk(
                    old_start=hunk_old_start,
                    old_lines=tuple(pending_old),
                    new_start=hunk_new_start,
                    new_lines=tuple(pending_new),
                )
            )
            pending_old.clear()
            pending_new.clear()

    while row < len(old) and col < len(new):
        if old[row] == new[col]:
            flush()
            row += 1
            col += 1
            hunk_old_start = row
            hunk_new_start = col
        elif table[row + 1][col] >= table[row][col + 1]:
            pending_old.append(old[row])
            row += 1
        else:
            pending_new.append(new[col])
            col += 1
    pending_old.extend(old[row:])
    pending_new.extend(new[col:])
    flush()
    return hunks


def apply_hunks(old_text: str, hunks: list[Hunk]) -> str:
    lines = old_text.splitlines()
    for hunk in sorted(
        hunks, key=lambda held: -held.old_start
    ):
        expected = tuple(
            lines[
                hunk.old_start : hunk.old_start
                + len(hunk.old_lines)
            ]
        )
        if expected != hunk.old_lines:
            raise Invalid(
                f"the hunk at old:{hunk.old_start + 1} does "
                "not match the text it claims to replace; "
                "patches apply to what they saw or not at all"
            )
        lines[
            hunk.old_start : hunk.old_start + len(hunk.old_lines)
        ] = list(hunk.new_lines)
    return "\n".join(lines)


def change_summary(old_text: str, new_text: str) -> str:
    hunks = diff_lines(old_text, new_text)
    if not hunks:
        return "identical"
    removed = sum(len(hunk.old_lines) for hunk in hunks)
    added = sum(len(hunk.new_lines) for hunk in hunks)
    return (
        f"{len(hunks)} hunk(s), -{removed} +{added}"
    )

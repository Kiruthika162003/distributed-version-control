"""Rename detection: a delete and an add that are secretly one event.

The tree diff reports what changed by path, but a moved file
shows up as a deletion here and an addition there, and every
tool downstream tells a worse story for it: blame loses the
trail, merge treats the halves separately, and the log claims
work that never happened. The detector pairs deletions with
additions in two passes: exact pass first, where matching
content addresses make the rename certain and free to prove,
then a similarity pass over what remains, scoring shared
lines against total lines and accepting only above a
threshold, greedily, best pairs first. The score rides along
in the report because "renamed with 62 percent similarity"
invites a human check while "renamed" asserts a certainty
the arithmetic does not have, and inflated certainty is how
rename detection earned its reputation for guessing.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Invalid

SIMILARITY_FLOOR = 0.5


@dataclass(frozen=True)
class Rename:
    old_path: str
    new_path: str
    similarity: float

    def describe(self) -> str:
        certainty = (
            "exact"
            if self.similarity == 1.0
            else f"{self.similarity:.0%} similar"
        )
        return (
            f"{self.old_path} -> {self.new_path} ({certainty})"
        )


def line_similarity(old: bytes, new: bytes) -> float:
    old_lines = old.decode(errors="replace").splitlines()
    new_lines = new.decode(errors="replace").splitlines()
    if not old_lines and not new_lines:
        return 1.0
    if not old_lines or not new_lines:
        return 0.0
    shared = 0
    pool = list(new_lines)
    for line in old_lines:
        if line in pool:
            pool.remove(line)
            shared += 1
    return 2 * shared / (len(old_lines) + len(new_lines))


def detect_renames(
    removed: dict[str, bytes],
    added: dict[str, bytes],
    floor: float = SIMILARITY_FLOOR,
) -> tuple[list[Rename], list[str], list[str]]:
    if not 0 < floor <= 1:
        raise Invalid(
            "the similarity floor is a fraction in (0, 1]"
        )
    renames: list[Rename] = []
    open_removed = dict(removed)
    open_added = dict(added)
    for old_path, old_content in list(open_removed.items()):
        for new_path, new_content in list(open_added.items()):
            if old_content == new_content:
                renames.append(
                    Rename(
                        old_path=old_path,
                        new_path=new_path,
                        similarity=1.0,
                    )
                )
                del open_removed[old_path]
                del open_added[new_path]
                break
    scored: list[tuple[float, str, str]] = []
    for old_path, old_content in open_removed.items():
        for new_path, new_content in open_added.items():
            score = line_similarity(old_content, new_content)
            if score >= floor:
                scored.append((score, old_path, new_path))
    scored.sort(reverse=True)
    for score, old_path, new_path in scored:
        if (
            old_path in open_removed
            and new_path in open_added
        ):
            renames.append(
                Rename(
                    old_path=old_path,
                    new_path=new_path,
                    similarity=round(score, 4),
                )
            )
            del open_removed[old_path]
            del open_added[new_path]
    return (
        sorted(renames, key=lambda held: held.old_path),
        sorted(open_removed),
        sorted(open_added),
    )


def narrate(
    renames: list[Rename],
    true_removals: list[str],
    true_additions: list[str],
) -> str:
    lines = []
    for rename in renames:
        lines.append(f"  renamed {rename.describe()}")
    for path in true_removals:
        lines.append(f"  removed {path}")
    for path in true_additions:
        lines.append(f"  added {path}")
    if not lines:
        return "no changes to narrate"
    header = (
        f"{len(renames)} rename(s), {len(true_removals)} "
        f"removal(s), {len(true_additions)} addition(s)"
    )
    return "\n".join([header, *lines])

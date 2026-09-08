"""Three-way merge: the base breaks ties, and real conflicts stay loud.

Two-way merge guesses; three-way merge knows, because the
common ancestor answers the question two files cannot answer
alone: who changed this line. Each region resolves by one
rule with no exceptions: if only one side moved away from the
base, take that side; if both sides moved identically, take
either; if both moved differently, that is a conflict, and
the conflict is rendered with all three texts, base included,
because a conflict marker without the base shows two answers
and hides the question. The merge never resolves a real
conflict by heuristic, not even an appealing one, since every
silent resolution strategy eventually merges a security check
out of existence, and the person who typed neither side is
the one who debugs it.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.difflines import diff_lines


@dataclass(frozen=True)
class MergedRegion:
    kind: str
    lines: tuple[str, ...]
    base_lines: tuple[str, ...] = ()
    left_lines: tuple[str, ...] = ()
    right_lines: tuple[str, ...] = ()


def _changed_regions(
    base: list[str], side: list[str]
) -> dict[int, bool]:
    changed: dict[int, bool] = {}
    for hunk in diff_lines("\n".join(base), "\n".join(side)):
        span = max(len(hunk.old_lines), 1)
        for offset in range(span):
            changed[hunk.old_start + offset] = True
    return changed


def _rebuild(
    base: list[str], side: list[str]
) -> dict[int, list[str]]:
    replacement: dict[int, list[str]] = {
        index: [line] for index, line in enumerate(base)
    }
    for hunk in diff_lines("\n".join(base), "\n".join(side)):
        anchor = hunk.old_start
        span = len(hunk.old_lines)
        if span == 0:
            joined = replacement.setdefault(anchor, [])
            joined[0:0] = list(hunk.new_lines)
            continue
        replacement[anchor] = list(hunk.new_lines)
        for offset in range(1, span):
            replacement[anchor + offset] = []
    return replacement


def merge3(
    base_text: str, left_text: str, right_text: str
) -> list[MergedRegion]:
    base = base_text.splitlines()
    left_changed = _changed_regions(
        base, left_text.splitlines()
    )
    right_changed = _changed_regions(
        base, right_text.splitlines()
    )
    left_rebuild = _rebuild(base, left_text.splitlines())
    right_rebuild = _rebuild(base, right_text.splitlines())
    regions: list[MergedRegion] = []
    positions = sorted(
        set(range(len(base)))
        | set(left_rebuild)
        | set(right_rebuild)
    ) or [0]
    for index in positions:
        base_here = tuple(
            [base[index]] if index < len(base) else []
        )
        left_here = tuple(left_rebuild.get(index, base_here))
        right_here = tuple(right_rebuild.get(index, base_here))
        left_moved = left_changed.get(index, False) or (
            left_here != base_here
        )
        right_moved = right_changed.get(index, False) or (
            right_here != base_here
        )
        if not left_moved and not right_moved:
            regions.append(
                MergedRegion(kind="clean", lines=base_here)
            )
        elif left_moved and not right_moved:
            regions.append(
                MergedRegion(kind="clean", lines=left_here)
            )
        elif right_moved and not left_moved:
            regions.append(
                MergedRegion(kind="clean", lines=right_here)
            )
        elif left_here == right_here:
            regions.append(
                MergedRegion(kind="clean", lines=left_here)
            )
        else:
            regions.append(
                MergedRegion(
                    kind="conflict",
                    lines=(),
                    base_lines=base_here,
                    left_lines=left_here,
                    right_lines=right_here,
                )
            )
    return regions


def render(
    regions: list[MergedRegion],
    left_name: str = "ours",
    right_name: str = "theirs",
) -> str:
    lines: list[str] = []
    for region in regions:
        if region.kind == "clean":
            lines.extend(region.lines)
        else:
            lines.append(f"<<<<<<< {left_name}")
            lines.extend(region.left_lines)
            lines.append("||||||| base")
            lines.extend(region.base_lines)
            lines.append("=======")
            lines.extend(region.right_lines)
            lines.append(f">>>>>>> {right_name}")
    return "\n".join(lines)


def is_clean(regions: list[MergedRegion]) -> bool:
    return all(region.kind == "clean" for region in regions)


def conflict_count(regions: list[MergedRegion]) -> int:
    return sum(
        1 for region in regions if region.kind == "conflict"
    )

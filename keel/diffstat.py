"""Diffstat: the shape of a change at a glance, drawn to scale.

Before anyone reads a diff they size it up, and the stat
answers the sizing questions honestly: which files moved, how
much in each direction, and how the churn distributes,
rendered with bars scaled to the largest file's change so the
picture is proportional rather than absolute, because a
twenty-character bar meaning fifty lines in one repo and five
thousand in another is a chart that cannot be read across
projects. Binary-looking content is stated as such with byte
deltas instead of line counts, since counting lines in bytes
that have no lines flatters nobody, and the summary row at
the bottom is the only place totals appear, once, because a
reader who wants the total wants it exactly once and a reader
who wants detail wants rows.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.difflines import diff_lines
from keel.errors import Invalid

BAR_WIDTH = 20


def looks_binary(content: bytes) -> bool:
    return b"\x00" in content


@dataclass(frozen=True)
class FileStat:
    path: str
    added: int
    removed: int
    binary: bool

    def churn(self) -> int:
        return self.added + self.removed


def stat_changes(
    old_files: dict[str, bytes], new_files: dict[str, bytes]
) -> list[FileStat]:
    stats: list[FileStat] = []
    for path in sorted(set(old_files) | set(new_files)):
        old = old_files.get(path, b"")
        new = new_files.get(path, b"")
        if old == new:
            continue
        if looks_binary(old) or looks_binary(new):
            stats.append(
                FileStat(
                    path=path,
                    added=max(0, len(new) - len(old)),
                    removed=max(0, len(old) - len(new)),
                    binary=True,
                )
            )
            continue
        hunks = diff_lines(
            old.decode(errors="replace"),
            new.decode(errors="replace"),
        )
        added = sum(len(h.new_lines) for h in hunks)
        removed = sum(len(h.old_lines) for h in hunks)
        stats.append(
            FileStat(
                path=path,
                added=added,
                removed=removed,
                binary=False,
            )
        )
    return stats


def render_stat(stats: list[FileStat]) -> str:
    if not stats:
        return "no changes; the stat of nothing is nothing"
    widest = max(stat.churn() for stat in stats)
    if widest == 0:
        raise Invalid("a change with zero churn is not a change")
    name_width = max(len(stat.path) for stat in stats)
    lines = []
    for stat in stats:
        if stat.binary:
            lines.append(
                f"{stat.path:<{name_width}}  binary "
                f"(+{stat.added} -{stat.removed} bytes)"
            )
            continue
        scaled = max(
            1, round(BAR_WIDTH * stat.churn() / widest)
        )
        plus_share = (
            stat.added / stat.churn() if stat.churn() else 0
        )
        plus_bar = round(scaled * plus_share)
        bar = "+" * plus_bar + "-" * (scaled - plus_bar)
        lines.append(
            f"{stat.path:<{name_width}}  "
            f"{stat.added + stat.removed:>4} {bar}"
        )
    total_added = sum(s.added for s in stats if not s.binary)
    total_removed = sum(
        s.removed for s in stats if not s.binary
    )
    binaries = sum(1 for s in stats if s.binary)
    summary = (
        f"{len(stats)} file(s) changed, {total_added} "
        f"insertion(s), {total_removed} deletion(s)"
    )
    if binaries:
        summary += f", {binaries} binary"
    lines.append(summary)
    return "\n".join(lines)

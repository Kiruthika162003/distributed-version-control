"""Soundings: the depth of the tree, charted before anyone runs aground.

Directory depth is a tax every path pays on every mention,
in imports, in reviews, in the width of everyone's
terminal, and the soundings chart where the tree stands:
the histogram of depths first, because the shape says more
than any average, then the deepest paths by name, since
the deepest path is where tab completion goes to die, and
the mean depth for trend watchers. The verdicts follow the
chart with their thresholds aboard: a flat tree is praised
guardedly, flatness at scale being a junk drawer wearing
minimalism, a deep tree is asked whether the nesting earns
its tax, and the middle is called navigable and left
alone. One hard sounding is taken at the singleton chain,
a directory containing only a directory containing only a
directory, corridor architecture that adds depth without
adding shelter, and those are listed for collapsing.
"""

from __future__ import annotations

from keel.repo import Repo

FLAT_MEAN = 1.2
DEEP_MEAN = 3.0


def _depth(path: str) -> int:
    return path.count("/")


def chart(repo: Repo, address: str) -> str:
    paths = sorted(repo.files_at(address))
    depths = [_depth(path) for path in paths]
    histogram: dict[int, int] = {}
    for depth in depths:
        histogram[depth] = histogram.get(depth, 0) + 1
    mean = sum(depths) / len(depths) if depths else 0.0
    lines = [
        f"soundings across {len(paths)} path(s):"
    ]
    for depth in sorted(histogram):
        lines.append(
            f"  depth {depth}: {histogram[depth]} "
            "path(s)"
        )
    deepest = max(depths) if depths else 0
    for path in paths:
        if _depth(path) == deepest and deepest > 0:
            lines.append(
                f"  deepest: {path}; where tab "
                "completion goes to die"
            )
            break
    lines.append(f"  mean depth {mean:.1f}")
    if mean <= FLAT_MEAN:
        lines.append(
            "verdict: flat; praised guardedly, "
            "flatness at scale being a junk drawer "
            "wearing minimalism"
        )
    elif mean >= DEEP_MEAN:
        lines.append(
            "verdict: deep; does the nesting earn "
            "its tax on every mention?"
        )
    else:
        lines.append(
            "verdict: navigable, and left alone"
        )
    corridors = _corridors(paths)
    for corridor in corridors:
        lines.append(
            f"  corridor: {corridor}; depth without "
            "shelter, listed for collapsing"
        )
    return "\n".join(lines)


def _corridors(paths: list[str]) -> list[str]:
    children: dict[str, set[str]] = {}
    directories: set[str] = set()
    for path in paths:
        parts = path.split("/")
        for index in range(1, len(parts)):
            parent = "/".join(parts[: index - 1])
            child = "/".join(parts[:index])
            directories.add(child)
            children.setdefault(parent, set()).add(
                child
            )
    for path in paths:
        parent = (
            path.rsplit("/", 1)[0]
            if "/" in path
            else ""
        )
        children.setdefault(parent, set()).add(path)
    found = []
    for directory in sorted(directories):
        held = children.get(directory, set())
        if len(held) == 1 and next(
            iter(held)
        ) in directories:
            found.append(directory + "/")
    return found

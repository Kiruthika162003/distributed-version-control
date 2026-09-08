"""Dirstat: the diff rolled up by directory, percentages that sum honestly.

A change list with forty paths answers every question except
the one asked first, where did this change land, and the
rollup answers it: byte deltas aggregated by top-level
directory, expressed as percentages of the whole, sorted
heaviest first. The percentages are computed from absolute
deltas so a large deletion counts as change rather than
negative change, because a refactor that removes a thousand
lines landed somewhere, and a report that scores it zero
tells the reviewer to skip exactly the directory that most
needs eyes. Rounding is done by largest remainder so the
column sums to one hundred every time, since a report whose
percentages sum to ninety-eight invites the reader to hunt
for the missing two instead of reading, and depth is a
parameter, top-level by default, deeper on request, flat
files billed to the root's own line.
"""

from __future__ import annotations

from keel.errors import Invalid
from keel.repo import Repo

ROOT = "(root)"


def _bucket(path: str, depth: int) -> str:
    parts = path.split("/")
    if len(parts) <= 1:
        return ROOT
    return "/".join(parts[: min(depth, len(parts) - 1)])


def measure(
    repo: Repo,
    old_address: str,
    new_address: str,
    depth: int = 1,
) -> dict[str, int]:
    if depth < 1:
        raise Invalid(
            "a depth below one rolls everything into "
            "one number, and one number is not a map"
        )
    old_files = repo.files_at(old_address)
    new_files = repo.files_at(new_address)
    weights: dict[str, int] = {}
    for path in set(old_files) | set(new_files):
        old = old_files.get(path, b"")
        new = new_files.get(path, b"")
        if old == new:
            continue
        delta = abs(len(new) - len(old))
        if delta == 0:
            delta = len(new)
        bucket = _bucket(path, depth)
        weights[bucket] = (
            weights.get(bucket, 0) + delta
        )
    return weights


def _percentages(
    weights: dict[str, int]
) -> dict[str, int]:
    total = sum(weights.values())
    if total == 0:
        return {}
    exact = {
        bucket: weight * 100 / total
        for bucket, weight in weights.items()
    }
    floored = {
        bucket: int(value)
        for bucket, value in exact.items()
    }
    leftover = 100 - sum(floored.values())
    by_remainder = sorted(
        exact,
        key=lambda bucket: (
            -(exact[bucket] - floored[bucket]),
            bucket,
        ),
    )
    for bucket in by_remainder[:leftover]:
        floored[bucket] += 1
    return floored


def render(
    repo: Repo,
    old_address: str,
    new_address: str,
    depth: int = 1,
) -> str:
    weights = measure(
        repo, old_address, new_address, depth
    )
    if not weights:
        return "no change landed anywhere; same trees"
    shares = _percentages(weights)
    ordered = sorted(
        weights,
        key=lambda bucket: (-weights[bucket], bucket),
    )
    lines = [
        f"where the change landed "
        f"({sum(weights.values())} byte(s) of motion):"
    ]
    for bucket in ordered:
        lines.append(
            f"  {shares[bucket]:3d}% {bucket} "
            f"({weights[bucket]} byte(s))"
        )
    lines.append(
        "deletions count as change; what was removed "
        "landed somewhere too"
    )
    return "\n".join(lines)

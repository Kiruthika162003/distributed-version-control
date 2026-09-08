"""The size census: where the bytes live and which ones earn their rent.

Repositories gain weight the way attics do, one reasonable
box at a time, and the census is the annual walk with a
flashlight. Objects are weighed by kind first, because the
ratio matters before any single number: a store that is
mostly tree bytes has a layout problem while a store that
is mostly blob bytes has a content problem, and the same
diet does not treat both. Blobs are then named, every tree
in every commit consulted so each blob answers to the paths
that ever claimed it, since an anonymous heavy object is a
suspect and a named one is a decision. The prescriptions
quote their thresholds inline, a blob past the heavy line
gets pointed at the warehouse and a path hoarding many
versions gets pointed at the delta pack, because advice
with hidden thresholds is astrology with a config file.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.objects import BLOB
from keel.repo import Repo

HEAVY_BYTES = 1000
HOARD_VERSIONS = 4


@dataclass(frozen=True)
class SizeCensus:
    counts: dict[str, int]
    weights: dict[str, int]
    blob_names: dict[str, tuple[str, ...]]
    versions_by_path: dict[str, int]

    def total_bytes(self) -> int:
        return sum(self.weights.values())


def measure(repo: Repo) -> SizeCensus:
    counts: dict[str, int] = {}
    weights: dict[str, int] = {}
    for _address, (kind, payload) in (
        repo.store.objects.items()
    ):
        counts[kind] = counts.get(kind, 0) + 1
        weights[kind] = (
            weights.get(kind, 0) + len(payload)
        )
    names: dict[str, set[str]] = {}
    versions: dict[str, set[str]] = {}
    for commit in repo.graph.commits.values():
        for path, blob in repo.trees.read_tree(
            commit.tree
        ).items():
            names.setdefault(blob, set()).add(path)
            versions.setdefault(path, set()).add(blob)
    return SizeCensus(
        counts=counts,
        weights=weights,
        blob_names={
            blob: tuple(sorted(held))
            for blob, held in names.items()
        },
        versions_by_path={
            path: len(held)
            for path, held in versions.items()
        },
    )


def heaviest_blobs(
    repo: Repo, census: SizeCensus, top: int = 3
) -> list[tuple[str, int, tuple[str, ...]]]:
    blobs = [
        (address, len(payload))
        for address, (kind, payload) in (
            repo.store.objects.items()
        )
        if kind == BLOB
    ]
    blobs.sort(key=lambda held: (-held[1], held[0]))
    return [
        (
            address,
            size,
            census.blob_names.get(address, ("unclaimed",)),
        )
        for address, size in blobs[:top]
    ]


def report(repo: Repo, top: int = 3) -> str:
    census = measure(repo)
    lines = [
        f"{sum(census.counts.values())} object(s), "
        f"{census.total_bytes()} byte(s) total"
    ]
    for kind in sorted(census.counts):
        lines.append(
            f"  {kind}: {census.counts[kind]} object(s), "
            f"{census.weights.get(kind, 0)} byte(s)"
        )
    for address, size, names in heaviest_blobs(
        repo, census, top
    ):
        lines.append(
            f"  heavy: {address[:8]} at {size} byte(s), "
            f"known as {', '.join(names)}"
        )
    prescriptions = []
    for _address, size, names in heaviest_blobs(
        repo, census, top
    ):
        if size > HEAVY_BYTES:
            prescriptions.append(
                f"  point {', '.join(names)} at the "
                f"warehouse; {size} byte(s) is past the "
                f"heavy line of {HEAVY_BYTES}"
            )
    for path in sorted(census.versions_by_path):
        held = census.versions_by_path[path]
        if held >= HOARD_VERSIONS:
            prescriptions.append(
                f"  delta-pack {path}; {held} versions "
                f"is a hoard at the line of "
                f"{HOARD_VERSIONS}"
            )
    if prescriptions:
        lines.append("prescriptions:")
        lines.extend(prescriptions)
    else:
        lines.append(
            "no prescriptions; the attic is just full "
            "of attic"
        )
    return "\n".join(lines)

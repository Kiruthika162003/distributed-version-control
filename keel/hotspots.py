"""Hotspots: where change frequency meets size, trouble compounds.

Every file has two independent risk axes: how often it
changes and how big it has grown, and the files where both
run high are where the defects live, because frequent change
means frequent opportunity and size means each opportunity
has more places to hide. The census walks history counting
touches per path, takes current size from the tip, and
scores the product, ranking hotspots with both factors
printed since a product hides which axis to attack: the
huge stable file wants splitting someday, the small churning
file wants an owner today, and the huge churning file wants
both and a meeting. Deleted files fall out of the ranking
but their touch history is reported as a footnote, because
a file that churned wildly and then vanished is often the
same trouble wearing a new path.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Invalid
from keel.repo import Repo


@dataclass(frozen=True)
class Hotspot:
    path: str
    touches: int
    size: int

    def score(self) -> int:
        return self.touches * self.size

    def prescription(self) -> str:
        if self.touches >= 3 and self.size >= 200:
            return "both and a meeting"
        if self.touches >= 3:
            return "an owner today"
        if self.size >= 200:
            return "splitting someday"
        return "watch"


def census(repo: Repo, tip: str) -> tuple[
    list[Hotspot], list[str]
]:
    touches: dict[str, int] = {}
    for address in repo.graph.ancestors(tip):
        commit = repo.graph.get(address)
        if len(commit.parents) > 1:
            continue
        if commit.parents:
            parent_files = repo.files_at(commit.parents[0])
        else:
            parent_files = {}
        own_files = repo.files_at(address)
        for path in set(parent_files) | set(own_files):
            if parent_files.get(path) != own_files.get(
                path
            ):
                touches[path] = touches.get(path, 0) + 1
    current = repo.files_at(tip)
    spots = [
        Hotspot(
            path=path,
            touches=count,
            size=len(current[path]),
        )
        for path, count in touches.items()
        if path in current
    ]
    spots.sort(key=lambda spot: (-spot.score(), spot.path))
    ghosts = sorted(
        f"{path} churned {count} time(s) then vanished; "
        "often the same trouble wearing a new path"
        for path, count in touches.items()
        if path not in current and count >= 3
    )
    return spots, ghosts


def report(repo: Repo, tip: str) -> str:
    spots, ghosts = census(repo, tip)
    if not spots:
        raise Invalid("no history, no hotspots")
    lines = ["hotspots, both axes printed:"]
    for spot in spots[:5]:
        lines.append(
            f"  {spot.path}: {spot.touches} touch(es) x "
            f"{spot.size} bytes = {spot.score()}; "
            f"{spot.prescription()}"
        )
    lines.extend(f"  footnote: {ghost}" for ghost in ghosts)
    return "\n".join(lines)

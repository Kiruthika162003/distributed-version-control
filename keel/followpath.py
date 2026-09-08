"""Follow: a file's history across its renames, the trail walked honestly.

Plain per-path history ends at the rename and calls it a
birth, which is how a file with five years of story shows
three weeks of it. The follow walks the first-parent line
backward and, whenever the tracked path appears out of
nowhere, asks the rename detector whether a deletion in
the same commit matches it, exact content first, then
similarity above the standing floor, and if so the walk
continues under the old name with the switch recorded. The
trail is the deliverable: every name the file has answered
to, each with the commit where it changed and the
similarity that justified the jump, because a follow that
silently hops names is unfalsifiable, and the reader
deserves to see the one weak link in an otherwise exact
chain. When no candidate clears the floor the trail ends
in those words, a birth is a birth, and inventing lineage
past it would make the whole trail suspect.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Missing
from keel.renames import detect_renames
from keel.repo import Repo


@dataclass(frozen=True)
class TrailStep:
    path: str
    address: str
    note: str

    def line(self) -> str:
        return (
            f"  {self.address[:8]} {self.path}: "
            f"{self.note}"
        )


def follow(
    repo: Repo, tip: str, path: str
) -> list[TrailStep]:
    chain = []
    cursor = tip
    while True:
        commit = repo.graph.get(cursor)
        chain.append(commit)
        if not commit.parents:
            break
        cursor = commit.parents[0]
    tracked = path
    trail: list[TrailStep] = []
    if path not in repo.files_at(tip):
        raise Missing(
            f"{path} is not at this tip; follow "
            "starts from a file that exists"
        )
    for commit in chain:
        current = repo.files_at(commit.address)
        if commit.parents:
            parent = repo.files_at(commit.parents[0])
        else:
            parent = {}
        if tracked not in current:
            continue
        if tracked in parent:
            if current[tracked] != parent[tracked]:
                trail.append(
                    TrailStep(
                        path=tracked,
                        address=commit.address,
                        note="edited",
                    )
                )
            continue
        if not commit.parents:
            trail.append(
                TrailStep(
                    path=tracked,
                    address=commit.address,
                    note="born here; a birth is a birth",
                )
            )
            continue
        removed = {
            old: parent[old]
            for old in parent
            if old not in current
        }
        added = {tracked: current[tracked]}
        renames, _deleted, _added = detect_renames(
            removed, added
        )
        if renames:
            jump = renames[0]
            certainty = (
                "exact content"
                if jump.similarity == 1.0
                else f"{jump.similarity:.0%} similar, "
                "the one weak link"
            )
            trail.append(
                TrailStep(
                    path=tracked,
                    address=commit.address,
                    note=(
                        f"renamed from {jump.old_path} "
                        f"({certainty})"
                    ),
                )
            )
            tracked = jump.old_path
        else:
            trail.append(
                TrailStep(
                    path=tracked,
                    address=commit.address,
                    note=(
                        "appeared with no candidate "
                        "above the floor; a birth is a "
                        "birth"
                    ),
                )
            )
    return trail


def narrate(repo: Repo, tip: str, path: str) -> str:
    trail = follow(repo, tip, path)
    names = []
    for step in trail:
        if step.path not in names:
            names.append(step.path)
    lines = [
        f"{path} has answered to {len(names)} name(s): "
        + " <- ".join(names)
    ]
    lines.extend(step.line() for step in trail)
    return "\n".join(lines)

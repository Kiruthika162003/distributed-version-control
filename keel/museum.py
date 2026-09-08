"""The museum: retired code exhibited with its dates and its way back.

The graveyard lists the dead; the museum curates them, one
exhibit per retired path with what a visitor actually
wants: the span it lived, born at one sequence and buried
at another, the size it stood at on its last day, the
burying commit's stated reason, and, the part that makes
this a museum and not a memorial, the dive instructions,
the exact address where salvage would find the final
bytes, because retired code gets un-retired weekly and
the visit that ends in a working recovery is the point
of keeping exhibits at all. The curation order is by
size at death, largest first, the big retirements being
the ones with stories, and the empty museum says what
every archivist hopes to say: nothing retired yet,
everything still working for a living.
"""

from __future__ import annotations

from keel.lifespans import chronicle
from keel.repo import Repo


def exhibits(
    repo: Repo, tip: str
) -> list[dict[str, object]]:
    found = []
    for path, events in chronicle(repo, tip).items():
        if events[-1].kind != "died":
            continue
        burial = events[-1]
        born = events[0]
        burying = repo.graph.get(burial.address)
        last_alive = burying.parents[0]
        final_bytes = repo.files_at(last_alive).get(
            path, b""
        )
        found.append(
            {
                "path": path,
                "born_seq": repo.graph.get(
                    born.address
                ).sequence,
                "buried_seq": burying.sequence,
                "size_at_death": len(final_bytes),
                "reason": burying.message.splitlines()[
                    0
                ],
                "dive_address": last_alive,
            }
        )
    found.sort(
        key=lambda held: (
            -held["size_at_death"],
            held["path"],
        )
    )
    return found


def tour(repo: Repo, tip: str) -> str:
    shown = exhibits(repo, tip)
    if not shown:
        return (
            "nothing retired yet; everything still "
            "working for a living"
        )
    lines = [f"{len(shown)} exhibit(s), largest first:"]
    for exhibit in shown:
        lines.append(
            f"  {exhibit['path']}: lived seq "
            f"{exhibit['born_seq']} to "
            f"{exhibit['buried_seq']}, stood at "
            f"{exhibit['size_at_death']} byte(s); "
            f"buried by {exhibit['reason']!r}; "
            f"salvage dives at "
            f"{str(exhibit['dive_address'])[:8]}"
        )
    lines.append(
        "retired code gets un-retired weekly; the "
        "visit that ends in a working recovery is "
        "the point of the exhibits"
    )
    return "\n".join(lines)

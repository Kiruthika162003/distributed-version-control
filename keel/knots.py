"""Knots: the integration tempo, read from the merges per window.

Speed claims about a repository are usually vibes, and the
knots measurement replaces them with the one rate that
matters for integration health: merges per window of
sequence, read from the worklog's own buckets, because a
trunk that integrates steadily absorbs change in small
honest collisions while a trunk that integrates in bursts
saves its collisions up. The reading is the list of
per-window merge counts and one verdict computed from the
spread, steady when no window doubles the average, gusty
when one does, becalmed when nothing has merged at all in
living memory, each verdict carrying what a navigator
would do about it, and none of them a grade, tempo being
a fact about the water and not a score for the crew.
"""

from __future__ import annotations

from keel.repo import Repo
from keel.worklog import digest


def reading(
    repo: Repo, tip: str, window: int = 5
) -> str:
    windows = digest(repo, tip, window)
    counts = [held.merges for held in windows]
    total = sum(counts)
    lines = [
        f"knots across {len(windows)} window(s) of "
        f"{window}: "
        + ", ".join(str(count) for count in counts)
    ]
    if total == 0:
        lines.append(
            "becalmed; nothing has merged in living "
            "memory, and a trunk that never "
            "integrates is saving its collisions up"
        )
    else:
        average = total / len(counts)
        if any(
            count > 2 * average for count in counts
        ):
            lines.append(
                "gusty; the bursts save collisions "
                "up, and the navigator smooths the "
                "queue rather than the crew"
            )
        else:
            lines.append(
                "steady; change absorbed in small "
                "honest collisions"
            )
    lines.append(
        "tempo is a fact about the water, not a "
        "score for the crew"
    )
    return "\n".join(lines)

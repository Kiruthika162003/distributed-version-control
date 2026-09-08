"""Impact: what a proposed change wakes up, read before anyone reviews it.

A change list names its paths; it does not name what those
paths are attached to, and the attachments are where
surprises live. The assessment reads two ledgers history
already keeps: the marriages, where touching one partner
and not the other predicts the follow-up commit everyone
pretends is unrelated, and the hotspots, where touching
ground that is already churning earns the review a warning
about the neighborhood. A marriage touched on both sides is
reported as kept, not warned, because editing both partners
together is exactly what the marriage wants, and paths that
wake nothing are counted in one quiet line, since an
assessment that finds danger everywhere is an assessment
nobody schedules reviews by. The output is sized to its
findings, and the empty case says plainly that this change
walks alone.
"""

from __future__ import annotations

from keel.coupling import measure as marriages_of
from keel.hotspots import census as hotspot_census
from keel.repo import Repo


def assess(
    repo: Repo,
    tip: str,
    touched_paths: list[str],
) -> str:
    touched = set(touched_paths)
    marriages = marriages_of(repo, tip)
    woken: list[str] = []
    kept: list[str] = []
    for marriage in marriages:
        pair = {marriage.left, marriage.right}
        inside = pair & touched
        if not inside:
            continue
        if pair <= touched:
            kept.append(
                f"  kept: {marriage.left} + "
                f"{marriage.right} edited together, "
                "which is what the marriage wants"
            )
            continue
        absent = (pair - touched).pop()
        present = inside.pop()
        woken.append(
            f"  woken: {present} is touched but "
            f"{absent} is not; the marriage "
            f"({marriage.rate:.0%}) predicts the "
            "follow-up commit everyone pretends is "
            "unrelated"
        )
    spots, _ghosts = hotspot_census(repo, tip)
    burning = [
        spot
        for spot in spots
        if spot.prescription() != "watch"
    ]
    hot = [
        f"  hot ground: {spot.path} "
        f"({spot.touches} touch(es), "
        f"{spot.size} byte(s)); prescription "
        f"{spot.prescription()!r}"
        for spot in burning
        if spot.path in touched
    ]
    findings = woken + hot
    quiet = (
        touched
        - {line.split()[1] for line in woken}
        - {spot.path for spot in burning}
    )
    for marriage in marriages:
        if {marriage.left, marriage.right} <= touched:
            quiet -= {marriage.left, marriage.right}
    lines = [
        f"impact of {len(touched)} path(s):"
    ]
    lines.extend(woken)
    lines.extend(kept)
    lines.extend(hot)
    if quiet:
        lines.append(
            f"  {len(quiet)} path(s) wake nothing"
        )
    if not findings:
        lines.append(
            "this change walks alone; schedule the "
            "review it looks like"
        )
    else:
        lines.append(
            f"{len(findings)} finding(s); size the "
            "review by the neighborhood, not the "
            "diff"
        )
    return "\n".join(lines)

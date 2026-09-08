"""Offboarding: everything a name still holds, gathered before it goes.

People leave and their names stay load-bearing: a lock on
the design file, a seat on three rosters, a place in the
review rotation, and each one fails at the worst time if
nobody looks. The manifest gathers every holding by asking
the organs that keep names, the lock office for locks held,
the access table for rosters ridden, the review wheel for
rotation seats and undischarged load, and prints them as a
checklist rather than a report, because offboarding is work
to do and not a fact to know. Each line names the handover
action in the holding's own terms, release or reassign or
retire, and the empty manifest is the compliment it sounds
like: this person leaves nothing jammed, which is either
luck or the sign of someone who released as they went.
"""

from __future__ import annotations

from keel.acl import AccessTable
from keel.filelocks import LockOffice
from keel.reviewrotation import Wheel


def manifest(
    name: str,
    locks: LockOffice | None = None,
    access: AccessTable | None = None,
    wheel: Wheel | None = None,
) -> str:
    holdings: list[str] = []

    if locks is not None:
        for path in sorted(locks.locks):
            lock = locks.locks[path]
            if lock.holder == name:
                holdings.append(
                    f"  lock on {path} "
                    f"({lock.reason}); release it or "
                    "the next editor steals it in "
                    "capitals"
                )

    if access is not None:
        for team in sorted(access.teams):
            if name in access.teams[team]:
                guarded = [
                    pattern
                    for pattern, granted in (
                        access.grants
                    )
                    if granted == team
                ]
                note = (
                    f" guarding "
                    f"{', '.join(sorted(guarded))}"
                    if guarded
                    else ""
                )
                holdings.append(
                    f"  seat on {team}{note}; retire "
                    "it so the roster stays true"
                )

    if wheel is not None:
        for team in sorted(wheel.rosters):
            if name in wheel.rosters[team]:
                load = wheel.load.get(name, 0)
                away = (
                    "; currently marked away"
                    if name in wheel.away
                    else ""
                )
                holdings.append(
                    f"  rotation seat on the {team} "
                    f"wheel with {load} assignment(s) "
                    f"on record{away}; remove it or "
                    "the wheel skips a ghost forever"
                )

    if not holdings:
        return (
            f"{name} leaves nothing jammed; either "
            "luck, or the sign of someone who "
            "released as they went"
        )
    lines = [
        f"offboarding {name}: {len(holdings)} "
        "holding(s), a checklist and not a report"
    ]
    lines.extend(holdings)
    lines.append(
        "each line is work to do; the worst time to "
        "discover a load-bearing name is after it "
        "stops answering"
    )
    return "\n".join(lines)

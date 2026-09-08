"""Graph diff: two repositories compared commit by commit, not vibe by vibe.

Sync debugging starts with the same sentence every time,
they should be identical, and the graph diff replaces the
should with counts: commits held by both, commits only
here, commits only there, each side's exclusives listed
with their subjects because an address alone sends the
debugger on a second errand the tool could have run. The
comparison is by address, which content addressing makes
exact, the same commit being the same address everywhere
or not the same commit at all. The verdict line uses the
mirror's vocabulary on purpose, identical or diverged,
with the direction of the divergence stated, ahead here,
ahead there, or both, because a fetch fixes one direction
and a push the other and both is the case that needs the
mirror's conversation about who overwrote whom.
"""

from __future__ import annotations

from keel.repo import Repo


def compare(
    ours: Repo, theirs: Repo
) -> dict[str, list[str]]:
    our_line = set(ours.graph.commits)
    their_line = set(theirs.graph.commits)
    return {
        "shared": sorted(our_line & their_line),
        "only_here": sorted(our_line - their_line),
        "only_there": sorted(their_line - our_line),
    }


def report(ours: Repo, theirs: Repo) -> str:
    sides = compare(ours, theirs)
    lines = [
        f"{len(sides['shared'])} commit(s) shared, "
        f"{len(sides['only_here'])} only here, "
        f"{len(sides['only_there'])} only there"
    ]
    for address in sides["only_here"]:
        subject = ours.graph.get(
            address
        ).message.splitlines()[0]
        lines.append(
            f"  only here: {address[:8]} {subject}"
        )
    for address in sides["only_there"]:
        subject = theirs.graph.get(
            address
        ).message.splitlines()[0]
        lines.append(
            f"  only there: {address[:8]} {subject}"
        )
    here = bool(sides["only_here"])
    there = bool(sides["only_there"])
    if not here and not there:
        lines.append(
            "identical to the address; they should "
            "be identical, and for once they are"
        )
    elif here and there:
        lines.append(
            "diverged both ways; a fetch fixes one "
            "direction and a push the other, and "
            "both is the mirror's conversation about "
            "who overwrote whom"
        )
    elif here:
        lines.append(
            "ahead here only; a push settles it"
        )
    else:
        lines.append(
            "ahead there only; a fetch settles it"
        )
    return "\n".join(lines)

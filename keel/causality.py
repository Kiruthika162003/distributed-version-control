"""Causality: no commit precedes its parents, and the gaps get named.

The sequence number is this history's clock, and the clock
has one law: every commit's number exceeds every parent's,
because a child older than its parent is not an anomaly to
log but a corruption to stop on, the graph's arrow of time
being the assumption under every walk, bisect, and era in
the workshop. The audit checks the law across the whole
graph and reports violations with both numbers shown, and
then it reads the quieter story: the gaps. Sequence numbers
are stamped once and never reused, so a gap in the
surviving numbers is the scar of a collection, and counting
the scars answers a question nobody thinks to ask until an
audit does, how much history has this repository digested
and let go. Scars are reported as history, not as findings,
since a repository that never collected anything has simply
never lived long enough to.
"""

from __future__ import annotations

from keel.errors import Corrupt
from keel.repo import Repo


def enforce(repo: Repo) -> str:
    violations: list[str] = []
    for address, commit in sorted(
        repo.graph.commits.items()
    ):
        for parent in commit.parents:
            held = repo.graph.commits.get(parent)
            if held is None:
                continue
            if held.sequence >= commit.sequence:
                violations.append(
                    f"{address[:8]} (seq "
                    f"{commit.sequence}) follows "
                    f"parent {parent[:8]} (seq "
                    f"{held.sequence}); a child older "
                    "than its parent is a corruption, "
                    "not an anomaly"
                )
    if violations:
        raise Corrupt(
            f"{len(violations)} arrow-of-time "
            "violation(s); every walk in the "
            "workshop assumes what just broke:\n"
            + "\n".join(
                f"  {line}" for line in violations
            )
        )
    return (
        f"{len(repo.graph.commits)} commit(s) obey "
        "the arrow of time"
    )


def scars(repo: Repo) -> str:
    held = sorted(
        commit.sequence
        for commit in repo.graph.commits.values()
    )
    if not held:
        return "no commits, no history, no scars"
    missing = []
    for expected in range(held[0], held[-1] + 1):
        if expected not in set(held):
            missing.append(expected)
    if not missing:
        return (
            f"{len(held)} commit(s), sequences "
            "unbroken; nothing has been let go"
        )
    runs = []
    start = missing[0]
    previous = missing[0]
    for number in missing[1:]:
        if number != previous + 1:
            runs.append((start, previous))
            start = number
        previous = number
    runs.append((start, previous))
    described = ", ".join(
        f"{low}" if low == high else f"{low}-{high}"
        for low, high in runs
    )
    return (
        f"{len(held)} commit(s) survive, "
        f"{len(missing)} sequence(s) digested and "
        f"let go ({described}); scars are history, "
        "not findings"
    )

"""The branch census: merged, stale, or active, and the verb for each.

Branch lists rot in a specific way: the merged ones linger
because deleting feels destructive, the abandoned ones linger
because nobody remembers whose they were, and the active ones
hide in the noise the other two make. The census sorts every
branch against the trunk into exactly three verdicts. Merged
means the tip is an ancestor of the trunk, so deletion loses
nothing and the prescription says so with the address that
proves it. Active means the tip is within the freshness
window of the trunk, measured in repository sequence numbers
rather than wall clocks, because this history orders events
by acceptance and not by whichever machine's clock drifted.
Stale means old and unmerged, the one verdict that earns a
question instead of an action, since unmerged work is either
abandoned or precious and no algorithm can tell which. The
sweep deletes only the merged, never the stale, because a
cleanup that guesses about precious is a cleanup that gets
turned off after its first mistake.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Invalid, Missing
from keel.repo import Repo

FRESHNESS_WINDOW = 5

VERDICT_MERGED = "merged"
VERDICT_STALE = "stale"
VERDICT_ACTIVE = "active"


@dataclass(frozen=True)
class BranchVerdict:
    branch: str
    verdict: str
    age: int
    prescription: str

    def line(self) -> str:
        return (
            f"  {self.branch}: {self.verdict} "
            f"(age {self.age}) - {self.prescription}"
        )


def census(
    repo: Repo,
    trunk: str = "main",
    window: int = FRESHNESS_WINDOW,
) -> list[BranchVerdict]:
    if window < 1:
        raise Invalid(
            "a freshness window below one calls every "
            "branch stale, including the trunk"
        )
    trunk_tip = repo.refs.branches.get(trunk)
    if trunk_tip is None:
        raise Missing(
            f"{trunk} is not a branch; a census needs a "
            "trunk to measure against"
        )
    trunk_sequence = repo.graph.get(trunk_tip).sequence
    verdicts: list[BranchVerdict] = []
    for branch, tip in sorted(repo.refs.branches.items()):
        if branch == trunk:
            continue
        age = max(
            0,
            trunk_sequence - repo.graph.get(tip).sequence,
        )
        if repo.graph.is_ancestor(tip, trunk_tip):
            verdicts.append(
                BranchVerdict(
                    branch=branch,
                    verdict=VERDICT_MERGED,
                    age=age,
                    prescription=(
                        f"delete; the trunk already holds "
                        f"{tip[:8]}"
                    ),
                )
            )
        elif age <= window:
            verdicts.append(
                BranchVerdict(
                    branch=branch,
                    verdict=VERDICT_ACTIVE,
                    age=age,
                    prescription="leave it alone",
                )
            )
        else:
            verdicts.append(
                BranchVerdict(
                    branch=branch,
                    verdict=VERDICT_STALE,
                    age=age,
                    prescription=(
                        "ask its owner; unmerged work is "
                        "either abandoned or precious, and "
                        "no algorithm can tell which"
                    ),
                )
            )
    return verdicts


def report(
    repo: Repo,
    trunk: str = "main",
    window: int = FRESHNESS_WINDOW,
) -> str:
    verdicts = census(repo, trunk, window)
    if not verdicts:
        return f"only {trunk} exists; nothing to judge"
    counted = {
        VERDICT_MERGED: 0,
        VERDICT_STALE: 0,
        VERDICT_ACTIVE: 0,
    }
    for verdict in verdicts:
        counted[verdict.verdict] += 1
    lines = [
        f"{counted[VERDICT_MERGED]} merged, "
        f"{counted[VERDICT_STALE]} stale, "
        f"{counted[VERDICT_ACTIVE]} active "
        f"(window {window})"
    ]
    lines.extend(verdict.line() for verdict in verdicts)
    return "\n".join(lines)


def sweep(
    repo: Repo,
    trunk: str = "main",
    window: int = FRESHNESS_WINDOW,
) -> str:
    verdicts = census(repo, trunk, window)
    deleted = []
    spared = 0
    for verdict in verdicts:
        if verdict.verdict == VERDICT_MERGED:
            repo.refs.delete(verdict.branch)
            deleted.append(verdict.branch)
        elif verdict.verdict == VERDICT_STALE:
            spared += 1
    summary = (
        f"swept {len(deleted)} merged branch(es), spared "
        f"{spared} stale one(s); a cleanup that guesses "
        "about precious gets turned off after its first "
        "mistake"
    )
    if deleted:
        return summary + "\n  gone: " + ", ".join(deleted)
    return summary

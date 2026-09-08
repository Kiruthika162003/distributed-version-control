"""The conflict forecast: which open branches will fight when they meet.

Conflicts are cheapest the day before they happen, and the
forecast buys that day: every pair of open branches is
dry-merged, nothing committed, and the meetings are sorted
into clean and contested with the fighting paths named.
Pairs that cannot meet at all, strangers with no common
ancestor or criss-cross histories the base finder refuses,
are reported in those words rather than folded into the
conflict column, because cannot meet and will fight need
different calendars. The advice at the end is the reread:
a path contested by several pairs is the town square, and
the town square does not get less contested by waiting, so
its claimants integrate soonest or the merge queue decides
by arrival, which the queue's own witness proved is not
the same thing as deciding by merit.
"""

from __future__ import annotations

from itertools import combinations

from keel.errors import Invalid, KeelError
from keel.merge import merge_commits
from keel.repo import Repo


def forecast(
    repo: Repo, branches: list[str]
) -> list[tuple[str, str, str, tuple[str, ...]]]:
    if len(branches) < 2:
        raise Invalid(
            "a forecast needs at least two branches; "
            "one branch meets nobody"
        )
    for branch in branches:
        if branch not in repo.refs.branches:
            raise Invalid(
                f"{branch} is not a branch here"
            )
    meetings = []
    for left, right in combinations(
        sorted(branches), 2
    ):
        left_tip = repo.refs.branches[left]
        right_tip = repo.refs.branches[right]
        try:
            outcome = merge_commits(
                repo, left_tip, right_tip
            )
        except KeelError as refusal:
            meetings.append(
                (
                    left,
                    right,
                    "cannot meet",
                    (str(refusal).split(";")[0],),
                )
            )
            continue
        if outcome.is_clean():
            meetings.append((left, right, "clean", ()))
        else:
            meetings.append(
                (
                    left,
                    right,
                    "will fight",
                    tuple(sorted(outcome.conflicts)),
                )
            )
    return meetings


def render(repo: Repo, branches: list[str]) -> str:
    meetings = forecast(repo, branches)
    lines = [
        f"{len(branches)} open branch(es), "
        f"{len(meetings)} meeting(s) forecast:"
    ]
    contested_by: dict[str, int] = {}
    for left, right, verdict, detail in meetings:
        if verdict == "clean":
            lines.append(
                f"  {left} + {right}: clean meeting"
            )
        elif verdict == "will fight":
            lines.append(
                f"  {left} + {right}: will fight over "
                + ", ".join(detail)
            )
            for path in detail:
                contested_by[path] = (
                    contested_by.get(path, 0) + 1
                )
        else:
            lines.append(
                f"  {left} + {right}: cannot meet "
                f"({detail[0]})"
            )
    squares = sorted(
        path
        for path, count in contested_by.items()
        if count >= 2
    )
    for path in squares:
        lines.append(
            f"advice: {path} is the town square, "
            f"contested in {contested_by[path]} "
            "meeting(s); its claimants integrate "
            "soonest, or the queue decides by arrival"
        )
    if not squares and contested_by:
        lines.append(
            "advice: each fight has exactly two "
            "claimants; pair them off and settle"
        )
    if not contested_by:
        lines.append(
            "advice: none; enjoy a forecast with no "
            "weather in it"
        )
    return "\n".join(lines)

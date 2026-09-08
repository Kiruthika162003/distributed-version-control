"""The crow's nest: what is approaching, called before it arrives.

The night watch reports what is already wrong; the crow's
nest reports what will be, which is the cheaper report by
exactly the cost of the incident. Three approaches are
watched. Branches drifting toward the staleness window are
called at two-thirds of the way there, because the
conversation about abandoned work is easiest while its
author still remembers it. Deprecations nearing their
deadline are called in the last third of their countdown,
the migration that will miss its date being visible well
before it misses. Budgets past eighty percent of their
ceiling are called with the exact headroom left, since the
overdraft refusal downstream is fairer when this warning
preceded it. Every call names the threshold that triggered
it, and a quiet nest reports clear horizons in as many
words, the lookout who only ever cries alarm being a
lookout nobody believes.
"""

from __future__ import annotations

from keel.budgets import BudgetBook
from keel.deprecations import DeprecationLedger
from keel.repo import Repo
from keel.stalebranches import FRESHNESS_WINDOW

APPROACH_SHARE = 2 / 3
BUDGET_ALARM = 0.8


def watch(
    repo: Repo,
    trunk: str = "main",
    window: int = FRESHNESS_WINDOW,
    deprecations: DeprecationLedger | None = None,
    budgets: BudgetBook | None = None,
) -> str:
    calls: list[str] = []
    trunk_tip = repo.refs.branches[trunk]
    trunk_sequence = repo.graph.get(
        trunk_tip
    ).sequence
    threshold = int(window * APPROACH_SHARE)
    for branch, tip in sorted(
        repo.refs.branches.items()
    ):
        if branch == trunk:
            continue
        if repo.graph.is_ancestor(tip, trunk_tip):
            continue
        age = trunk_sequence - repo.graph.get(
            tip
        ).sequence
        if threshold <= age <= window:
            calls.append(
                f"  {branch} is {age} of {window} "
                "toward stale; the conversation is "
                "easiest while its author still "
                "remembers the work"
            )
    if deprecations is not None:
        now = trunk_sequence
        for path in sorted(deprecations.notices):
            notice = deprecations.notices[path]
            runway = notice.deadline - notice.noticed_at
            burned = now - notice.noticed_at
            if (
                now <= notice.deadline
                and runway > 0
                and burned / runway >= APPROACH_SHARE
            ):
                calls.append(
                    f"  {path} has burned {burned} of "
                    f"{runway} toward its deadline; "
                    "the migration that will miss its "
                    "date is visible before it misses"
                )
    if budgets is not None:
        files = repo.head_files()
        for prefix, ceiling in sorted(
            budgets.allowances.items()
        ):
            spent = sum(
                len(content)
                for path, content in files.items()
                if path.startswith(prefix)
            )
            if spent / ceiling >= BUDGET_ALARM and (
                spent <= ceiling
            ):
                calls.append(
                    f"  {prefix} stands at {spent} of "
                    f"{ceiling} byte(s), past the "
                    "eighty percent line with "
                    f"{ceiling - spent} of headroom; "
                    "the overdraft refusal downstream "
                    "is fairer for this warning"
                )
    if not calls:
        return (
            "the crow's nest reports clear horizons; "
            "a lookout who only ever cries alarm is "
            "a lookout nobody believes"
        )
    return "\n".join(
        [
            f"{len(calls)} approach(es) called "
            "before arrival:",
            *calls,
        ]
    )

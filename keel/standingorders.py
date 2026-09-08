"""Standing orders: every rule currently in force, on one board.

The journals say what happened and the audits say what
drifted; the standing orders say what is in force right
now, which is the page a person needs before they act
rather than after. The board lists the freezes with their
reasons and askable names, the locks with their holders,
the declared absences, the deprecation notices still open,
and the budget allowances with their ceilings, each in one
line, because standing state that takes a paragraph to
state has already stopped being consulted. Absent organs
contribute nothing and are not mentioned, this board being
the one page in the workshop that skips the not-checked
note on purpose: standing orders are what binds, and the
absence of a rule binds nobody, which needs no line to
say. The empty board is the sailor's favorite reading:
no standing orders, act on judgment.
"""

from __future__ import annotations

from keel.budgets import BudgetBook
from keel.deprecations import DeprecationLedger
from keel.filelocks import LockOffice
from keel.freeze import FreezeBoard
from keel.reviewrotation import Wheel


def board(
    freezes: FreezeBoard | None = None,
    locks: LockOffice | None = None,
    wheel: Wheel | None = None,
    deprecations: DeprecationLedger | None = None,
    budgets: BudgetBook | None = None,
) -> str:
    orders: list[str] = []
    if freezes is not None:
        for branch in sorted(freezes.freezes):
            standing = freezes.freezes[branch]
            orders.append(
                f"  {branch} is frozen: "
                f"{standing.reason} (ask "
                f"{standing.frozen_by})"
            )
    if locks is not None:
        for path in sorted(locks.locks):
            lock = locks.locks[path]
            orders.append(
                f"  {path} is locked by "
                f"{lock.holder}: {lock.reason}"
            )
    if wheel is not None:
        for member in sorted(wheel.away):
            orders.append(
                f"  {member} is away: "
                f"{wheel.away[member]}"
            )
    if deprecations is not None:
        for path in sorted(deprecations.notices):
            notice = deprecations.notices[path]
            orders.append(
                f"  {path} is deprecated for "
                f"{notice.successor}, gone by "
                f"sequence {notice.deadline}"
            )
    if budgets is not None:
        for prefix in sorted(budgets.allowances):
            orders.append(
                f"  {prefix} is budgeted at "
                f"{budgets.allowances[prefix]} byte(s)"
            )
    if not orders:
        return (
            "no standing orders; act on judgment"
        )
    return "\n".join(
        [
            f"{len(orders)} standing order(s) in "
            "force:",
            *orders,
        ]
    )

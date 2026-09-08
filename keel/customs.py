"""Customs: the material gates, cleared together or itemized together.

The gatekeeper judges the social claims of a landing,
reviews and freezes and routing; customs judges the
material ones: whether the submitter may write these paths
at all, whether any of them is locked by someone mid-turn,
and whether the bytes fit the budgets. The gates run in
that order because it is the order of expense to fix,
membership is an afternoon, a lock is a conversation, and
a budget is a diet, but no gate stops the others from
speaking, the one-trip rule holding here as firmly as at
the gatekeeper, since a submitter who fixes the ACL and
then discovers the lock has been taught to dread the next
push. Declarations are optional organ by organ and absent
ones are named as waved through, not silently passed,
because the difference between no rule and no check is
the difference between open and unwatched.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.acl import AccessTable
from keel.budgets import BudgetBook
from keel.errors import Conflict, Invalid
from keel.filelocks import LockOffice
from keel.repo import Repo


@dataclass
class Customs:
    repo: Repo
    access: AccessTable | None = None
    locks: LockOffice | None = None
    budgets: BudgetBook | None = None

    def clear(
        self,
        who: str,
        proposed: dict[str, bytes],
    ) -> str:
        touched = sorted(
            path
            for path in set(proposed)
            | set(self.repo.head_files())
            if proposed.get(path)
            != self.repo.head_files().get(path)
        )
        verdicts: list[tuple[str, str, bool]] = []

        if self.access is None:
            verdicts.append(
                ("access", "no table; waved through", False)
            )
        else:
            try:
                verdicts.append(
                    (
                        "access",
                        self.access.check(who, touched),
                        False,
                    )
                )
            except Invalid as refusal:
                verdicts.append(
                    ("access", str(refusal), True)
                )

        if self.locks is None:
            verdicts.append(
                ("locks", "no office; waved through", False)
            )
        else:
            try:
                verdicts.append(
                    (
                        "locks",
                        self.locks.check_landing(
                            who, touched
                        ),
                        False,
                    )
                )
            except Conflict as refusal:
                verdicts.append(
                    ("locks", str(refusal), True)
                )

        if self.budgets is None:
            verdicts.append(
                (
                    "budgets",
                    "no book; waved through",
                    False,
                )
            )
        else:
            try:
                verdicts.append(
                    (
                        "budgets",
                        self.budgets.check_landing(
                            self.repo, proposed
                        ),
                        False,
                    )
                )
            except Conflict as refusal:
                verdicts.append(
                    ("budgets", str(refusal), True)
                )

        failures = [
            gate
            for gate, _verdict, failed in verdicts
            if failed
        ]
        lines = []
        if failures:
            lines.append(
                f"customs holds the shipment: "
                f"{len(failures)} gate(s) object "
                f"({', '.join(failures)})"
            )
        else:
            lines.append(
                f"customs clears {who}: "
                f"{len(touched)} path(s) through all "
                "three gates"
            )
        for gate, verdict, failed in verdicts:
            mark = "HOLD" if failed else "ok"
            first_line = verdict.splitlines()[0]
            lines.append(
                f"  {gate}: [{mark}] {first_line}"
            )
        lines.append(
            "membership is an afternoon, a lock is a "
            "conversation, a budget is a diet; every "
            "gate spoke either way"
        )
        page = "\n".join(lines)
        if failures:
            raise Conflict(page)
        return page

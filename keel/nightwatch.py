"""The night watch: every governance ledger walked once, before morning.

The health report examines the data; the night watch
examines the promises, the owners file against the tree,
the naming policy against the branch list, the deprecation
notices against the calendar, the budgets against the
spend, because governance rots quietly, a rule at a time,
and the rot is only visible when somebody walks all the
ledgers in one round. Each section keeps its ledger's own
voice for the health report's old reason, and organs not
configured are logged as not on the rounds tonight, never
skipped silently, since a watch that cannot say what it
did not check is a watch that slept. The closing count is
of ledgers with findings rather than findings themselves,
one drifting ledger being a chore while four is a
management conversation, and the number tells you which
meeting to book.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.branchpolicy import NamingPolicy
from keel.budgets import BudgetBook
from keel.codeowners import OwnersFile
from keel.deprecations import DeprecationLedger
from keel.repo import Repo


@dataclass
class NightWatch:
    repo: Repo
    owners: OwnersFile | None = None
    policy: NamingPolicy | None = None
    deprecations: DeprecationLedger | None = None
    budgets: BudgetBook | None = None

    def rounds(self) -> str:
        sections: list[str] = []
        drifting = 0

        if self.owners is None:
            sections.append(
                "owners: not on the rounds tonight"
            )
        else:
            page = self.owners.audit(
                sorted(self.repo.head_files())
            )
            sections.append("owners:\n  " + page.replace(
                "\n", "\n  "
            ))
            if not page.startswith("0 orphan(s)"):
                drifting += 1

        if self.policy is None:
            sections.append(
                "naming: not on the rounds tonight"
            )
        else:
            page = self.policy.audit(self.repo)
            sections.append(
                "naming:\n  " + page.replace("\n", "\n  ")
            )
            headline = page.splitlines()[0]
            if " 0 unlabeled" not in headline:
                drifting += 1

        if self.deprecations is None:
            sections.append(
                "deprecations: not on the rounds "
                "tonight"
            )
        else:
            page = self.deprecations.audit()
            sections.append(
                "deprecations:\n  "
                + page.replace("\n", "\n  ")
            )
            if "OVERDUE" in page or "touch(es) since" in (
                page
            ):
                drifting += 1

        if self.budgets is None:
            sections.append(
                "budgets: not on the rounds tonight"
            )
        else:
            page = self.budgets.headroom(self.repo)
            sections.append(
                "budgets:\n  "
                + page.replace("\n", "\n  ")
            )
            if "0 of room" in page:
                drifting += 1

        if drifting == 0:
            closing = (
                "every ledger walked, none drifting; "
                "the promises still describe the place"
            )
        else:
            closing = (
                f"{drifting} ledger(s) drifting; one "
                "is a chore, four is a management "
                "conversation, and the number tells "
                "you which meeting to book"
            )
        return "\n\n".join(
            ["the night watch:", *sections, closing]
        )

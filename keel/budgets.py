"""Size budgets: directories on an allowance, spent bytes accounted.

Repositories do not get heavy in one commit; they get heavy
in four hundred reasonable ones, and the budget is the
counterweight: a directory gets a byte allowance, every
landing is priced against it, and the landing that would
break the allowance bounces with the arithmetic shown,
current spend plus this change against the ceiling, because
a refusal with the numbers is a negotiation and a refusal
without them is a wall. Headroom reporting is half the
value, the budget that answers how much room is left before
anyone hits it turns the panic cleanup into a planned diet.
Budgets are refused on nested directories for the owners
file's old reason, one byte billed to two allowances makes
both books wrong, and the unbudgeted remainder is priced at
zero on purpose: a budget system that taxes everything
teaches people to fight the system instead of the growth.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Conflict, Invalid
from keel.repo import Repo


@dataclass
class BudgetBook:
    allowances: dict[str, int] = field(
        default_factory=dict
    )

    def set_allowance(
        self, prefix: str, ceiling: int
    ) -> str:
        if not prefix.endswith("/"):
            raise Invalid(
                f"{prefix!r} is not a directory; "
                "budgets cover directories, and "
                "directories end with a slash"
            )
        if ceiling < 1:
            raise Invalid(
                "a ceiling below one byte is a ban "
                "wearing a ledger"
            )
        for held in self.allowances:
            if held.startswith(prefix) or (
                prefix.startswith(held)
            ):
                raise Invalid(
                    f"{prefix} nests with {held}; one "
                    "byte billed to two allowances "
                    "makes both books wrong"
                )
        self.allowances[prefix] = ceiling
        return (
            f"{prefix} allowed {ceiling} byte(s)"
        )

    def _spend(
        self, files: dict[str, bytes], prefix: str
    ) -> int:
        return sum(
            len(content)
            for path, content in files.items()
            if path.startswith(prefix)
        )

    def check_landing(
        self,
        repo: Repo,
        proposed: dict[str, bytes],
    ) -> str:
        current = repo.head_files()
        overdrafts: list[str] = []
        for prefix, ceiling in sorted(
            self.allowances.items()
        ):
            spent = self._spend(current, prefix)
            would_be = self._spend(proposed, prefix)
            if would_be > ceiling:
                overdrafts.append(
                    f"  {prefix}: {spent} now, "
                    f"{would_be} after this change, "
                    f"ceiling {ceiling}; over by "
                    f"{would_be - ceiling}"
                )
        if overdrafts:
            raise Conflict(
                f"{len(overdrafts)} allowance(s) "
                "broken; a refusal with the numbers "
                "is a negotiation:\n"
                + "\n".join(overdrafts)
            )
        return (
            f"all {len(self.allowances)} allowance(s) "
            "honored"
        )

    def headroom(self, repo: Repo) -> str:
        if not self.allowances:
            return (
                "no allowances set; growth is "
                "currently free and unwatched"
            )
        current = repo.head_files()
        lines = [
            f"{len(self.allowances)} allowance(s):"
        ]
        for prefix, ceiling in sorted(
            self.allowances.items()
        ):
            spent = self._spend(current, prefix)
            room = ceiling - spent
            share = (
                spent * 100 // ceiling
                if ceiling
                else 100
            )
            lines.append(
                f"  {prefix}: {spent} of {ceiling} "
                f"byte(s) spent ({share}%), "
                f"{room} of room"
            )
        lines.append(
            "headroom turns the panic cleanup into "
            "a planned diet"
        )
        return "\n".join(lines)

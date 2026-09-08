"""Ref transactions: several pointers move together or nobody moves.

A release that advances main, retags stable, and retires a
feature branch is one decision, and applying it as three
commands invents two new failure states, the half-applied
release being the worse of them because it looks like a
whole one from most angles. The transaction stages every
move first and validates the batch as a unit, existence,
fast-forward unless force is declared per move, no branch
named twice, and only a batch that validates entirely is
applied at all, the all-or-nothing that makes the decision
atomic again. Validation failures name every objection at
once in the standing one-trip tradition, and the applied
receipt lists every pointer with its journey, because a
transaction that reports success without the itinerary
teaches operators to stop reading receipts exactly when
receipts matter most.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid
from keel.repo import Repo


@dataclass(frozen=True)
class RefMove:
    branch: str
    target: str
    force: bool = False
    delete: bool = False


@dataclass
class RefTransaction:
    repo: Repo
    moves: list[RefMove] = field(default_factory=list)

    def stage(
        self,
        branch: str,
        target: str = "",
        force: bool = False,
        delete: bool = False,
    ) -> str:
        self.moves.append(
            RefMove(
                branch=branch,
                target=target,
                force=force,
                delete=delete,
            )
        )
        verb = "delete" if delete else "move"
        return f"staged: {verb} {branch}"

    def _objections(self) -> list[str]:
        found: list[str] = []
        seen: set[str] = set()
        for move in self.moves:
            if move.branch in seen:
                found.append(
                    f"{move.branch} is named twice; a "
                    "pointer moved twice in one "
                    "decision is two decisions"
                )
                continue
            seen.add(move.branch)
            held = self.repo.refs.branches.get(
                move.branch
            )
            if move.delete:
                if held is None:
                    found.append(
                        f"{move.branch} does not exist "
                        "to delete"
                    )
                continue
            if move.target not in (
                self.repo.graph.commits
            ):
                found.append(
                    f"{move.branch} targets "
                    f"{move.target[:8]}, which is not "
                    "a commit here"
                )
                continue
            if (
                held is not None
                and not move.force
                and not self.repo.graph.is_ancestor(
                    held, move.target
                )
            ):
                found.append(
                    f"{move.branch} would rewind from "
                    f"{held[:8]} without force "
                    "declared; declare it per move or "
                    "do not do it"
                )
        return found

    def apply(self) -> str:
        if not self.moves:
            raise Invalid(
                "an empty transaction decides nothing"
            )
        objections = self._objections()
        if objections:
            raise Invalid(
                f"{len(objections)} objection(s), "
                "nothing applied; the half-applied "
                "release looks whole from most "
                "angles:\n"
                + "\n".join(
                    f"  {line}" for line in objections
                )
            )
        itinerary: list[str] = []
        for move in self.moves:
            held = self.repo.refs.branches.get(
                move.branch
            )
            if move.delete:
                self.repo.refs.delete(move.branch)
                itinerary.append(
                    f"  {move.branch}: retired from "
                    f"{held[:8]}"
                )
            elif held is None:
                self.repo.refs.create_branch(
                    move.branch, move.target
                )
                itinerary.append(
                    f"  {move.branch}: born at "
                    f"{move.target[:8]}"
                )
            else:
                self.repo.refs.move(
                    move.branch,
                    move.target,
                    reason="ref transaction",
                    force=move.force,
                )
                itinerary.append(
                    f"  {move.branch}: {held[:8]} -> "
                    f"{move.target[:8]}"
                )
        self.moves.clear()
        return (
            f"applied {len(itinerary)} move(s) as one "
            "decision:\n" + "\n".join(itinerary)
        )

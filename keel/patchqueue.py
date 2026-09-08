"""The patch queue: named changes worn in layers over the head commit.

A patch here is a reversible garment: it records what each
path looked like before and what it becomes after, so
pushing verifies the ground it expects and popping restores
it exactly, and neither direction ever guesses. The stack
discipline is the honest part: patches apply in series
order and remove in reverse, because layers that interleave
stop being reversible the day two of them touch one path.
Every push checks that the world still matches the patch's
recorded before-state, and a mismatch is refused with the
path named rather than applied approximately, since a patch
that lands on moved ground is a merge conducted by
sleepwalking. Folding retires the bottom patch into a real
commit, the queue's only exit into history, and it verifies
the same ground twice, once against the view and once
against the head, because the moment of becoming permanent
is the wrong moment to discover drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Conflict, Invalid, Missing
from keel.repo import Repo


@dataclass
class Patch:
    name: str
    before: dict[str, bytes | None]
    after: dict[str, bytes | None]
    applied: bool = False


@dataclass
class PatchQueue:
    repo: Repo
    series: list[Patch] = field(default_factory=list)

    def view(self) -> dict[str, bytes]:
        files = dict(self.repo.head_files())
        for patch in self.series:
            if not patch.applied:
                continue
            for path, content in patch.after.items():
                if content is None:
                    files.pop(path, None)
                else:
                    files[path] = content
        return files

    def new_patch(
        self, name: str, changes: dict[str, bytes | None]
    ) -> str:
        if not name.strip():
            raise Invalid("a patch needs a name to answer to")
        if any(
            patch.name == name for patch in self.series
        ):
            raise Invalid(
                f"{name} is already in the series; two "
                "garments with one name swap in the dark"
            )
        if not changes:
            raise Invalid(
                f"{name} changes nothing; an empty patch "
                "is a name for a mood"
            )
        current = self.view()
        before = {
            path: current.get(path) for path in changes
        }
        self.series.append(
            Patch(name=name, before=before, after=changes)
        )
        return (
            f"{name} added to the series, "
            f"{len(changes)} path(s), not yet worn"
        )

    def _next_unapplied(self) -> Patch:
        for patch in self.series:
            if not patch.applied:
                return patch
        raise Missing(
            "every patch is already worn; the queue "
            "has no next"
        )

    def _top_applied(self) -> Patch:
        for patch in reversed(self.series):
            if patch.applied:
                return patch
        raise Missing(
            "nothing is worn; the queue has no top"
        )

    def push_patch(self) -> str:
        patch = self._next_unapplied()
        current = self.view()
        for path, expected in patch.before.items():
            if current.get(path) != expected:
                raise Conflict(
                    f"{patch.name} expected different "
                    f"ground at {path}; a patch that lands "
                    "on moved ground is a merge conducted "
                    "by sleepwalking"
                )
        patch.applied = True
        return f"{patch.name} worn"

    def pop_patch(self) -> str:
        patch = self._top_applied()
        current = self.view()
        for path, held in patch.after.items():
            if current.get(path) != held:
                raise Conflict(
                    f"{patch.name} cannot come off "
                    f"cleanly; {path} no longer matches "
                    "what the patch put there"
                )
        patch.applied = False
        return f"{patch.name} set aside, ground restored"

    def refresh(
        self, changes: dict[str, bytes | None]
    ) -> str:
        patch = self._top_applied()
        for path in changes:
            if path not in patch.after:
                raise Invalid(
                    f"{path} is not part of {patch.name}; "
                    "a refresh edits the garment, not the "
                    "wardrobe"
                )
        patch.after.update(changes)
        return f"{patch.name} refreshed in place"

    def fold_bottom(self) -> str:
        bottom = next(
            (
                patch
                for patch in self.series
                if patch.applied
            ),
            None,
        )
        if bottom is None:
            raise Missing("nothing worn, nothing to fold")
        head = dict(self.repo.head_files())
        for path, expected in bottom.before.items():
            if head.get(path) != expected:
                raise Conflict(
                    f"the head moved under {bottom.name} "
                    f"at {path}; permanence is the wrong "
                    "moment to discover drift"
                )
        for path, content in bottom.after.items():
            if content is None:
                head.pop(path, None)
            else:
                head[path] = content
        self.repo.commit(head, f"patch: {bottom.name}")
        self.series.remove(bottom)
        return (
            f"{bottom.name} folded into history; the "
            "queue's only exit"
        )

    def series_report(self) -> str:
        if not self.series:
            return "an empty series; the head stands alone"
        lines = [f"{len(self.series)} patch(es) in series:"]
        for patch in self.series:
            marker = "worn" if patch.applied else "waiting"
            lines.append(
                f"  {patch.name}: {marker}, "
                f"{len(patch.after)} path(s)"
            )
        return "\n".join(lines)

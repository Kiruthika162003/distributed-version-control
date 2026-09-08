"""The mirror: a faithful copy that says so the moment it stops being one.

A mirror has one job and one failure mode. The job is
making the replica's branch table equal the source's, and
sync does it with the usual machinery, shipping only what
the replica lacks and journaling every pointer it moves.
The failure mode is the push that lands on the mirror
directly, work committed to a copy that the next sync would
silently shred, and the defense is memory: the mirror
records where it left every branch, and a branch found
elsewhere at sync time stops the whole sync with the drift
named, because a mirror that overwrites contributions is a
paper shredder wearing a sign that says copier. Reclaim is
the explicit override, one branch at a time, loud in the
journal, so discarding someone's misdirected work is a
decision with a name on it rather than a side effect of
the schedule.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Conflict, Missing
from keel.repo import Repo
from keel.transfer import negotiate, receive


@dataclass
class Mirror:
    source: Repo
    replica: Repo
    last_set: dict[str, str] = field(default_factory=dict)
    syncs: int = 0
    journal: list[str] = field(default_factory=list)

    def _drifted(self) -> list[str]:
        drifted = []
        for branch, recorded in self.last_set.items():
            held = self.replica.refs.branches.get(branch)
            if held != recorded:
                drifted.append(branch)
        for branch in self.replica.refs.branches:
            if branch not in self.last_set:
                drifted.append(branch)
        return sorted(set(drifted))

    def sync(self) -> str:
        drifted = self._drifted()
        if drifted:
            raise Conflict(
                "the mirror was written to directly on "
                + ", ".join(drifted)
                + "; syncing now would shred that work, "
                "and a mirror that overwrites "
                "contributions is a paper shredder "
                "wearing a sign that says copier. "
                "Reclaim each branch by name to proceed"
            )
        wants = list(self.source.refs.branches.values())
        haves = list(self.replica.graph.commits)
        shipped = 0
        if wants:
            batch = negotiate(
                self.source, wants=wants, haves=haves
            )
            receive(self.replica.store, batch)
            for address, (kind, _payload) in (
                batch.objects.items()
            ):
                if kind == "commit":
                    self.replica.graph.commits[address] = (
                        self.source.graph.get(address)
                    )
            shipped = batch.size()
        moved = 0
        for branch, tip in sorted(
            self.source.refs.branches.items()
        ):
            held = self.replica.refs.branches.get(branch)
            if held == tip:
                continue
            if held is None:
                self.replica.refs.create_branch(
                    branch, tip
                )
            else:
                self.replica.refs.move(
                    branch,
                    tip,
                    reason="mirror sync",
                    force=True,
                )
            self.last_set[branch] = tip
            moved += 1
        for branch in list(self.replica.refs.branches):
            if branch not in self.source.refs.branches:
                self.replica.refs.delete(branch)
                self.last_set.pop(branch, None)
                self.journal.append(
                    f"retired {branch}; the source no "
                    "longer has it"
                )
                moved += 1
        for branch, tip in (
            self.replica.refs.branches.items()
        ):
            self.last_set[branch] = tip
        self.syncs += 1
        self.journal.append(
            f"sync #{self.syncs}: {shipped} object(s) "
            f"shipped, {moved} pointer(s) moved"
        )
        return self.journal[-1]

    def reclaim(self, branch: str) -> str:
        held = self.replica.refs.branches.get(branch)
        if held is None and branch not in self.last_set:
            raise Missing(
                f"{branch} shows no drift to reclaim"
            )
        recorded = self.last_set.get(branch)
        if held == recorded and held is not None:
            raise Missing(
                f"{branch} is exactly where the mirror "
                "left it; nothing to reclaim"
            )
        entry = (
            f"RECLAIMED {branch}: direct write at "
            f"{(held or 'deleted')[:8]} discarded by "
            "decision, not by schedule"
        )
        if held is not None:
            self.last_set[branch] = held
        else:
            self.last_set.pop(branch, None)
        self.journal.append(entry)
        return entry

    def verify(self) -> str:
        drifts = []
        for branch, tip in sorted(
            self.source.refs.branches.items()
        ):
            held = self.replica.refs.branches.get(branch)
            if held != tip:
                drifts.append(
                    f"  {branch}: source {tip[:8]}, "
                    f"replica "
                    f"{held[:8] if held else 'absent'}"
                )
        for branch in sorted(self.replica.refs.branches):
            if branch not in self.source.refs.branches:
                drifts.append(
                    f"  {branch}: replica only; the "
                    "source never heard of it"
                )
        if not drifts:
            return (
                "faithful: every branch matches to the "
                "address"
            )
        return "\n".join(
            [f"{len(drifts)} drift(s):", *drifts]
        )

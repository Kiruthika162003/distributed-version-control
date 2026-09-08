"""The merge queue: land in line, tested against what actually landed.

The failure the queue exists to prevent has a shape: two
branches each pass their checks against the trunk they saw,
both land, and the trunk breaks because nobody tested the
combination. The queue closes that gap by retesting every
entry against the trunk as it stands when the entry's turn
arrives, accumulated landings included, so the thing that
gets checked is the thing that ships. Bounces are narrated
and non-blocking: an entry that conflicts with what landed
ahead of it steps out of line with the colliding paths
named, and the entries behind it keep moving, because one
person's conflict is not a queue outage. The gate is the
caller's to supply and the queue's to obey, its refusal
reason quoted in the receipt, since a queue that summarizes
failures as failed teaches submitters to resubmit blind.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from keel.errors import Invalid, Missing
from keel.merge import commit_merge, merge_commits
from keel.repo import Repo

STATE_WAITING = "waiting"
STATE_LANDED = "landed"
STATE_BOUNCED = "bounced"

Gate = Callable[[dict[str, bytes]], str | None]


@dataclass
class QueueEntry:
    branch: str
    submitter: str
    position: int
    state: str = STATE_WAITING
    note: str = ""

    def line(self) -> str:
        tail = f" ({self.note})" if self.note else ""
        return (
            f"  #{self.position} {self.branch} by "
            f"{self.submitter}: {self.state}{tail}"
        )


@dataclass
class MergeQueue:
    repo: Repo
    trunk: str = "main"
    entries: list[QueueEntry] = field(default_factory=list)
    next_position: int = 1

    def submit(self, branch: str, submitter: str) -> str:
        if branch == self.trunk:
            raise Invalid(
                f"{branch} is the trunk; the queue lands "
                "onto it, not it onto itself"
            )
        if branch not in self.repo.refs.branches:
            raise Missing(f"{branch} is not a branch here")
        for entry in self.entries:
            if (
                entry.branch == branch
                and entry.state == STATE_WAITING
            ):
                raise Invalid(
                    f"{branch} already waits at "
                    f"#{entry.position}; queueing twice "
                    "lands once and confuses twice"
                )
        entry = QueueEntry(
            branch=branch,
            submitter=submitter,
            position=self.next_position,
        )
        self.next_position += 1
        self.entries.append(entry)
        return (
            f"{branch} queued at #{entry.position}; it "
            "will be tested against the trunk as it "
            "stands at its turn, not as it stands now"
        )

    def process(self, gate: Gate) -> str:
        waiting = [
            entry
            for entry in self.entries
            if entry.state == STATE_WAITING
        ]
        if not waiting:
            return "the queue is empty; nothing to land"
        self.repo.refs.checkout(self.trunk)
        landed = 0
        bounced = 0
        for entry in waiting:
            trunk_tip = self.repo.refs.branches[self.trunk]
            branch_tip = self.repo.refs.branches[
                entry.branch
            ]
            outcome = merge_commits(
                self.repo, trunk_tip, branch_tip
            )
            if not outcome.is_clean():
                paths = ", ".join(sorted(outcome.conflicts))
                entry.state = STATE_BOUNCED
                entry.note = (
                    f"conflicts with what landed ahead "
                    f"on {paths}"
                )
                bounced += 1
                continue
            refusal = gate(dict(outcome.merged_files))
            if refusal is not None:
                entry.state = STATE_BOUNCED
                entry.note = f"gate said: {refusal}"
                bounced += 1
                continue
            merged = commit_merge(
                self.repo,
                outcome,
                f"land {entry.branch} (queue "
                f"#{entry.position})",
            )
            entry.state = STATE_LANDED
            entry.note = f"as {merged.address[:8]}"
            landed += 1
        return (
            f"processed {len(waiting)} entr(ies): "
            f"{landed} landed, {bounced} bounced; every "
            "landing was tested against the trunk it "
            "actually joined"
        )

    def report(self) -> str:
        if not self.entries:
            return "an empty queue; the trunk moves alone"
        lines = [f"queue for {self.trunk}:"]
        lines.extend(
            entry.line() for entry in self.entries
        )
        return "\n".join(lines)

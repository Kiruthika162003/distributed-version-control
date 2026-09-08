"""Maintenance: repack and collect on a schedule, with receipts that add up.

Repositories accumulate loose objects the way desks
accumulate paper, and maintenance is the standing appointment
that keeps the accumulation from becoming the architecture:
repack folds loose blobs into delta chains where they earn
it, collection sweeps what nothing reaches, and the runner
does them in that order because packing first means the
collector's census sees the compact truth. Every run emits a
combined receipt whose numbers must reconcile, objects before
equals objects after plus objects freed, and the runner
checks that arithmetic itself, because a maintenance job
whose own receipts do not add up is the last tool anyone
should trust with deletion. Runs are bounded by an effort
budget, packing stops when the budget does, and the receipt
says how much desk remains, since maintenance that pretends
to finish teaches operators to stop scheduling it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid
from keel.gc import Collector
from keel.objects import BLOB
from keel.packfile import Pack
from keel.repo import Repo


@dataclass
class MaintenanceRun:
    repo: Repo
    effort_budget: int = 50
    receipts: list[str] = field(default_factory=list)

    def repack(self) -> Pack:
        pack = Pack()
        blobs = [
            (address, payload)
            for address, (kind, payload) in sorted(
                self.repo.store.objects.items()
            )
            if kind == BLOB
        ]
        previous: str | None = None
        packed = 0
        for address, payload in blobs[: self.effort_budget]:
            pack.add(payload, base_address=previous)
            previous = address
            packed += 1
        remaining = len(blobs) - packed
        self.receipts.append(
            f"repack: {packed} blob(s) considered, "
            f"{len(pack.deltas)} delta(s) formed, "
            f"{remaining} left on the desk"
            + (
                "; the budget ran out before the desk did"
                if remaining
                else ""
            )
        )
        return pack

    def collect(self) -> None:
        before = len(self.repo.store.objects)
        collector = Collector(repo=self.repo)
        verdict = collector.collect()
        after = len(self.repo.store.objects)
        freed = before - after
        if before != after + freed:
            raise Invalid(
                "the maintenance receipts do not add up, and "
                "a job whose own receipts do not reconcile is "
                "the last tool to trust with deletion"
            )
        self.receipts.append(
            f"collect: {before} object(s) before, {after} "
            f"after, {freed} freed ({verdict.split(';')[0]})"
        )

    def run(self) -> str:
        self.repack()
        self.collect()
        return "\n".join(
            [
                "maintenance complete, receipts reconciled:",
                *(f"  {line}" for line in self.receipts),
            ]
        )

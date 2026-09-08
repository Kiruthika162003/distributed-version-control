"""Quarantine: arrivals wait in the airlock until the physical clears them.

Objects from elsewhere are claims until verified, and the
airlock verifies them before they touch the store, because
scrubbing corruption out of a store is surgery while
refusing it at the door is paperwork. Three inspections run
on every batch: each object's bytes are re-digested against
the address they claim, each tree's children must resolve
inside the union of the store and the batch itself, and
each commit's parents must do the same, since a batch is
allowed to depend on itself or on history already held but
never on objects that exist nowhere. The verdict is
wholesale by design: one tampered object rejects the whole
batch, innocents included, because a batch is a statement
of trust from one source and a source that ships one lie
forfeits the benefit of the doubt for the shipment. All
findings are listed before the rejection, one trip, and
admission rebuilds commit records from their own payloads
so the graph learns exactly what the bytes say, nothing
more.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.commits import Commit
from keel.errors import Corrupt
from keel.objects import COMMIT, TREE, digest_bytes
from keel.repo import Repo
from keel.transfer import TransferBatch
from keel.trees import _parse_entries


def _parse_commit_payload(
    payload: bytes,
) -> tuple[str, tuple[str, ...], int, str]:
    text = payload.decode()
    head, _, message = text.partition("message=")
    fields = dict(
        line.split("=", 1)
        for line in head.splitlines()
        if "=" in line
    )
    parents = tuple(
        parent
        for parent in fields.get("parents", "").split(",")
        if parent
    )
    return (
        fields["tree"],
        parents,
        int(fields["seq"]),
        message,
    )


@dataclass
class Airlock:
    target: Repo
    admitted: int = 0
    rejected_batches: int = 0
    journal: list[str] = field(default_factory=list)

    def _findings(
        self, batch: TransferBatch
    ) -> list[str]:
        known = set(self.target.store.objects) | set(
            batch.objects
        )
        findings: list[str] = []
        for address, (kind, payload) in sorted(
            batch.objects.items()
        ):
            if digest_bytes(kind, payload) != address:
                findings.append(
                    f"{address[:8]} ({kind}): bytes do "
                    "not match the claimed address"
                )
                continue
            if kind == TREE:
                for name, _child_kind, child in (
                    _parse_entries(payload)
                ):
                    if child not in known:
                        findings.append(
                            f"tree {address[:8]}: entry "
                            f"{name} points at "
                            f"{child[:8]}, which exists "
                            "nowhere"
                        )
            elif kind == COMMIT:
                tree, parents, _seq, _msg = (
                    _parse_commit_payload(payload)
                )
                if tree not in known:
                    findings.append(
                        f"commit {address[:8]}: tree "
                        f"{tree[:8]} exists nowhere"
                    )
                for parent in parents:
                    if (
                        parent not in known
                        and parent
                        not in self.target.graph.commits
                    ):
                        findings.append(
                            f"commit {address[:8]}: "
                            f"parent {parent[:8]} exists "
                            "nowhere"
                        )
        return findings

    def inspect(self, batch: TransferBatch) -> str:
        findings = self._findings(batch)
        if not findings:
            return (
                f"{len(batch.objects)} object(s) would "
                "clear the airlock"
            )
        return "\n".join(
            [
                f"{len(findings)} finding(s), all "
                "listed before any verdict:"
            ]
            + [f"  {finding}" for finding in findings]
        )

    def admit(self, batch: TransferBatch) -> str:
        findings = self._findings(batch)
        if findings:
            self.rejected_batches += 1
            self.journal.append(
                f"rejected a batch of "
                f"{len(batch.objects)} on "
                f"{len(findings)} finding(s)"
            )
            raise Corrupt(
                "batch rejected wholesale, innocents "
                "included; a source that ships one lie "
                "forfeits the benefit of the doubt for "
                "the shipment:\n"
                + "\n".join(
                    f"  {finding}" for finding in findings
                )
            )
        fresh = 0
        for address, (kind, payload) in (
            batch.objects.items()
        ):
            if not self.target.store.has(address):
                self.target.store.put(kind, payload)
                fresh += 1
            if kind == COMMIT and (
                address not in self.target.graph.commits
            ):
                tree, parents, seq, message = (
                    _parse_commit_payload(payload)
                )
                self.target.graph.commits[address] = (
                    Commit(
                        address=address,
                        tree=tree,
                        parents=parents,
                        message=message,
                        sequence=seq,
                    )
                )
        self.admitted += fresh
        self.journal.append(
            f"admitted {fresh} object(s) after the "
            "physical"
        )
        return (
            f"{fresh} object(s) admitted; the graph "
            "learned exactly what the bytes say"
        )

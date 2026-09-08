"""Notes: annotations that attach to history without touching it.

A commit's address seals its contents forever, which is the
point, and also the problem the day CI wants to record a
build result against it or a reviewer wants to attach a
verdict: writing into the commit would change its address
and orphan every reference. Notes solve it by standing
beside history instead of inside it, a mapping from commit
address to note text kept in its own space, amendable and
even deletable without a single object changing, because the
note is an opinion about the commit and opinions have
different lifecycle rules than facts. Namespaces keep the
opinions from fighting, CI results and review verdicts and
benchmarks each in their own channel, and the render shows a
commit with its notes gathered, labeled by namespace, since
an unlabeled opinion reads as a fact to anyone in a hurry.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.commits import CommitGraph
from keel.errors import Invalid, Missing


@dataclass
class NoteSpace:
    graph: CommitGraph
    spaces: dict[str, dict[str, str]] = field(
        default_factory=dict
    )
    history: list[str] = field(default_factory=list)

    def attach(
        self, namespace: str, address: str, text: str
    ) -> str:
        if not namespace.strip() or "/" in namespace:
            raise Invalid(
                f"{namespace!r} is not a namespace; one word "
                "per channel"
            )
        if not text.strip():
            raise Invalid("an empty note is a nudge, not data")
        self.graph.get(address)
        space = self.spaces.setdefault(namespace, {})
        verb = "amended" if address in space else "attached"
        space[address] = text
        self.history.append(
            f"{namespace}: {verb} on {address[:8]}"
        )
        return (
            f"note {verb} to {address[:8]} in {namespace}; "
            "the commit's address did not move"
        )

    def read(self, namespace: str, address: str) -> str:
        space = self.spaces.get(namespace, {})
        note = space.get(address)
        if note is None:
            raise Missing(
                f"{address[:8]} has no note in {namespace}"
            )
        return note

    def remove(self, namespace: str, address: str) -> str:
        space = self.spaces.get(namespace, {})
        if address not in space:
            raise Missing(
                f"{address[:8]} has no note in {namespace}"
            )
        del space[address]
        self.history.append(
            f"{namespace}: removed from {address[:8]}"
        )
        return (
            "note removed; opinions have different lifecycle "
            "rules than facts"
        )

    def render(self, address: str) -> str:
        commit = self.graph.get(address)
        lines = [f"{address[:8]} {commit.message}"]
        found = 0
        for namespace in sorted(self.spaces):
            note = self.spaces[namespace].get(address)
            if note is not None:
                found += 1
                lines.append(f"  [{namespace}] {note}")
        if not found:
            lines.append("  (no notes; the commit stands alone)")
        return "\n".join(lines)

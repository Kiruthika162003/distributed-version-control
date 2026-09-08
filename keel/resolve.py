"""Conflict resolution: a checklist with teeth, not a feeling of doneness.

A merge that stops on conflicts leaves a precise to-do list,
and the resolver holds it so the human cannot lose it: every
conflicted path must be settled by taking ours, taking
theirs, or supplying a hand-merged text, and the session
refuses to conclude while any path is unsettled, because the
classic disaster is committing a merge with one forgotten
file still wearing its markers. Hand-merged text is screened
for leftover conflict markers on the way in, since markers
that survive into history compile surprisingly often and
break at the worst possible distance from their cause. Every
settlement is journaled with the choice made, so the merge
commit's story includes not just that conflicts existed but
how each one ended, which is the difference between a merge
and an alibi.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Conflict, Invalid, Missing
from keel.merge import MergeOutcome

MARKER_PREFIXES = ("<<<<<<<", "=======", ">>>>>>>", "|||||||")


@dataclass
class ResolutionSession:
    outcome: MergeOutcome
    left_files: dict[str, bytes]
    right_files: dict[str, bytes]
    settled: dict[str, tuple[str, bytes]] = field(
        default_factory=dict
    )
    journal: list[str] = field(default_factory=list)

    def open_paths(self) -> list[str]:
        return sorted(
            path
            for path in self.outcome.conflicts
            if path not in self.settled
        )

    def take_ours(self, path: str) -> str:
        return self._take(path, "ours", self.left_files)

    def take_theirs(self, path: str) -> str:
        return self._take(path, "theirs", self.right_files)

    def _take(
        self,
        path: str,
        side: str,
        source: dict[str, bytes],
    ) -> str:
        if path not in self.outcome.conflicts:
            raise Missing(
                f"{path} is not conflicted; settling it would "
                "be theater"
            )
        if path not in source:
            raise Invalid(
                f"{path} does not exist on the {side} side; "
                "taking a side that deleted it means staging "
                "the deletion, and that is said explicitly "
                "with settle_deletion"
            )
        self.settled[path] = (side, source[path])
        self.journal.append(f"{path}: took {side}")
        return f"{path} settled by taking {side}"

    def settle_deletion(self, path: str) -> str:
        if path not in self.outcome.conflicts:
            raise Missing(f"{path} is not conflicted")
        self.settled[path] = ("deletion", b"")
        self.journal.append(f"{path}: settled as deleted")
        return f"{path} settled as a deletion"

    def settle_by_hand(self, path: str, text: bytes) -> str:
        if path not in self.outcome.conflicts:
            raise Missing(f"{path} is not conflicted")
        for line in text.decode(errors="replace").splitlines():
            if line.startswith(MARKER_PREFIXES):
                raise Invalid(
                    f"{path}: a conflict marker survives in "
                    f"the hand merge ({line[:20]}...); markers "
                    "that reach history compile surprisingly "
                    "often and break far from their cause"
                )
        self.settled[path] = ("hand", text)
        self.journal.append(f"{path}: hand-merged")
        return f"{path} settled by hand"

    def conclude(self) -> dict[str, bytes]:
        remaining = self.open_paths()
        if remaining:
            raise Conflict(
                f"{len(remaining)} path(s) still open "
                f"({', '.join(remaining)}); a checklist with "
                "an unchecked box is not done, whatever it "
                "feels like"
            )
        files = dict(self.outcome.merged_files)
        for path, (choice, content) in self.settled.items():
            if choice == "deletion":
                files.pop(path, None)
            else:
                files[path] = content
        self.outcome.merged_files = files
        self.outcome.conflicts = {}
        return files

    def story(self) -> str:
        if not self.journal:
            return "nothing settled yet"
        return "\n".join(
            [
                f"{len(self.journal)} settlement(s):",
                *(f"  {entry}" for entry in self.journal),
            ]
        )

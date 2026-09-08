"""The stash: a shelf for half-done work, with labels and a strict clerk.

Half-done work interrupted by urgent work needs somewhere to
go that is not a commit, because committing it would either
pollute history or breed a branch-per-interruption museum.
The stash is a labeled stack of working-copy snapshots, and
its clerk enforces the two rules that keep shelves useful:
every entry carries the branch it came from and a label,
because an unlabeled stash aged three weeks is write-only
storage, and popping onto a different branch than the entry
came from is a warning in the receipt rather than a silent
success, since half-done work usually assumes the ground it
was standing on. Apply keeps the entry, pop removes it, and
dropping an entry names what it abandons, so the shelf never
loses anything quietly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid, Missing


@dataclass(frozen=True)
class StashEntry:
    label: str
    branch: str
    files: tuple[tuple[str, bytes], ...]


@dataclass
class Stash:
    entries: list[StashEntry] = field(default_factory=list)

    def push(
        self,
        files: dict[str, bytes],
        branch: str,
        label: str,
    ) -> str:
        if not label.strip():
            raise Invalid(
                "an unlabeled stash aged three weeks is "
                "write-only storage; say what it is"
            )
        if not files:
            raise Invalid(
                "an empty working copy has nothing to shelve"
            )
        self.entries.append(
            StashEntry(
                label=label,
                branch=branch,
                files=tuple(sorted(files.items())),
            )
        )
        return (
            f"shelved {len(files)} file(s) as "
            f"{label!r} from {branch}"
        )

    def _entry(self, index: int) -> StashEntry:
        if not self.entries:
            raise Missing("the shelf is empty")
        if not (0 <= index < len(self.entries)):
            raise Missing(
                f"stash index {index} is off the shelf"
            )
        return self.entries[index]

    def apply(
        self, current_branch: str, index: int = -1
    ) -> tuple[dict[str, bytes], str]:
        position = (
            len(self.entries) - 1 if index == -1 else index
        )
        entry = self._entry(position)
        files = dict(entry.files)
        receipt = (
            f"applied {entry.label!r} "
            f"({len(files)} file(s))"
        )
        if entry.branch != current_branch:
            receipt += (
                f"; WARNING: shelved on {entry.branch}, "
                f"applied on {current_branch}, and half-done "
                "work usually assumes the ground it stood on"
            )
        return files, receipt

    def pop(
        self, current_branch: str
    ) -> tuple[dict[str, bytes], str]:
        files, receipt = self.apply(current_branch)
        self.entries.pop()
        return files, receipt + "; entry removed"

    def drop(self, index: int) -> str:
        entry = self._entry(index)
        self.entries.pop(index)
        return (
            f"dropped {entry.label!r}, abandoning "
            f"{len(entry.files)} file(s); the shelf never "
            "loses anything quietly"
        )

    def listing(self) -> list[str]:
        return [
            f"[{position}] {entry.label!r} from "
            f"{entry.branch} ({len(entry.files)} file(s))"
            for position, entry in enumerate(self.entries)
        ]

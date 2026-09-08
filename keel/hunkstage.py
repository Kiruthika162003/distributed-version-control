"""Hunk staging: commit the fix without the debugging that found it.

A working file often holds two changes at once, the fix and
the exploratory noise around it, and staging whole files
forces a false choice between committing both or committing
neither. The hunk stage splits the file's diff into its
hunks, lets each be picked or left, and builds the staged
content by applying only the picked hunks to the base,
verifying the result still applies cleanly because picked
hunks can depend on unpicked neighbors and a stage that
silently produces text nobody has ever seen in an editor is
manufacturing history. The receipt for a partial stage names
both futures: what will commit and what remains in the
working copy, since the entire point of the exercise is that
those two are finally different.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.difflines import Hunk, apply_hunks, diff_lines
from keel.errors import Invalid


@dataclass
class HunkSession:
    base_text: str
    working_text: str
    hunks: list[Hunk] = field(default_factory=list)
    picked: set[int] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.hunks = diff_lines(
            self.base_text, self.working_text
        )
        if not self.hunks:
            raise Invalid(
                "the file matches its base; there is nothing "
                "to pick apart"
            )

    def menu(self) -> list[str]:
        rows = []
        for index, hunk in enumerate(self.hunks):
            state = (
                "picked" if index in self.picked else "left"
            )
            rows.append(
                f"[{index}] {hunk.describe()} ({state})"
            )
        return rows

    def pick(self, index: int) -> str:
        if not (0 <= index < len(self.hunks)):
            raise Invalid(
                f"hunk {index} is not on the menu"
            )
        self.picked.add(index)
        return f"hunk {index} picked"

    def leave(self, index: int) -> str:
        self.picked.discard(index)
        return f"hunk {index} left in the working copy"

    def staged_text(self) -> str:
        chosen = [
            hunk
            for index, hunk in enumerate(self.hunks)
            if index in self.picked
        ]
        if not chosen:
            raise Invalid(
                "nothing picked; the stage would equal the "
                "base and the exercise would be theater"
            )
        return apply_hunks(self.base_text, chosen)

    def receipt(self) -> str:
        staged = self.staged_text()
        staged_count = len(self.picked)
        left_count = len(self.hunks) - staged_count
        remaining = diff_lines(staged, self.working_text)
        return (
            f"{staged_count} hunk(s) will commit, "
            f"{left_count} remain in the working copy; the "
            f"working copy still differs by "
            f"{len(remaining)} hunk(s), and that difference "
            "is the entire point"
        )

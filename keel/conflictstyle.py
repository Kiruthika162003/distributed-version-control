"""Conflict rendering styles: the same disagreement, dressed for its reader.

A conflict has one truth and several audiences: the developer
resolving in an editor wants the classic markers, the
reviewer skimming a summary wants one line per collision
with sizes, and tooling wants a structured record it can
parse without guessing where markers end. The dresser
recomputes the three-way regions from the three file sets,
because the merge outcome records that paths conflicted, not
how, and dressing needs the how. The styles are guaranteed
to agree on the count, a cheap invariant the dresser checks
itself, since two reports of the same merge disagreeing
about how many conflicts exist is the kind of bug that
outlives every individual conflict in it. The editor style
includes the base region always, resolving without it is
answering a question with the question hidden, and the terse
style names paths, never just counts, because a count
without names is a mood.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.diff3 import conflict_count, merge3, render
from keel.errors import Invalid


@dataclass
class ConflictDresser:
    base_files: dict[str, bytes]
    left_files: dict[str, bytes]
    right_files: dict[str, bytes]
    conflict_paths: tuple[str, ...]

    def _regions(self, path: str):
        base = self.base_files.get(path, b"")
        left = self.left_files.get(path, b"")
        right = self.right_files.get(path, b"")
        return merge3(
            base.decode(errors="replace"),
            left.decode(errors="replace"),
            right.decode(errors="replace"),
        )

    def editor_style(self) -> dict[str, str]:
        return {
            path: render(
                self._regions(path),
                left_name="ours",
                right_name="theirs",
            )
            for path in self.conflict_paths
        }

    def terse_style(self) -> str:
        if not self.conflict_paths:
            return "no conflicts; nothing to dress"
        lines = []
        for path in sorted(self.conflict_paths):
            regions = self._regions(path)
            count = conflict_count(regions)
            widest = max(
                (
                    len(region.left_lines)
                    + len(region.right_lines)
                    for region in regions
                    if region.kind == "conflict"
                ),
                default=0,
            )
            lines.append(
                f"{path}: {count} collision(s), widest "
                f"{widest} line(s)"
            )
        return "\n".join(lines)

    def structured_style(self) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for path in sorted(self.conflict_paths):
            for index, region in enumerate(
                self._regions(path)
            ):
                if region.kind != "conflict":
                    continue
                records.append(
                    {
                        "path": path,
                        "region": index,
                        "base": list(region.base_lines),
                        "ours": list(region.left_lines),
                        "theirs": list(region.right_lines),
                    }
                )
        return records

    def dress_all(self) -> dict[str, object]:
        editor = self.editor_style()
        structured = self.structured_style()
        editor_total = sum(
            page.count("<<<<<<<")
            for page in editor.values()
        )
        if editor_total != len(structured):
            raise Invalid(
                f"the styles disagree, {editor_total} "
                f"against {len(structured)}; two reports of "
                "one merge disagreeing about the count "
                "outlives every conflict in it"
            )
        return {
            "editor": editor,
            "terse": self.terse_style(),
            "structured": structured,
            "agreed_count": len(structured),
        }

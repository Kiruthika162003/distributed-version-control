"""The receipts desk: every organ's journal, filed under one spike.

Half the organs in this workshop keep journals, the freeze
board and the lock office and the mirror and the wheel, and
each journal is honest alone and invisible together, which
is how the day the freeze lifted, the lock was stolen, and
the mirror reclaimed a branch reads as three unrelated
stories. The desk files any journal an organ hands it,
labeled by the organ's name, and renders them in one page
grouped by organ with the loud entries surfaced first
within each group, the capitals having earned their
capitals, STOLEN and OVERRIDE and RECLAIMED being exactly
the lines tomorrow's questions are about. The desk never
writes a journal line of its own, being furniture and not
an organ, and it says how many organs kept no journal, in
the night watch's tradition of naming what was not
checked.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def _is_loud(entry: str) -> bool:
    head, _, _rest = entry.partition(":")
    return head.isupper() and len(head) > 1


@dataclass
class ReceiptsDesk:
    filed: dict[str, list[str]] = field(
        default_factory=dict
    )
    silent_organs: list[str] = field(
        default_factory=list
    )

    def file_journal(
        self, organ: str, journal: list[str]
    ) -> str:
        if not journal:
            self.silent_organs.append(organ)
            return (
                f"{organ} kept no journal today; "
                "filed as silence"
            )
        self.filed[organ] = list(journal)
        return (
            f"{organ}: {len(journal)} entr(ies) filed"
        )

    def page(self) -> str:
        if not self.filed and not self.silent_organs:
            return (
                "the spike is empty; no organ has "
                "reported"
            )
        loud_total = 0
        lines = []
        for organ in sorted(self.filed):
            entries = self.filed[organ]
            loud = [
                entry
                for entry in entries
                if _is_loud(entry)
            ]
            quiet = [
                entry
                for entry in entries
                if not _is_loud(entry)
            ]
            loud_total += len(loud)
            lines.append(
                f"{organ} ({len(entries)} entr(ies)):"
            )
            lines.extend(
                f"  {entry}" for entry in loud
            )
            lines.extend(
                f"  {entry}" for entry in quiet
            )
        header = [
            f"the day's receipts: "
            f"{sum(len(held) for held in self.filed.values())} "
            f"entr(ies) from {len(self.filed)} "
            f"organ(s), {loud_total} in capitals"
        ]
        if loud_total:
            header.append(
                "the capitals earned their capitals; "
                "tomorrow's questions are about "
                "exactly those lines"
            )
        footer = []
        if self.silent_organs:
            footer.append(
                f"{len(self.silent_organs)} organ(s) "
                "kept no journal: "
                + ", ".join(sorted(self.silent_organs))
            )
        return "\n".join(header + lines + footer)

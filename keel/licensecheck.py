"""License headers: one declared text, audited byte for byte where it counts.

License drift is invisible until diligence week, when a
buyer's lawyer finds three headers in one repository and
bills a month of everyone's life, so the auditor holds one
declared header and compares files against it exactly.
Three verdicts cover the ground: present when the header's
lines open the file, absent when they do not appear at
all, and mangled when a recognizable fragment appears with
different words, the worst verdict of the three, because
an absent header is an oversight while a mangled one is a
different license claim someone will have to interpret
under oath. Scope is declared by suffixes, code files
audited, assets and prose left alone, since a license
header in a JSON fixture is noise that trains people to
ignore the audit. The fix list is ordered mangled first
for the lawyer's reason: oversights cost an afternoon,
interpretations cost the month.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.errors import Invalid

VERDICT_PRESENT = "present"
VERDICT_ABSENT = "absent"
VERDICT_MANGLED = "mangled"


@dataclass
class LicenseAuditor:
    header_lines: tuple[str, ...] = ()
    suffixes: tuple[str, ...] = (".py",)
    fingerprint: str = field(default="", init=False)

    def declare(self, header: str) -> str:
        lines = tuple(
            line.strip()
            for line in header.strip().splitlines()
            if line.strip()
        )
        if not lines:
            raise Invalid(
                "an empty header licenses nothing"
            )
        self.header_lines = lines
        anchor = max(lines, key=len).split()
        self.fingerprint = " ".join(anchor[:3])
        return (
            f"header declared, {len(lines)} line(s); "
            "the audit compares exactly"
        )

    def _in_scope(self, path: str) -> bool:
        return path.endswith(self.suffixes)

    def verdict(self, content: bytes) -> str:
        if not self.header_lines:
            raise Invalid(
                "declare the header before auditing; "
                "an audit against nothing approves "
                "everything"
            )
        try:
            text = content.decode()
        except UnicodeDecodeError:
            return VERDICT_ABSENT
        opening = [
            line.strip()
            for line in text.splitlines()[
                : len(self.header_lines) + 2
            ]
            if line.strip()
        ]
        window = opening[: len(self.header_lines)]
        if tuple(window) == self.header_lines:
            return VERDICT_PRESENT
        if self.fingerprint and (
            self.fingerprint in text
        ):
            return VERDICT_MANGLED
        return VERDICT_ABSENT


    def audit(
        self, files: dict[str, bytes]
    ) -> str:
        counted = {
            VERDICT_PRESENT: [],
            VERDICT_ABSENT: [],
            VERDICT_MANGLED: [],
        }
        skipped = 0
        for path in sorted(files):
            if not self._in_scope(path):
                skipped += 1
                continue
            counted[self.verdict(files[path])].append(
                path
            )
        lines = [
            f"{len(counted[VERDICT_PRESENT])} present, "
            f"{len(counted[VERDICT_MANGLED])} mangled, "
            f"{len(counted[VERDICT_ABSENT])} absent, "
            f"{skipped} out of scope"
        ]
        for path in counted[VERDICT_MANGLED]:
            lines.append(
                f"  mangled: {path}; a different "
                "license claim someone interprets "
                "under oath"
            )
        for path in counted[VERDICT_ABSENT]:
            lines.append(
                f"  absent: {path}; an afternoon's "
                "oversight"
            )
        if (
            not counted[VERDICT_MANGLED]
            and not counted[VERDICT_ABSENT]
        ):
            lines.append(
                "diligence week will be boring here, "
                "which is the entire goal"
            )
        return "\n".join(lines)

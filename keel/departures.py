"""Departures: the content gates, cleared before the bytes become history.

Three gauntlets guard three kinds of claim: the gatekeeper
judges the social ones, customs the material ones, and
departures the content itself, secrets that must not board,
paths that will not survive the trip to another filesystem,
and license headers that must read exactly. The one-trip
rule is law here as everywhere, every gate speaking before
any verdict, and the ordering is by blast radius rather
than expense this time, secrets first because a leak is
forever while a collision is a ticket and a header is a
patch. The license gate is advisory at departure, counted
but never holding the shipment alone, in the lint's old
spirit, because a missing header is fixed in the next
commit while a landed secret is rotated across every
system that trusted it, and a gauntlet that cannot tell
those apart teaches people to bypass the whole airport.
"""

from __future__ import annotations

from dataclasses import dataclass

from keel.errors import Conflict
from keel.licensecheck import LicenseAuditor
from keel.portability import audit_paths
from keel.secretscan import scan_files


@dataclass
class Departures:
    license_auditor: LicenseAuditor | None = None

    def clear(
        self, files: dict[str, bytes]
    ) -> str:
        verdicts: list[tuple[str, str, bool]] = []

        secret_findings = scan_files(files)
        if secret_findings:
            verdicts.append(
                (
                    "secrets",
                    f"{len(secret_findings)} "
                    "secret-shaped finding(s); a leak "
                    "is forever",
                    True,
                )
            )
        else:
            verdicts.append(
                (
                    "secrets",
                    "nothing secret-shaped boards",
                    False,
                )
            )

        travel_findings = audit_paths(sorted(files))
        if travel_findings:
            verdicts.append(
                (
                    "portability",
                    f"{len(travel_findings)} path(s) "
                    "will not survive the trip",
                    True,
                )
            )
        else:
            verdicts.append(
                (
                    "portability",
                    "every path travels well",
                    False,
                )
            )

        if self.license_auditor is None:
            verdicts.append(
                (
                    "license",
                    "no header declared; waved "
                    "through",
                    False,
                )
            )
        else:
            page = self.license_auditor.audit(files)
            headline = page.splitlines()[0]
            verdicts.append(
                (
                    "license",
                    headline
                    + "; advisory at departure, a "
                    "header is a patch",
                    False,
                )
            )

        failures = [
            gate
            for gate, _verdict, failed in verdicts
            if failed
        ]
        lines = []
        if failures:
            lines.append(
                f"departure denied: "
                f"{len(failures)} gate(s) hold "
                f"({', '.join(failures)})"
            )
        else:
            lines.append(
                f"cleared for departure: "
                f"{len(files)} file(s)"
            )
        for gate, verdict, failed in verdicts:
            mark = "HOLD" if failed else "ok"
            lines.append(
                f"  {gate}: [{mark}] {verdict}"
            )
        lines.append(
            "ordered by blast radius: a leak is "
            "forever, a collision is a ticket, a "
            "header is a patch"
        )
        page = "\n".join(lines)
        if failures:
            raise Conflict(page)
        return page

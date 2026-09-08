"""Every witness, one call, one page."""

from __future__ import annotations

import importlib

from keel.witnesses.finding import Testimony

WITNESSES = (
    "keel.witnesses.wirebill",
    "keel.witnesses.packbill",
    "keel.witnesses.bisectcount",
    "keel.witnesses.dedupbill",
    "keel.witnesses.renametrust",
    "keel.witnesses.leaseproof",
)


def all_testimonies() -> list[Testimony]:
    found = []
    for dotted in WITNESSES:
        module = importlib.import_module(dotted)
        found.append(module.run())
    return found


def broken() -> list[str]:
    return [
        testimony.witness
        for testimony in all_testimonies()
        if not testimony.holds
    ]


def report() -> str:
    testimonies = all_testimonies()
    lines = [testimony.line() for testimony in testimonies]
    failing = sum(
        1 for testimony in testimonies if not testimony.holds
    )
    lines.append("")
    lines.append(
        f"{len(testimonies)} witnesses, {failing} broken"
    )
    return "\n".join(lines)

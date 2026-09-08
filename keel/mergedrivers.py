"""Merge drivers: diff3 for truth, union for lists, ours and theirs on oath.

Most files deserve diff3 and its honest conflicts, but some
files are lists whose lines do not contest each other, the
changelog, the contributors roll, and the union driver
merges those by keeping every line from both sides in base
order, additions interleaved, because for a list the only
wrong answer is losing somebody's entry. Ours and theirs
exist for the generated file whose regeneration is cheaper
than any merge, and they run on oath: each use is logged
with the path and the side taken, never silent, since a
driver that discards half the work without a receipt is
how generated files eat hand edits. The registry resolves
names from the attributes table and refuses strangers with
the roster, and union refuses binary paths outright,
because a union of bytes that are not lines is a zipper
run over two different jackets.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from keel.attributes import AttributesFile
from keel.diff3 import is_clean, merge3, render
from keel.errors import Invalid

DRIVERS = ("diff3", "union", "ours", "theirs")


def union_merge(
    base: str, ours: str, theirs: str
) -> str:
    base_lines = base.splitlines()
    kept: list[str] = []
    seen_ours = set()
    seen_theirs = set()
    for line in base_lines:
        kept.append(line)
    for line in ours.splitlines():
        if line not in base_lines:
            kept.append(line)
            seen_ours.add(line)
    for line in theirs.splitlines():
        if line not in base_lines and line not in seen_ours:
            kept.append(line)
            seen_theirs.add(line)
    removed = [
        line
        for line in base_lines
        if line not in ours.splitlines()
        and line not in theirs.splitlines()
    ]
    for line in removed:
        kept.remove(line)
    return "\n".join(kept) + ("\n" if kept else "")


@dataclass
class DriverBench:
    attributes: AttributesFile
    oath_log: list[str] = field(default_factory=list)

    def resolve(self, path: str) -> str:
        driver = self.attributes.merge_driver(path)
        if driver not in DRIVERS:
            raise Invalid(
                f"{path} names driver {driver!r}; the "
                f"bench knows {', '.join(DRIVERS)}"
            )
        return driver

    def merge(
        self,
        path: str,
        base: str,
        ours: str,
        theirs: str,
    ) -> tuple[str, str]:
        driver = self.resolve(path)
        if driver == "union":
            if self.attributes.is_binary(path):
                raise Invalid(
                    f"{path} is binary; a union of bytes "
                    "that are not lines is a zipper run "
                    "over two different jackets"
                )
            return (
                union_merge(base, ours, theirs),
                f"{path}: union kept every line",
            )
        if driver in ("ours", "theirs"):
            taken = ours if driver == "ours" else theirs
            receipt = (
                f"{path}: {driver} took one side whole; "
                "logged, never silent"
            )
            self.oath_log.append(receipt)
            return taken, receipt
        regions = merge3(base, ours, theirs)
        if is_clean(regions):
            return (
                render(regions),
                f"{path}: diff3 merged clean",
            )
        return (
            render(regions),
            f"{path}: diff3 left conflicts for a person",
        )
